# from http://stackoverflow.com/questions/15736995/how-can-i-quickly-estimate-the-distance-between-two-latitude-longitude-points
from math import radians, cos, sin, asin, sqrt
from . import random_color

def distance(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    m = 6367 * c * 1000

    return m

def point(coords, properties=None):
    return {
        'type': 'Feature',
        'properties': properties if properties else dict(),
        'geometry': {
            'type': 'Point',
            'coordinates': coords,
        },
    }

def line_string(coordinates, properties=None):
    defaults = {
        'stroke': random_color(),
        'stroke-width': 4,
        'stroke-opacity': 1,
    }

    properties = properties if properties else dict()

    return {
        'type': 'Feature',
        'properties': {**defaults, **properties},
        'geometry': {
            'type': 'LineString',
            'coordinates': coordinates,
        },
    }
