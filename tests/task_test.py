from redis import Redis

from mapmatching.task import TaskContext


def test_task_context():
    tc = TaskContext()

    @tc.task
    class FooTask:
        'foo help'

        def execute(self, redis, args):
            assert type(redis) == Redis

    @tc.task
    class VarTask:
        'var help'

        def add_arguments(self, parser):
            parser.add_argument('a')

        def execute(self, args, redis):
            assert args.a == 'a'
            assert type(redis) == Redis

    args = tc.parse_args(['foo'])
    args.func(args)

    args = tc.parse_args(['var', 'a'])
    args.func(args)
