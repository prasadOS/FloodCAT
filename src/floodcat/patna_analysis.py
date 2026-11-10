"""Presentation summaries on the verified common footprint; no remapping."""
import math
import numpy as np
from .patna import summarize

MODULES = ('Overview', 'Hazard', 'Exposure', 'Vulnerability', 'Compare', 'Data & methods')
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


SCREENING_LABEL = 'Depth-weighted exposure screening — not a validated vulnerability model.'
POP_WEIGHT_LABEL = 'Depth-weighted population (person-metres)'
BUILT_WEIGHT_LABEL = 'Depth-weighted built-up surface (m²·m)'


def weighted_cells(bundle, threshold_m=0.):
    """Native-cell products; NaN outside common, zero for common below threshold.

    A below-threshold indicator is zero by definition, not imputed exposure.
    Only selected cells are multiplied; unknown source values are never used.
    The existing engine validates input availability and strict thresholds first.
    """
    summary = summarize(bundle, threshold_m)
    a = bundle[0]
    common = a['common_valid']
    selected = common & (a['depth_m'] > summary['Depth strictly greater than (m)'])
    products = []
    for key in ('population_count', 'built_surface_m2'):
        values = np.full(common.shape, np.nan, dtype=float)
        values[common] = 0.
        try:
            with np.errstate(over='raise', invalid='raise'):
                values[selected] = np.asarray(a[key][selected], dtype=float) * np.asarray(a['depth_m'][selected], dtype=float)
        except FloatingPointError as error:
            raise ValueError('Depth-weighted indicator exceeds finite float range') from error
        if not np.isfinite(values[common]).all():
            raise ValueError('Depth-weighted indicator exceeds finite float range')
        values.flags.writeable = False
        products.append(values)
    return selected, products[0], products[1]


def screening_summary(bundle, threshold_m=0.):
    selected, pop, built = weighted_cells(bundle, threshold_m)
    try:
        pop_total = math.fsum(pop[selected])
        built_total = math.fsum(built[selected])
    except OverflowError as error:
        raise ValueError('Depth-weighted indicator sum exceeds finite float range') from error
    return {'Screening definition': SCREENING_LABEL, 'Depth strictly greater than (m)': float(threshold_m),
            POP_WEIGHT_LABEL: pop_total, BUILT_WEIGHT_LABEL: built_total,
            **{f'Population at depth >{t:g} m (people)': summarize(bundle, t)['Estimated exposed population (people)']
               for t in (1., 2., 5.)},
            'Domain': 'Common-data footprint; not all of Patna district.',
            'Built-up indicator interpretation': 'm²·m (dimensionally m³); not flood volume or building damage',
            'Not estimated': 'Vulnerability, casualties, displacement, damage, monetary loss or annualized impacts'}


def priority_cells(bundle, threshold_m=0., limit=10):
    """Rank complete flooded native cells, descending person-metres.

    Equal products use row, then column as a stable tie-break. Coordinates are
    native cell centres, not administrative units or neighborhood risk locations.
    """
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError('Priority table limit must be a positive integer')
    selected, weights, _ = weighted_cells(bundle, threshold_m)
    a, report, _, _ = bundle
    dx, _, west, _, dy, north = report['target_grid']['transform']
    indices = sorted(zip(*np.nonzero(selected)), key=lambda rc: (-float(weights[rc]), *rc))[:limit]
    return [{'Rank': rank, 'WRI row (0-based)': int(r), 'WRI column (0-based)': int(c),
             'Longitude (°E)': west + dx*(c+.5), 'Latitude (°N)': north + dy*(r+.5),
             'Modeled flood depth (m)': float(a['depth_m'][r,c]),
             'Estimated population (people/cell)': float(a['population_count'][r,c]),
             POP_WEIGHT_LABEL: float(weights[r,c])}
            for rank, (r,c) in enumerate(indices,1)]
