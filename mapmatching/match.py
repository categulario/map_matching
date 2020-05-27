import math
import logging

from mapmatching.geo import d
from mapmatching.geojson import point, line_string, feature_collection

LOGGER = logging.getLogger(__name__)


class Node:

    def __init__(self, layer=None, way=None, cost=math.inf, path=None,
                 parent=None, skip_node=None):
        self.cost = cost
        self.path = path
        self.parent = parent
        self.layer = layer
        self.way = way
        self.skip_node = skip_node

    def __hash__(self):
        return Node.hash(self.layer, self.way)

    def __str__(self):
        return '<Node:{} {}>'.format(
            self.layer, self.cost
        )

    @staticmethod
    def hash(layer, way):
        return hash('{}-{}'.format(layer, way))


def match(redis, lua, coordinates, max_layer, radius):
    closest_ways = [
        lua.ways_from_gps(args=[radius]+coords) for coords in coordinates
    ]

    parents = dict()

    for layer in range(1, min(max_layer, len(coordinates))):
        LOGGER.info('processing layer {}'.format(layer))
        total_links = len(closest_ways[layer-1])*len(closest_ways[layer])
        count = 0

        best_of_layer = None
        best_of_layer_cost = math.inf

        for wayt, nearestnodet in closest_ways[layer]:  # t for to
            best_cost = math.inf
            best_parent = None
            best_path = None

            for wayf, nearestnodef in closest_ways[layer-1]:  # f for from
                parent = parents.get(Node.hash(layer-1, wayf))

                if layer > 1 and parent is None:
                    # these nodes are not useful as their parents couldn't be
                    # routed
                    continue

                try:
                    length, path = lua.a_star(args=[
                        nearestnodef,
                        nearestnodet,
                        parent.skip_node
                        if (parent is not None) and
                           (parent.skip_node is not None)
                        else 'None',
                    ])
                except TypeError:
                    continue  # no route from start to end

                # difference between path length and great circle distance
                # between the two gps points
                curcost = math.log(abs(
                    length - d(*(coordinates[layer-1]+coordinates[layer]))
                ))
                # distance between start of path and first gps point
                curcost += d(*(coordinates[layer-1] + list(map(
                    float, redis.geopos('base:nodehash', nearestnodef)[0]
                ))))
                # distance between end of path and second gps point
                curcost += d(*(coordinates[layer] + list(map(
                    float, redis.geopos('base:nodehash', nearestnodet)[0]
                ))))

                if parent:
                    curcost += parent.cost

                if curcost < best_cost:
                    best_cost = curcost
                    best_parent = parent
                    best_path = path

                count += 1
                LOGGER.info('processed {} of {} links for layer {}'.format(
                    count, total_links, layer,
                ))

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

    return feature_collection(lines + [line_string(coordinates, {
        'stroke': '#000000',
        'stroke-width': 4,
        'stroke-opacity': .5,
    })])
