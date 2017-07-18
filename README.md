# Map-Matching Algorithm

[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/map_matching/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

My implementation of the map matching algorithm from [this article](https://www.researchgate.net/publication/308856380_Fast_Hidden_Markov_Model_Map-Matching_for_Sparse_and_Noisy_Trajectories). The goal is to get the streets from a gps track.

For reference read the resulting article

## Setup

Install:

* python3
* redis >= 3.2.0

Download the data using the overpass api, there is a simple curl command to do that in the `overpass/` folder:

```bash
$ ./overpass/get_street_graph.sh
```

Install python dependencies. You may want to put them inside a virtualenv:

```bash
$ pip install -r requirements.py
```

Upload the street graph to redis:

```bash
$ ./main.py loaddata
```

Finally run one of the available tasks to do something.
