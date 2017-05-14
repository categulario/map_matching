#!/usr/bin/env python3
import json
import sys
import os
from lib import task, tasks, init_redis
from pprint import pprint

@task
def loaddata():
    """loads the graph data obtained from OSM overpass api"""
    data = json.load(open('./overpass/street_graph.json'))

    red = init_redis()

    for element in data['elements']:
        etype = element['type']
        eid   = element['id']

        if etype == 'node':
            # load to GEOHASH with ID
            red.geoadd('mapmatch:nodehash', element['lon'], element['lat'], eid)
            # add to node count
            red.pfadd('mapmatch:node:count', eid)

        elif etype == 'way':
            # add nodes to way
            red.rpush('mapmatch:way:{}:nodes'.format(eid), *element['nodes'])
            # add to way count
            red.pfadd('mapmatch:way:count', eid)

            # add this way to node relations
            for node in element['nodes']:
                red.rpush('mapmatch:node:{}:ways'.format(node), eid)

            # add this way's tags
            for tag, value in element['tags'].items():
                red.set('mapmatch:way:{}:{}'.format(eid, tag), value)

@task
def compute():
    data = json.load(open('./data/route.geojson'))
    red = init_redis()

    for pos in data['features'][0]['geometry']['coordinates']:
        print(pos)

        nodes = red.georadius('mapmatch:nodehash', pos[0], pos[1], 15, unit='m')

        for node in nodes:
            ways = red.lrange('mapmatch:node:{}:ways'.format(node), 0, -1)

            print(ways)

        exit()

@task
def loadscripts():
    red = init_redis()
    red.script_flush()

    with open('./lua/del_redis_keys.lua') as delscript:
        red.eval(delscript.read(), 0, 'mapmatch:script:*')

    scriptlist = filter(
        lambda s: s.endswith('.lua'),
        os.listdir('lua')
    )

    scripts = dict()

    for script in scriptlist:
        name = script.split('.')[0]

        with open(os.path.join('lua', script)) as scriptfile:
            scripts[name] = red.script_load(scriptfile.read())
            red.set('mapmatch:script:{}'.format(name), scripts[name])

    pprint(scripts)

@task
def listscripts():
    red = init_redis()

    scripts = map(
        lambda s: s.decode('utf8').split(':')[2],
        red.keys('mapmatch:script:*')
    )

    for key in scripts:
        print(key)

@task
def runscript(scriptname):
    pass

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.stderr.write('Missing task argument\n')
        exit(1)

    task = sys.argv[1]

    if task not in tasks:
        sys.stderr.write('Unknown task {}\n'.format(task))
        exit(2)

    args = sys.argv[2:]

    locals()[task](*args)
