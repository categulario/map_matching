[out:json][timeout:25];

// gather results
(
  // from http://wiki.openstreetmap.org/wiki/Map_Features#Special_road_types
  way["highway"][highway!~"service,footway,steps,pedestrian,escape,raceway,bridleway,cycleway"](19.441181182861328,-96.99107360839844,19.59616470336914,-96.846435546875);
);

// print results
out body;
>;
out skel qt;
