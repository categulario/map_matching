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
from heapq import heappush, heappop
import argparse

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

    print()

    return 'done'

@task
def mapmatch():
    data = json.load(open('./data/route.geojson'))

    coordinates = data['features'][0]['geometry']['coordinates']
    heap = []

    # First set of edges from layer 0 to layer 1
    for way1, dist1, nearestnode1 in lua('ways_from_gps', 150, 0, *coordinates[0]):
        for way2, dist2, nearestnode2 in lua('ways_from_gps', 150, 1, *coordinates[1]):
            weigth, path = lua('a_star', nearestnode1, nearestnode2)

            newedge = Edge(
                weigth         = weigth,
                to_layer       = 1,
                to_nearestnode = nearestnode2,
                path           = path,
                parent         = None,
            )

            heappush(heap, newedge)

    while len(heap) > 0:
        edge = heappop(heap)
        print(edge)

        if edge.to_layer == len(coordinates)-1 :
            break

        next_layer = edge.to_layer+1

        # add edges to next layer from this edge's last node
        for way, dist, nearestnode in lua('ways_from_gps', 150, next_layer, *coordinates[next_layer]):
            weigth, path = lua('a_star', edge.to_nearestnode, nearestnode)

            newedge = Edge(
                weigth         = edge.weigth + weigth,
                to_layer       = next_layer,
                to_nearestnode = nearestnode,
                path           = path,
                parent         = edge,
            )

            heappush(heap, newedge)

    curedge = edge
    path = []

    while curedge != None:
        path = curedge.path + path

        curedge = curedge.parent

    json.dump(feature_collection([
        line_string(list(map(float, pos)) for pos in path)
    ] + [line_string(coordinates, {
        'stroke': '#000000',
        'stroke-width': 4,
        'stroke-opacity': .5,
    })]), open('./build/result.geojson', 'w'))

@task
def a_star(fromnode, tonode):
    loadlua()

    route = lua('a_star', fromnode, tonode)

    if route == 0:
        return 'Route not found'

    json.dump(feature_collection([
            line_string(list(map(float, coords)) for coords in lua('a_star', fromnode, tonode))
    ]), open('./build/a_star.geojson', 'w'))

    return route

@task
def loadlua():
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
def lslua():
    return '\n'.join(map(
        lambda s: '{}: {}'.format(s[0].decode('utf8').split(':')[2], s[1].decode('utf8')),
        lua('list_scripts')
    ))

@task
def lua(scriptname, *args):
    sha = red.get('base:script:{}'.format(scriptname))

    if sha is None:
        sys.stderr.write('Unknown script {}\n'.format(scriptname))
        exit(3)

    return red.evalsha(sha, 0, *args)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compute the map matching route')

    parser.add_argument('task', help='the task to execute', choices=tasks)
    parser.add_argument('args', nargs='*', help='arguments for the task')
    parser.add_argument('-s', '--silent', action='store_true')

    args = parser.parse_args()

    val = locals()[args.task](*args.args)

    if args.silent:
        exit()

    if type(val) is str:
        print(val)
    elif val is not None:
        pprint(val)
