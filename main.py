#!/usr/bin/env python3
import json
import sys
import os
from lib import *
from lib.graph import Node, INF
from lib.geo import *
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

    return 'done'

@task
def triangles():
    coords = loadcoords()

    features = []

    newlinecoords = []

    for n1, n2, n3 in zip(coords[0:-2], coords[1: -1], coords[2:]):
        # features.append(polygon([n1, n2, n3, n1]))
        mid = [
            (n1[0]+n2[0])/2,
            (n1[1]+n2[1])/2,
        ]

        prop = 2/3

        newlinecoords.append([
            n3[0] + (mid[0] - n3[0])*prop,
            n3[1] + (mid[1] - n3[1])*prop,
        ])

    features.append(line_string([coords[0]] + newlinecoords + [coords[-1]]))
    features.append(line_string(coords))

    json.dump(feature_collection(features), open('./build/triangles.geojson', 'w'))

@task
def mapmatch():
    coordinates = loadcoords()

    closest_ways = [
        lua('ways_from_gps', 150, layer, *coords) for layer, coords in enumerate(coordinates)
    ]

    parents = dict()

    for layer in range(1, 6):
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
                cur_parent = parents.get(Node.hash(layer-1, wayf))

                try:
                    length, path = lua('a_star', nearestnodef, nearestnodet, cur_parent.skip_node if cur_parent is not None else None)
                except TypeError as e:
                    continue

                # difference between path length and great circle distance between the two gps points
                curcost = log(abs(length - distance(*(coordinates[layer-1]+coordinates[layer]))))
                # distance between start of path and first gps point
                curcost += distance(*(coordinates[layer-1] + list(map(float, red.geopos('base:nodehash', nearestnodef)[0]))))
                # distance between end of path and second gps point
                curcost += distance(*(coordinates[layer] + list(map(float, red.geopos('base:nodehash', nearestnodet)[0]))))

                if cur_parent: curcost += cur_parent.cost

                if curcost < best_cost:
                    best_cost   = curcost
                    best_way    = wayt
                    best_path   = path
                    best_parent = cur_parent

                count += 1
                print('processed {} of {} links for this layer'.format(count, total_links), end='\r', flush=True)

            if len(best_path) >= 2:
                skip_node = best_path[-2][2]
            elif len(best_path) == 1:
                skip_node = best_parent.path[-1] if best_parent else None

            newnode = Node(
                layer     = layer,
                way       = wayt,
                cost      = best_cost,
                path      = best_path,
                parent    = best_parent,
                skip_node = skip_node,
            )

            parents[Node.hash(layer, wayt)] = newnode

            if newnode.cost < best_of_layer_cost:
                best_of_layer = newnode
                best_of_layer_cost = newnode.cost

        print()

    curnode = best_of_layer
    lines = []

    while curnode != None:
        if len(curnode.path) == 1:
            lines.append(point(map(float, curnode.path[0])))
        else:
            lines.append(line_string(
                (list(map(float, pos)) for pos in curnode.path),
                {
                    'layer': curnode.layer,
                    'way': curnode.way.decode('utf8'),
                }
            ))

        curnode = curnode.parent

    json.dump(feature_collection(lines + [line_string(coordinates, {
        'stroke': '#000000',
        'stroke-width': 4,
        'stroke-opacity': .5,
    })]), open('./build/result.geojson', 'w'))

@task
def a_star(fromnode, tonode, skip_node=None):
    loadlua()

    route = lua('a_star', fromnode, tonode, skip_node)

    if route == 0:
        return 'Route not found'

    json.dump(feature_collection([
            line_string(list(map(float, coords)) for coords in route[1])
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

@task
def osrmresponse(responsefile):
    def to_coordinate(tracepoint):
        return tracepoint['location']

    data = json.load(open(responsefile))

    json.dump(feature_collection([
        line_string(map(to_coordinate, data['tracepoints'])),
    ]), sys.stdout)

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
