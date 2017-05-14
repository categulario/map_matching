from functools import wraps

def init_redis():
    import redis

    return redis.StrictRedis(
        host='localhost',
        port=6379,
        db=1
    )

tasks = []

def task(f):
    tasks.append(f.__name__)

    @wraps(f)
    def wrapper(*args, **kwds):
        return f(*args, **kwds)

    return wrapper
