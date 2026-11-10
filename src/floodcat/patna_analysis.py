"""Presentation summaries on the verified common footprint; no remapping."""
import math
import numpy as np
from .patna import summarize

MODULES = ('Overview', 'Hazard', 'Exposure', 'Depth severity', 'Compare', 'Data & methods')
BANDS = (('>0–1 m', 0., 1.), ('>1–2 m', 1., 2.), ('>2–5 m', 2., 5.), ('>5 m', 5., np.inf))


def depth_bands(bundle, threshold_m=0.):
    # Reuse the existing engine's threshold validation, including bool/string rejection.
    summary = summarize(bundle, threshold_m)
    threshold = summary['Depth strictly greater than (m)']
    a, _, _, area = bundle
    result = []
    for label, lo, hi in BANDS:
        selected = a['common_valid'] & (a['depth_m'] > max(lo, threshold)) & (a['depth_m'] <= hi)
        result.append({'Depth band': label, 'Threshold (m)': threshold,
                       'Flooded cells': int(selected.sum()), 'Area (km²)': math.fsum(area[selected]),
                       'Estimated people': math.fsum(a['population_count'][selected]),
                       'Built-up surface (m²)': math.fsum(a['built_surface_m2'][selected])})
    return result
