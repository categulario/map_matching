[out:json][timeout:25];

// gather results
(
  way["highway"][highway!~"service,footway,steps,pedestrian,escape,raceway,bridleway,cycleway"]({y1},{x1},{y2},{x2});
);

// print results
out body;
>;
out skel qt;
