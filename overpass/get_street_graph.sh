#!/bin/bash

curl --data-urlencode data@payload.overpassql http://overpass-api.de/api/interpreter > street_graph.json
