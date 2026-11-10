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


def map_payload(depth, valid, common, transform, *, population=None, weighted_population=None, threshold_m=0., initial_layer="depth"):
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
    payload = {'rows': rows, 'cols': cols, 'transform': list(transform), 'bounds': bounds,
            'depth': [float(v) if ok else None for v, ok in zip(depth.flat, valid.flat)],
            'common': common.ravel().astype(int).tolist()}
    if initial_layer not in ('depth', 'weighted'):
        raise ValueError('Unknown initial map layer')
    if population is not None or weighted_population is not None:
        pop, weights = np.asarray(population), np.asarray(weighted_population)
        if pop.shape != depth.shape or weights.shape != depth.shape:
            raise ValueError('Map indicators must match the native grid')
        if not np.isfinite(threshold_m) or threshold_m < 0:
            raise ValueError('Map threshold must be finite and nonnegative')
        if any(np.any(~np.isfinite(v[common]) | (v[common] < 0)) for v in (pop, weights)):
            raise ValueError('Map common-cell indicators must be finite and nonnegative')
        expected = np.zeros(depth.shape)
        wet = common & (depth > threshold_m)
        with np.errstate(over='ignore', invalid='ignore'):
            expected[wet] = np.asarray(pop[wet], dtype=float) * np.asarray(depth[wet], dtype=float)
        if not np.array_equal(weights[common], expected[common]):
            raise ValueError('Map indicator disagrees with strict native-cell product')
        payload.update(population=[float(v) if ok else None for v, ok in zip(pop.flat, common.flat)],
                       weightedPopulation=[float(v) if ok else None for v, ok in zip(weights.flat, common.flat)],
                       threshold=float(threshold_m), initialLayer=initial_layer)
    elif initial_layer != 'depth':
        raise ValueError('Weighted layer requires verified indicator arrays')
    return payload


def map_html(depth, valid, common, transform, **indicators):
    payload = map_payload(depth, valid, common, transform, **indicators)
    css = (STATIC/'leaflet/leaflet.css').read_text()
    js = (STATIC/'leaflet/leaflet.js').read_text().split('//# sourceMappingURL=')[0]
    template = (STATIC/'native_map.html').read_text()
    return template.replace('/* LEAFLET_CSS */', css).replace('/* LEAFLET_JS */', js).replace(
        '/* GRID_DATA */', json.dumps(payload, allow_nan=False, separators=(',', ':')))


def render_map(depth, valid, common, transform, *, height=460, **indicators):
    components.html(map_html(depth, valid, common, transform, **indicators), height=height, scrolling=False)
