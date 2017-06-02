#!/usr/bin/env python3
import json
import sys
import os
from lib import task, tasks, init_redis
from lib.graph import Edge
from lib.geo import point, line_string, feature_collection, distance
from pprint import pprint
from itertools import starmap
from functools import partial
from hashids import Hashids
from heapq import heappush, heappop

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

    # Using dijskra to find the best route match
    heap = [Edge()]
    path = None

    while len(heap) > 0:
        edge = heappop(heap)

        # add to the heap the nodes reachable from current node
        for way, dist, nearestnode in runscript('ways_from_gps', 150, edge.layer, *coordinates[edge.layer]):
            weigth = float(dist) + edge.weigth

            if edge.from_street:
                gpsdist = distance(*(coordinates[edge.layer-1] + coordinates[edge.layer]))
                weigth += abs(gpsdist - runscript('a_star', edge.nearestnode, nearestnode))

            newedge = Edge(
                weigth      = weigth,
                layer       = edge.layer+1,
                from_street = edge.to_street,
                to_street   = way.decode('utf8'),
                nearestnode = nearestnode,
                parent      = edge,
            )

            heappush(heap, newedge)

        # last GPS position visited, route finished
        if edge.layer == len(coordinates)-1:
            break

    curedge = edge
    streets = set()

    while curedge != None:
        if curedge.from_street: streets.add(curedge.from_street)
        if curedge.to_street: streets.add(curedge.to_street)

        curedge = curedge.parent

    json.dump(feature_collection([
        line_string(list(map(lambda x: float(x), nodepos)) for nodepos in runscript('nodes_from_way', street)) for street in streets
    ] + [line_string(coordinates, {
        'stroke': '#000000',
        'stroke-width': 4,
        'stroke-opacity': .5,
    })]), open('./build/result.geojson', 'w'))

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
