from functools import wraps
from random import choice
import json


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


def random_color():
    return '#' + ''.join((choice('0123456789ABCDEF') for i in range(6)))


def loadcoords():
    data = json.load(open('./data/route.geojson'))

    return data['features'][0]['geometry']['coordinates']
