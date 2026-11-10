"""Lightweight, fail-closed reader and summaries for the audited M2C-1 bundle."""
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile

import numpy as np

from .exposure import calculate_exposure
from .wri import pixel_areas_km2

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / 'data/processed_real/patna_common'
MANIFEST = ROOT / 'config/patna_dashboard_checksums.json'
DOMAIN = 'Complete common WRI cells in the uploaded buffered bounding rectangle; NOT all of Patna district'
MODE = 'REAL — Patna common-footprint exposure'


class BundleError(ValueError):
    """A missing, changed or scientifically inconsistent dashboard artifact."""


def load_bundle(directory=DIRECTORY, manifest_path=MANIFEST):
    """Verify repository-pinned bytes before parsing; never enable NumPy pickle.

    The separate manifest pins all three artifacts, including the audit itself.
    This detects accidental replacement, not malicious changes to repository code.
    No raw rasters or optional geospatial dependencies are opened at runtime.
    """
    try:
        checksums = json.loads(Path(manifest_path).read_text())
        payload = {}
        for name in ('aligned_common.npz', 'validation.json', 'audit.json'):
            path = Path(directory) / name
            if path.stat().st_size > 2_000_000:
                raise ValueError('Artifact exceeds compact bundle limit')
            payload[name] = path.read_bytes()
            if hashlib.sha256(payload[name]).hexdigest() != checksums[name]:
                raise ValueError(f'Checksum mismatch: {name}')
        report = json.loads(payload['validation.json'])
        audit = json.loads(payload['audit.json'])
        if report['schema_version'] != 1 or any(audit[k] != 'passed' for k in
                ('status', 'independent_threshold_sums', 'source_checksums', 'known_source_budgets')):
            raise ValueError('A passing M2C-1 audit is required')
        artifact = report['processed_artifact']
        if artifact['sha256'] != checksums['aligned_common.npz'] or artifact['bytes'] != len(payload['aligned_common.npz']):
            raise ValueError('Validation and bundle disagree')
        with zipfile.ZipFile(io.BytesIO(payload['aligned_common.npz'])) as archive:
            if sum(i.file_size for i in archive.infolist()) > 10_000_000:
                raise ValueError('Expanded bundle exceeds size limit')
        with np.load(io.BytesIO(payload['aligned_common.npz']), allow_pickle=False) as archive:
            arrays = {k: archive[k] for k in archive.files}
        shape = tuple(report['target_grid']['shape'])
        if shape != (65, 168):
            raise ValueError('Unexpected verified target grid')
        masks = ('valid_depth', 'common_valid', 'population_valid', 'built_valid', 'built_geometry_uncertain')
        numeric = ('depth_m', 'population_count', 'built_surface_m2', 'population_known', 'built_known_m2',
                   'population_source_coverage', 'population_available_coverage',
                   'built_source_coverage', 'built_available_coverage')
        if set(arrays) != set(masks + numeric):
            raise ValueError('Unexpected array schema')
        for key in masks + numeric:
            a = arrays[key]
            if a.shape != shape or a.dtype.kind not in ('b' if key in masks else 'fiu'):
                raise ValueError(f'Invalid array: {key}')
        common = arrays['valid_depth'] & arrays['population_valid'] & arrays['built_valid'] & ~arrays['built_geometry_uncertain']
        if not np.array_equal(common, arrays['common_valid']) or not common.any():
            raise ValueError('Inconsistent common coverage')
        for key, mask in (('depth_m', 'valid_depth'), ('population_count', 'population_valid'), ('built_surface_m2', 'built_valid')):
            values = arrays[key][arrays[mask]]
            if not np.isfinite(values).all() or (values < 0).any():
                raise ValueError(f'Invalid available values: {key}')
        for key in numeric:
            if 'coverage' in key:
                a = arrays[key]
                if not np.isfinite(a).all() or (a < 0).any() or (a > 1 + 1e-9).any():
                    raise ValueError('Invalid coverage fraction')
        if int(common.sum()) != report['common_cells'] or int(arrays['valid_depth'].sum()) != report['hazard_valid_cells']:
            raise ValueError('Coverage count mismatch')
        if audit['coverage']['common_cells'] != report['common_cells']:
            raise ValueError('Audit coverage mismatch')
        transform = tuple(report['target_grid']['transform'])
        if len(transform) != 6 or not np.isfinite(transform).all() or transform[0] <= 0 or transform[4] >= 0 or transform[1] != 0 or transform[3] != 0:
            raise ValueError('Invalid geographic grid transform')
        area = np.broadcast_to(pixel_areas_km2(transform, shape[0])[:, None], shape)
        if not np.isfinite(area).all() or (area <= 0).any() or not math.isclose(math.fsum(area[common]), report['common_area_km2'], abs_tol=1e-7):
            raise ValueError('Common area mismatch')
        for a in arrays.values():
            a.flags.writeable = False
        return arrays, report, audit, area
    except (OSError, ValueError, KeyError, TypeError, OverflowError, zipfile.BadZipFile, EOFError) as error:
        raise BundleError(f'Processed Patna bundle unavailable or invalid: {error}') from error


def summarize(bundle, threshold_m):
    arrays, report, audit, area = bundle
    common = arrays['common_valid']
    result = calculate_exposure(arrays['depth_m'], common, arrays['population_count'],
                                arrays['built_surface_m2'], threshold_m,
                                population_valid=arrays['population_valid'], built_surface_valid=arrays['built_valid'])
    wet = arrays['valid_depth'] & (arrays['depth_m'] > result.threshold_m)
    included = wet & common
    return {'Analysis domain': DOMAIN, 'Depth strictly greater than (m)': result.threshold_m,
            'Estimated exposed population (people)': result.population.total_exposed,
            'Exposed built-up surface (m²)': result.built_surface_m2.total_exposed,
            'Common flooded area (km²)': math.fsum(area[included]),
            'Common flooded cells': int(included.sum()),
            'Uploaded hazard flooded cells': int(wet.sum()),
            'Excluded flooded cells (incomplete joint coverage)': int((wet & ~common).sum()),
            'Common cells': int(common.sum()), 'Valid uploaded hazard cells': int(arrays['valid_depth'].sum()),
            'Joint coverage (% of valid hazard cells)': 100 * common.sum() / arrays['valid_depth'].sum(),
            'Common domain area (km²)': math.fsum(area[common]),
            'Interpretation': 'Modeled screening exposure; not observed impacts, damage or monetary loss'}
