import argparse
import sys
import logging
import json

from mapmatching.task import TaskContext
from mapmatching.data import download_from_overpass, load_to_redis

LOGGER = logging.getLogger(__name__)
LOGGING_LEVELS = {
    name: getattr(logging, name.upper())
    for name in ('critical', 'error', 'warning', 'info', 'debug')
}
tc = TaskContext()


@tc.task
class DownloadTask:
    'Downloads street data from OpenStreetMaps'

    def add_arguments(self, parser):
        parser.add_argument(
            'x1', metavar='X1', type=float,
            help='X coordinate for the lower left corner of the bounding box')
        parser.add_argument(
            'y1', metavar='Y1', type=float,
            help='Y coordinate for the lower left corner of the bounding box')
        parser.add_argument(
            'x2', metavar='X2', type=float,
            help='X coordinate for the upper right corner of the bounding box')
        parser.add_argument(
            'y2', metavar='Y2', type=float,
            help='Y coordinate for the upper right corner of the bounding box')
        parser.add_argument('--output', '-o', type=argparse.FileType('w'),
                            default=sys.stdout,
                            help='Write data to this file')

    def execute(self, args):
        data = download_from_overpass(args.x1, args.y1, args.x2, args.y2)

        args.output.write(json.dumps(data))


@tc.task
class LoadTask:
    'Loads downloaded data into redis'

    def add_arguments(self, parser):
        parser.add_argument(
            '-f', '--file', metavar='FILE', type=argparse.FileType('r'),
            default=sys.stdin,
            help='File to read data from, defaults to stdin')

    def execute(self, redis, args):
        data = json.load(args.file)

        load_to_redis(data, redis)


@tc.task
class MatchTask:
    'Matches a GPS track to streets'

    def add_arguments(self, parser):
        parser.add_argument(
            'filename', metavar='FILE', type=argparse.FileType('r'),
            help='Where to read the GPS points from',
        )
        parser.add_argument(
            '-l', '--layers', metavar='NUM', type=int, default=sys.maxsize,
            help='match only the frist NUM points of the GPS track',
        )
        parser.add_argument(
            '-r', '--radius', metavar='NUM', type=int, default=150,
            help='radius in meters to use around gps points to find streets',
        )
        parser.add_argument(
            '--output', '-o', type=argparse.FileType('w'),
            default=sys.stdout,
            help='Write data to this file',
        )

    def execute(self, redis, args):
        from mapmatching.match import match
        from mapmatching.lua import LuaManager
        import json

        data = json.load(args.filename)
        coordinates = data['features'][0]['geometry']['coordinates']

        json_output = match(
            redis,
            LuaManager(redis),
            coordinates,
            args.layers,
            args.radius,
        )

        json.dump(json_output, args.output, indent=2)


def main():
    # Parse arguments and execute
    args = tc.parse_args()

    logging.basicConfig(
        format='%(levelname)s:%(message)s',
        level=LOGGING_LEVELS[args.verbosity],
    )

    if args.func is None:
        tc.print_usage()
    else:
        args.func(args)
