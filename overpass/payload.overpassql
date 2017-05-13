[out:json][timeout:25];

// gather results
(
  // query part for: “highway=*”
  way["highway"](19.441181182861328,-96.99107360839844,19.59616470336914,-96.846435546875);
);

// print results
out body;
>;
out skel qt;
