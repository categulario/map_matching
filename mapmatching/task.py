from redis import Redis
from functools import wraps
import argparse


class TaskContext:

    def __init__(self):
        self.redis = None

        self.parser = argparse.ArgumentParser(
            description='Match a gps track to streets',
        )
        self.parser.set_defaults(func=None)

        # General arguments
        self.parser.add_argument('--verbosity', '-v', default='warning',
                                 choices=('critical', 'error', 'warning',
                                          'info', 'debug'),
                                 help='verbosity')
        self.parser.add_argument('--redis-host', default='localhost',
                                 help='Redis host')
        self.parser.add_argument('--redis-port', type=int, default=6379,
                                 help='Redis port')
        self.parser.add_argument('--redis-db', type=int, default=1,
                                 help='Redis database number')

        # Subparsers
        self.subparsers = self.parser.add_subparsers(help='Sub commands')

    def get_redis(self, args):
        if self.redis is None:
            self.redis = Redis(
                host=args.redis_host,
                port=args.redis_port,
                db=args.redis_db,
            )

        return self.redis

    def task(self, class_def):
        # Inject redis parameter if present
        obj = class_def()

        try:
            redis_param_index = obj.execute.__code__.co_varnames.index('redis')
        except ValueError:
            redis_param_index = None

        @wraps(obj.execute)
        def wrapper(*args, **kwds):
            if redis_param_index is None:
                new_args = args
            else:
                new_args = args[:redis_param_index - 1] + \
                    (self.get_redis(args[0]),) + \
                    args[redis_param_index - 1:]

            return obj.execute(*new_args, **kwds)

        subparser = self.subparsers.add_parser(
            class_def.__name__[:-4].lower(),
            help=class_def.__doc__,
        )

        if hasattr(obj, 'add_arguments'):
            obj.add_arguments(subparser)

        subparser.set_defaults(func=wrapper)

        return class_def

    def parse_args(self, *args, **kwargs):
        return self.parser.parse_args(*args, **kwargs)

    def print_usage(self):
        return self.parser.print_usage()
