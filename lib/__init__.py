from functools import wraps
from random import choice
import json


def random_color():
    return '#' + ''.join((choice('0123456789ABCDEF') for i in range(6)))


def loadcoords(filename):
    data = json.load(open(filename))

    return data['features'][0]['geometry']['coordinates']
