#!/usr/bin/env python3
import json
import sys

def load_task():
    """loads the graph data obtained from OSM overpass api"""
    data = json.load(open('./overpass/street_graph.json'))

    types = dict()

    for element in data['elements']:
        etype = element['type']

        if etype in types:
            types[etype] += 1
        else:
            types[etype] = 1

    print(types)

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
