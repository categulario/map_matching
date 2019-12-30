// for use inside the geojson console
(function () {
  var gps_icon = L.icon({iconUrl: 'http://categulario.tk/marker.png', iconAnchor: [10, 10]})
  var street_icon = L.icon({iconUrl: 'http://categulario.tk/marker.png', iconAnchor: [10, 10]})
  var api = window.api;

  api.data.get('map').features.forEach(function (feature) {
    if (feature.geometry.type == 'LineString') {
      feature.geometry.coordinates.forEach(function (coord) {
        L.marker(coord.reverse(), {
          icon: gps_icon,
        }).addTo(api.map);
      });
    }
  });
})();
