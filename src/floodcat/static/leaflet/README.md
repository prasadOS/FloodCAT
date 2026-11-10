# Leaflet 1.9.4 (BSD-2-Clause)

Unmodified distribution files from the pinned npm package via jsDelivr:

- https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js
- https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css
- https://cdn.jsdelivr.net/npm/leaflet@1.9.4/LICENSE

SHA-256 base64 (matches the upstream Leaflet 1.9.4 quick-start SRI pins):

- JS: `20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=`
- CSS: `p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=`

License retained in LICENSE. No JavaScript CDN request is needed at runtime;
the application embeds these files into its local map component. Marker images
are unused; the layer selector is always expanded and needs no image sprite.
The renderer removes the optional source-map comment from the embedded JS.
Only OSM viewport tiles are external; failures do not affect scientific layers.
No Python dependency was added. This is a display library, not a remapping engine.
