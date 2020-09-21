import requests
import os


def download_from_overpass(x1, y1, x2, y2):
    ''' queries the overpass API and returns the data as string '''
    # http://wiki.openstreetmap.org/wiki/Map_Features#Special_road_types
    with open(os.path.join(
        os.path.dirname(__file__),
        'overpass/streets.overpassql'
    )) as queryfile:
        query = queryfile.read().format(
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
        )

    res = requests.post(
        'http://overpass-api.de/api/interpreter', data=query,
    )

    if res.status_code != 200:
        raise ValueError(res.text)

    return res.json()


def load_to_redis(data, redis):
    ''' loads the given data to redis '''
    for i, element in enumerate(data['elements']):
        etype = element['type']
        eid = element['id']

        if etype == 'node':
            # load to GEOHASH with ID
            redis.geoadd(
                'base:nodehash', element['lon'], element['lat'], eid
            )
            # add to node count
            redis.pfadd('base:node:count', eid)

        elif etype == 'way':
            # add nodes to way
            redis.rpush('base:way:{}:nodes'.format(eid), *element['nodes'])
            # add to way count
            redis.pfadd('base:way:count', eid)

            # add this way to node relations
            for node in element['nodes']:
                redis.rpush('base:node:{}:ways'.format(node), eid)

            # add this way's tags
            for tag, value in element['tags'].items():
                redis.set('base:way:{}:{}'.format(eid, tag), value)
