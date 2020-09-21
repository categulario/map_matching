Map-Matching Algorithm
######################

.. image:: https://badges.gitter.im/Join%20Chat.svg
   :target: https://gitter.im/map_matching/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge
   :alt: Gitter

.. image:: https://img.shields.io/github/stars/categulario/map_matching.svg
   :target: https://github.com/categulario/map_matching
   :alt: GitHub stars

.. image:: https://img.shields.io/github/contributors/categulario/map_matching.svg?color=red
   :target: https://github.com/categulario/map_matching/graphs/contributors
   :alt: GitHub contributors

.. image:: https://img.shields.io/github/license/categulario/map_matching.svg?color=blue
   :target: https://github.com/categulario/map_matching/blob/master/LICENSE.txt
   :alt: GNU GPL v3

.. image:: https://gitlab.com/categulario/map_matching/badges/master/pipeline.svg
   :target: https://gitlab.com/categulario/map_matching/pipelines
   :alt: Build Status

**Im rewriting this in the Rust programming language: check the progress here:**

https://gitlab.com/categulario/mapmatching-rs

My implementation of the map matching algorithm from `this article <https://www.researchgate.net/publication/308856380_Fast_Hidden_Markov_Model_Map-Matching_for_Sparse_and_Noisy_Trajectories>`_ (Althought with some modifications). The goal is to get the streets from a gps track.

This is how it looks like:

.. image:: https://categulario.tk/map_matching_result.png
   :target: https://categulario.tk/map_matching_result.png
   :alt: Output of the example run

The gray line is the gps trace and the colored lines describe the map-matched most-likely route in the streets for the vehicle.

For reference read `the resulting article <https://categulario.tk/mapmatching.pdf>`_.

Setup
-----

You'll need python 3.5+ and a redis server running. The usage of a virtual environment is recommended.

Install from pypi:

.. code:: bash

   $ pip install mapmatching

Or install from source:

.. code:: bash

   $ cd mapmatching
   $ python setup.py install

CLI Usage
---------

Download data from OpenStreetMaps:

.. code:: bash

   $ mapmatching download -h
   $ mapmatching download -96.99107360839844 19.441181182861328 -96.846435546875 19.59616470336914 -o streets.json

And load it to redis, by default it loads it to database 1 instead of redis default of 0.

.. code:: bash

   $ mapmatching load -f streets.json

The two previous commands can be chained:

.. code:: bash

   $ mapmatching download -96.99107360839844 19.441181182861328 -96.846435546875 19.59616470336914 | mapmatching load

Then run the match task with a geojson file with a single gps track. A sample track that works with the sample bounding box is contained in the ``data/`` directory of the repository.

.. code:: bash

   $ mapmatching match -h
   $ mapmatching match data/route.geojson -o output.json

Optionally visualize it in the browser:

.. code:: bash

   $ pip install geojsonio
   $ geojsonio output.json

if the output is too big you might need to copy+paste the contents of the output file into http://geojson.io

Python API
----------

You can also import this as a module and use it in your python code. You'll still need a running redis instance.

.. code:: python

   import json

   from redis import Redis

   from mapmatching.match import match
   from mapmatching.lua import LuaManager
   from mapmatching.data import download_from_overpass, load_to_redis

   data = download_from_overpass(-96.99107360839844, 19.441181182861328, -96.846435546875, 19.59616470336914)

   redis = Redis(host='localhost', port='6379', db=0)

   load_to_redis(data, redis)

   with open('data/route.geojson', 'r') as routefile:
      route = json.load(routefile)

   coordinates = route['features'][0]['geometry']['coordinates']

   json_output = match(
      redis,
      LuaManager(redis),
      coordinates,
      10,  # How many points to process
      50,  # Radius in meters to use in the search for close points
   )

   with open('output.json', 'w') as outputfile:
      json.dump(json_output, outputfile, indent=2)
