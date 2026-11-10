"""Native-cell Leaflet map; no reprojection/resampling of scientific arrays.

Leaflet handles only display projection. Each EPSG:4326 cell's four boundaries
are projected to Web Mercator at draw time. Canvas rectangles are flat-shaded,
never interpolated, and hover reads the original native cell by affine index.
"""
import json
from pathlib import Path

import numpy as np
import streamlit.components.v1 as components

STATIC = Path(__file__).with_name('static')


def map_payload(depth, valid, common, transform):
    depth, valid, common = np.asarray(depth), np.asarray(valid), np.asarray(common)
    if depth.ndim != 2 or valid.shape != depth.shape or common.shape != depth.shape:
        raise ValueError('Map arrays must share a 2D grid')
    if valid.dtype.kind != 'b' or common.dtype.kind != 'b':
        raise ValueError('Map masks must be boolean')
    dx, rx, west, ry, dy, north = transform
    if rx != 0 or ry != 0 or dx <= 0 or dy >= 0 or not np.isfinite(transform).all():
        raise ValueError('Map requires north-up EPSG:4326 affine coordinates')
    if np.any(valid & (~np.isfinite(depth) | (depth < 0))) or np.any(common & ~valid):
        raise ValueError('Map valid values/masks are inconsistent')
    rows, cols = depth.shape
    bounds = [[north + rows * dy, west], [north, west + cols * dx]]
    if not (-85 < bounds[0][0] < bounds[1][0] < 85 and -180 <= west < bounds[1][1] <= 180):
        raise ValueError('Map grid outside regional Mercator display bounds')
    return {'rows': rows, 'cols': cols, 'transform': list(transform), 'bounds': bounds,
            'depth': [float(v) if ok else None for v, ok in zip(depth.flat, valid.flat)],
            'common': common.ravel().astype(int).tolist()}


def map_html(depth, valid, common, transform):
    payload = map_payload(depth, valid, common, transform)
    css = (STATIC/'leaflet/leaflet.css').read_text()
    js = (STATIC/'leaflet/leaflet.js').read_text().split('//# sourceMappingURL=')[0]
    template = (STATIC/'native_map.html').read_text()
    return template.replace('/* LEAFLET_CSS */', css).replace('/* LEAFLET_JS */', js).replace(
        '/* GRID_DATA */', json.dumps(payload, allow_nan=False, separators=(',', ':')))


def render_map(depth, valid, common, transform, *, height=460):
    components.html(map_html(depth, valid, common, transform), height=height, scrolling=False)
