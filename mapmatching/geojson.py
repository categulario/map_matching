from random import choice


def random_color():
    return '#' + ''.join((choice('0123456789ABCDEF') for i in range(6)))


def feature_collection(features):
    return {
        'type': 'FeatureCollection',
        'features': list(features),
    }


def point(coords, properties=None):
    return {
        'type': 'Feature',
        'properties': properties if properties else dict(),
        'geometry': {
            'type': 'Point',
            'coordinates': list(coords),
        },
    }


def line_string(coordinates, properties=None):
    defaults = {
        'stroke': random_color(),
        'stroke-width': 4,
        'stroke-opacity': 1,
    }

    properties = properties or dict()

    return {
        'type': 'Feature',
        'properties': {**defaults, **properties},
        'geometry': {
            'type': 'LineString',
            'coordinates': list(coordinates),
        },
    }


def polygon(coordinates, properties=None):
    properties = properties or dict()

    defaults = {
        'fill': random_color(),
        'fill-opacity': 0.5
    }

    return {
        'type': 'Feature',
        'properties': {**defaults, **properties},
        'geometry': {
            'type': 'Polygon',
            'coordinates': [list(coordinates)],
        },
    }
