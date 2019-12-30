#!/usr/bin/env python3
from itertools import starmap
from math import log
from pprint import pprint
import argparse
import json
import os
import sys

from lib import init_redis, task, loadcoords, tasks
from lib.geo import line_string, feature_collection, point, d
from lib.graph import Node, INF

red = init_redis()

RADIUS = 150  # changes after parse_args


@task
def loaddata():
    """loads the graph data obtained from OSM overpass api"""
    data = json.load(open('./overpass/street_graph.json'))
    total = len(data['elements'])

    for i, element in enumerate(data['elements']):
        etype = element['type']
        eid = element['id']

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

    return 'done!                '


@task
def triangles(filename):
    coords = loadcoords(filename)

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

    json.dump(
        feature_collection(features),
        open('./build/triangles.geojson', 'w')
    )


@task
def ways_from_gps(longitude, latitude):
    def get_coordinates(way):
        return [
            list(map(float, coords))
            for coords in lua('nodes_from_way', way)
        ]

    def ans_to_json(way, nearestnode):
        return line_string(get_coordinates(way))

    json.dump(feature_collection(
        list(starmap(
            ans_to_json,
            lua('ways_from_gps', RADIUS, longitude, latitude)
        )) + [point([float(longitude), float(latitude)])]
    ), open('./build/ways_from_gps.geojson', 'w'), indent=2)


@task
def mapmatch(filename, layers):
    coordinates = loadcoords(filename)

    closest_ways = [
        lua('ways_from_gps', RADIUS, *coords) for coords in coordinates
    ]

    parents = dict()

    for layer in range(1, min(int(layers), len(coordinates))):
        print('processing layer {}'.format(layer))
        total_links = len(closest_ways[layer-1])*len(closest_ways[layer])
        count = 0

        best_of_layer = None
        best_of_layer_cost = INF

        for wayt, nearestnodet in closest_ways[layer]:  # t for to
            best_cost = INF
            best_parent = None
            best_path = None

            for wayf, nearestnodef in closest_ways[layer-1]:  # f for from
                parent = parents.get(Node.hash(layer-1, wayf))

                if layer > 1 and parent is None:
                    # these nodes are not useful as their parents couldn't be
                    # routed
                    continue

                try:
                    length, path = lua(
                        'a_star',
                        nearestnodef,
                        nearestnodet,
                        parent.skip_node if parent is not None else None
                    )
                except TypeError:
                    continue  # no route from start to end

                # difference between path length and great circle distance
                # between the two gps points
                curcost = log(abs(
                    length - d(*(coordinates[layer-1]+coordinates[layer]))
                ))
                # distance between start of path and first gps point
                curcost += d(*(coordinates[layer-1] + list(map(
                    float, red.geopos('base:nodehash', nearestnodef)[0]
                ))))
                # distance between end of path and second gps point
                curcost += d(*(coordinates[layer] + list(map(
                    float, red.geopos('base:nodehash', nearestnodet)[0]
                ))))

                if parent:
                    curcost += parent.cost

                if curcost < best_cost:
                    best_cost = curcost
                    best_parent = parent
                    best_path = path

                count += 1
                print('processed {} of {} links for this layer'.format(
                    count, total_links), end='\r', flush=True
                )

            try:
                if len(best_path) >= 2:
                    skip_node = best_path[-2][2]
                elif len(best_path) == 1:
                    skip_node = best_parent.skip_node if best_parent else None
            except TypeError:
                continue  # No feasible route to get here

            newnode = Node(
                layer=layer,
                way=wayt,
                cost=best_cost,
                path=best_path,
                parent=best_parent,
                skip_node=skip_node,
            )

            parents[Node.hash(layer, wayt)] = newnode

            if newnode.cost < best_of_layer_cost:
                best_of_layer = newnode
                best_of_layer_cost = newnode.cost

        print()

    curnode = best_of_layer
    lines = []

    while curnode is not None:
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
        lambda s: '{}: {}'.format(
            s[0].decode('utf8').split(':')[2], s[1].decode('utf8')
        ),
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


@task
def project(lon, lat):
    def to_feature(distance, lon, lat):
        return point([float(lon), float(lat)], {
            'dist': distance,
        })

    json.dump(feature_collection([
        point([float(lon), float(lat)], {
            'marker-color': '#3ba048',
        }),
    ] + list(starmap(
        to_feature,
        lua('project_point', 150, lon, lat)
    ))), open('./build/projection.json', 'w'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Compute the map matching route'
    )

    parser.add_argument('task', help='the task to execute', choices=tasks)
    parser.add_argument('args', nargs='*', help='arguments for the task')
    parser.add_argument('-s', '--silent', action='store_true')
    parser.add_argument('-r', '--radius', type=int,
                        help='The radius for various searches', default=150)

    args = parser.parse_args()

    RADIUS = args.radius

    val = locals()[args.task](*args.args)

    if args.silent:
        exit()

    if type(val) is str:
        print(val)
    elif val is not None:
        pprint(val)
