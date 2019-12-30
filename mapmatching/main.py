import argparse


class DownloadTask:

    def add_arguments(self, subparsers):
        download_parser = subparsers.add_parser('download', help='Downloads street data from OpenStreetMaps')
        download_parser.add_argument(
            'x1', metavar='X1', type=float,
            help='X coordinate for the lower left corner of the bounding box')
        download_parser.add_argument(
            'y1', metavar='Y1', type=float,
            help='Y coordinate for the lower left corner of the bounding box')
        download_parser.add_argument(
            'x2', metavar='X2', type=float,
            help='X coordinate for the upper right corner of the bounding box')
        download_parser.add_argument(
            'y2', metavar='Y2', type=float,
            help='Y coordinate for the upper right corner of the bounding box')
        download_parser.add_argument('--output', '-o', type=argparse.FileType('w'), help='Write data to this file')
        download_parser.set_defaults(func=self)

    def __call__(self, args):
        import requests

        # http://wiki.openstreetmap.org/wiki/Map_Features#Special_road_types
        query = '''[out:json][timeout:25];

// gather results
(
  way["highway"][highway!~"service,footway,steps,pedestrian,escape,raceway,bridleway,cycleway"]({y1},{x1},{y2},{x2});
);

// print results
out body;
>;
out skel qt;'''.format(
            x1=args.x1,
            y1=args.y1,
            x2=args.x2,
            y2=args.y2,
        )

        res = requests.post('http://overpass-api.de/api/interpreter', data=query)

        if res.status_code != 200:
            if args.verbosity > 1:
                print('Status code:', res.status_code)

            if args.verbosity > 2:
                print(res.text)

            exit('Query failed')

        if args.output is not None:
            args.output.write(res.text)
        else:
            print(res.text)


def main():
    parser = argparse.ArgumentParser(
        description='Match a gps track to streets',
    )

    # General arguments
    parser.add_argument('--verbose', '-v', action='count', default=0, help='verbosity', dest='verbosity')

    # Subparsers
    subparsers = parser.add_subparsers(help='Sub commands')

    d = DownloadTask()
    d.add_arguments(subparsers)

    # Parse arguments and execute
    args = parser.parse_args()
    args.func(args)
