from redis import Redis

from mapmatching.task import TaskContext


def test_task_context():
    tc = TaskContext()

    @tc.task
    def foo(redis):
        assert type(redis) == Redis

    @tc.task
    def var(a, redis):
        assert a == 'a'
        assert type(redis) == Redis

    @tc.task
    def log(a, redis, b):
        assert a == 'a'
        assert type(redis) == Redis
        assert b == 'b'

    foo()
    var('a')
    log('a', 'b')
