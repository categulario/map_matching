#!/usr/bin/env python3
import json
import sys
import os
from lib import task, tasks, init_redis
from lib.graph import Node, INF
from lib.geo import point, line_string, feature_collection, distance
from pprint import pprint
from itertools import starmap
from functools import partial
from heapq import heappush, heappop
import argparse
from math import exp, log

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

    closest_ways = [
        lua('ways_from_gps', 150, layer, *coords) for layer, coords in enumerate(coordinates)
    ]

    parents = dict()

    for layer in range(1, 10):
        print('processing layer {}'.format(layer))
        total_links = len(closest_ways[layer-1])*len(closest_ways[layer])
        count = 0

        best_of_layer = None
        best_of_layer_cost = INF

        for wayt, distt, nearestnodet in closest_ways[layer]: # t for to
            best_way    = None
            best_cost   = INF
            best_path   = None
            best_parent = None

            for wayf, distf, nearestnodef in closest_ways[layer-1]: # f for from
                length, path = lua('a_star', nearestnodef, nearestnodet)

                # difference between path length and great circle distance between the two gps points
                curcost = log(abs(length - distance(*(coordinates[layer-1]+coordinates[layer]))))
                # distance between start of path and first gps point
                curcost += distance(*(coordinates[layer-1] + list(map(float, red.geopos('base:nodehash', nearestnodef)[0]))))
                # distance between end of path and second gps point
                curcost += distance(*(coordinates[layer] + list(map(float, red.geopos('base:nodehash', nearestnodet)[0]))))

                cur_parent = parents.get(Node.hash(layer-1, wayf))
                if cur_parent: curcost += cur_parent.cost

                if curcost < best_cost:
                    best_cost   = curcost
                    best_way    = wayt
                    best_path   = path
                    best_parent = cur_parent

                count += 1
                print('processed {} of {} links for this layer'.format(count, total_links), end='\r', flush=True)

            newnode = Node(
                layer  = layer,
                way    = wayt,
                cost   = best_cost,
                path   = best_path,
                parent = best_parent,
            )

            parents[Node.hash(layer, wayt)] = newnode

            if newnode.cost < best_of_layer_cost:
                best_of_layer = newnode
                best_of_layer_cost = newnode.cost

        print()

    curnode = best_of_layer
    lines = []

    while curnode != None:
        lines.append(line_string(list(map(float, pos)) for pos in curnode.path))

        curnode = curnode.parent

    json.dump(feature_collection(lines + [line_string(coordinates, {
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
