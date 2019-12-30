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

.. image:: http://gitlab.com/categulario/map_matching/badges/master/build.svg
   :target: http://gitlab.com/categulario/map_matching/badges/master/build.svg
   :alt: Build Status


My implementation of the map matching algorithm from [this article](https://www.researchgate.net/publication/308856380_Fast_Hidden_Markov_Model_Map-Matching_for_Sparse_and_Noisy_Trajectories) (Althought with some modifications). The goal is to get the streets from a gps track.

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

Download the data using the overpass api, there is a simple curl command to do that in the `overpass/` folder:

.. code:: bash

   $ cd overpass/
   $ ./get_street_graph.sh

Install python dependencies. You may want to put them inside a virtualenv:

.. code:: bash

   $ pip install -r requirements.txt

Upload the street graph to redis:

.. code:: bash

   $ ./main.py loaddata

Load the lua scripts:

.. code:: bash

   $ ./main.py loadlua

run the mapmatching task with a geojson file with a single gps track and a number indicating how many points of the input gps track to process. Use a very hight number if you want the whole route processed

.. code:: bash

   $ ./main.py mapmatch data/route.geojson 5
