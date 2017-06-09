# Map-Matching Algorithm

My implementation of the map matching algorithm from [this article](https://www.researchgate.net/publication/308856380_Fast_Hidden_Markov_Model_Map-Matching_for_Sparse_and_Noisy_Trajectories)

For reference read the resulting article

## Setup

Install:

* python
* redis

Download the data using the overpass api, there is a simple curl command to do that in the `overpass/` folder:

```bash
$ ./overpass/get_street_graph.sh
```

Upload the street graph to redis:

```bash
$ ./main.py loaddata
```
