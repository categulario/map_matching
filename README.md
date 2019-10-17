# Map-Matching Algorithm

[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/map_matching/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

[![GitHub stars](https://img.shields.io/github/stars/categulario/map_matching.svg)](https://github.com/perusio/drupal-with-nginx/)

[![GitHub contributors](https://img.shields.io/github/contributors/categulario/map_matching.svg?color=red)](https://github.com/categulario/map_matching/graphs/contributors)

[![MIT License](https://img.shields.io/github/license/categulario/map_matching.svg?color=blue)](https://github.com/categulario/map_matching/blob/master/LICENSE.md)


My implementation of the map matching algorithm from [this article](https://www.researchgate.net/publication/308856380_Fast_Hidden_Markov_Model_Map-Matching_for_Sparse_and_Noisy_Trajectories). The goal is to get the streets from a gps track.

This is how it looks like:
![image](http://categulario.tk/map_matching_result.png)
The gray line is the gps trace and the colored lines describe the map-matched most-likely route in the streets for the vehicle.

For reference read the resulting article.

## Setup

Install:

* python3
* redis >= 3.2.0

Download the data using the overpass api, there is a simple curl command to do that in the `overpass/` folder:

```bash
$ cd overpass/
$ ./get_street_graph.sh
```

Install python dependencies. You may want to put them inside a virtualenv:

```bash
$ pip install -r requirements.py
```

Upload the street graph to redis:

```bash
$ ./main.py loaddata
```

Load the lua scripts:

```bash
$ ./main.py loadlua
```

run the mapmatching task with a geojson file with a single gps track and a number indicating how many points of the input gps track to process. Use a very hight number if you want the whole route processed

```bash
$ ./main.py mapmatching data/route.geojson 5
```
