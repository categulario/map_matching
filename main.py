#!/usr/bin/env python3
import json
import sys

def init_redis():
    import redis

    return redis.StrictRedis(
        host='localhost',
        port=6379,
        db=1
    )

def load_task():
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

def compute_task():
    print('compute')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.stderr.write('Missing task argument\n')
        exit(1)

    task = sys.argv[1]

    if task not in ['load', 'compute']:
        sys.stderr.write('Unknown task {}\n'.format(task))
        exit(2)

    locals()[task + '_task']()
