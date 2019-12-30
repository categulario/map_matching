from redis import Redis
from functools import wraps


class TaskContext:

    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=1):
        self.redis = None
        self.task_names = []

        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db

    def get_redis(self):
        if self.redis is None:
            self.redis = Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
            )

        return self.redis

    def task(self, f):
        self.task_names.append(f.__name__)

        # Inject redis parameter if present
        redis_param_index = f.__code__.co_varnames.index('redis')

        @wraps(f)
        def wrapper(*args, **kwds):
            new_args = args[:redis_param_index] + \
                (self.get_redis(),) + \
                args[redis_param_index:]

            return f(*new_args, **kwds)

        return wrapper
