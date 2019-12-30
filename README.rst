Map-Matching Algorithm
######################

.. image:: https://badges.gitter.im/Join%20Chat.svg
   :target: https://gitter.im/map_matching/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge
   :alt: Gitter

.. image:: https://img.shields.io/github/stars/categulario/map_matching.svg
   :target: https://github.com/perusio/drupal-with-nginx/
   :alt: GitHub stars

.. image:: https://img.shields.io/github/contributors/categulario/map_matching.svg?color=red
   :target: https://github.com/categulario/map_matching/graphs/contributors
   :alt: GitHub contributors

.. image:: https://img.shields.io/github/license/categulario/map_matching.svg?color=blue
   :target: https://github.com/categulario/map_matching/blob/master/LICENSE.md
   :alt: MIT License

.. image:: https://gitlab.com/categulario/map_matching/badges/master/pipeline.svg
   :target: https://gitlab.com/categulario/map_matching/pipelines
   :alt: Build Status


My implementation of the map matching algorithm from `this article <https://www.researchgate.net/publication/308856380_Fast_Hidden_Markov_Model_Map-Matching_for_Sparse_and_Noisy_Trajectories>`_ (Althought with some modifications). The goal is to get the streets from a gps track.

This is how it looks like:

.. image:: https://categulario.tk/map_matching_result.png
   :target: https://categulario.tk/map_matching_result.png
   :alt: Output of the example run

The gray line is the gps trace and the colored lines describe the map-matched most-likely route in the streets for the vehicle.

For reference read the resulting article.

Setup
-----

Install:

* python 3
* redis >= 3.2.0

Install python dependencies. You may want to put them inside a virtualenv:

.. code:: bash

   $ pip install -r requirements.txt

Download data from OpenStreetMaps:

.. code:: bash

   $ mapmatching download -h
   $ mapmatching download -96.99107360839844 19.441181182861328 -96.846435546875 19.59616470336914 -o streets.json

And load it to redis:

.. code:: bash

   $ mapmatching load streets.json

Then run the match task with a geojson file with a single gps track:

.. code:: bash

   $ mapmatching match -h
   $ mapmatching match data/route.geojson -o output.json

Optionally visualize it in the browser:

.. code:: bash

   $ pip install geojsonio
   $ geojsonio output.json
