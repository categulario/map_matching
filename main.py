#!/usr/bin/env python3
import json
import sys
import os
from lib import task, tasks, init_redis
from lib.geo import distance, point, line_string, feature_collection
from pprint import pprint
from itertools import starmap
from functools import partial
from hashids import Hashids

red = init_redis()

@task
def loaddata():
    """loads the graph data obtained from OSM overpass api"""
    data = json.load(open('./overpass/street_graph.json'))
    total = len(data['elements'])

    for i, element in enumerate(data['elements']):
        etype = element['type']
        eid   = element['id']

        if etype == 'node':
            # load to GEOHASH with ID
            red.geoadd('base:nodehash', element['lon'], element['lat'], eid)
            # add to node count
            red.pfadd('base:node:count', eid)

        elif etype == 'way':
            # add nodes to way
            red.rpush('base:way:{}:nodes'.format(eid), *element['nodes'])
            # add to way count
            red.pfadd('base:way:count', eid)

            # add this way to node relations
            for node in element['nodes']:
                red.rpush('base:node:{}:ways'.format(node), eid)

            # add this way's tags
            for tag, value in element['tags'].items():
                red.set('base:way:{}:{}'.format(eid, tag), value)

        print('loaded {}/{}'.format(i+1, total), end='\r', flush=True)

    return 'done'

@task
def compute():
    data = json.load(open('./data/route.geojson'))

    coordinates = data['features'][0]['geometry']['coordinates']
    hashes = Hashids(salt='a salt', min_length=6, alphabet='0123456789ABCDEF')

    # compute set of near streets for each GPS position z_i
    for i, pos in enumerate(coordinates):
        json.dump(feature_collection([
                point(pos, {'marker-color': '#BE2929'}),
            ] + list(map(
                partial(line_string, properties={
                    'stroke': '#'+hashes.encode(i),
                }),
                map(
                    lambda way: list(map(
                        lambda node: [float(node[1][0]), float(node[1][1])],
                        way
                    )),
                    runscript('ways_from_node', pos[0], pos[1], 150, i)
                )
            )),
        ), open('./build/node_{:03d}_streets.geojson'.format(i), 'w'))
        print('node streets: {}'.format(i), end='\r', flush=True)

    print()

    for i,j in zip(range(len(coordinates)-1), range(1, len(coordinates))):
        json.dump(feature_collection([
                point(coordinates[i], {'marker-color': '#BE2929'}),
                point(coordinates[j], {'marker-color': '#BE2929'}),
            ] + list(map(
                partial(line_string, properties={
                    'stroke': '#'+hashes.encode(i + j),
                }),
                map(
                    lambda way: list(map(
                        lambda node: [float(node[1][0]), float(node[1][1])],
                        way
                    )),
                    runscript('ways_from_transition', i, j)
                )
            )),
        ), open('./build/transition_{:03d}_streets.geojson'.format(i, j), 'w'))
        print('transition streets: {}'.format(i), end='\r', flush=True)

    print()

@task
def loadscripts():
    red.script_flush()

    with open('./lua/del_redis_keys.lua') as delscript:
        red.eval(delscript.read(), 0, 'base:script:*')

    scriptlist = filter(
        lambda s: s.endswith('.lua'),
        os.listdir('lua')
    )

    scripts = dict()

    for script in scriptlist:
        name = script.split('.')[0]

        with open(os.path.join('lua', script)) as scriptfile:
            scripts[name] = red.script_load(scriptfile.read())
            red.set('base:script:{}'.format(name), scripts[name])

    return '\n'.join(starmap(
        lambda s, h: '{}: {}'.format(s, h),
        scripts.items()
    ))

@task
def listscripts():
    return '\n'.join(map(
        lambda s: '{}: {}'.format(s[0].decode('utf8').split(':')[2], s[1].decode('utf8')),
        runscript('list_scripts')
    ))

@task
def runscript(scriptname, *args):
    sha = red.get('base:script:{}'.format(scriptname))

    if sha is None:
        sys.stderr.write('Unknown script {}\n'.format(scriptname))
        exit(3)

    return red.evalsha(sha, 0, *args)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.stderr.write('Missing task argument\n')
        exit(1)

    task = sys.argv[1]

    if task not in tasks:
        sys.stderr.write('Unknown task {}\n'.format(task))
        exit(2)

    args = sys.argv[2:]

    val = locals()[task](*args)

    if type(val) is str:
        print(val)
    elif val is not None:
        pprint(val)
