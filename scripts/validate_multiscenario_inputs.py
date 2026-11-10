"""Offline M2D input gate. Exit 2 when scientific identity remains unverified."""
import argparse
import json
from pathlib import Path
import numpy as np

from src.floodcat.patna import load_bundle
from src.floodcat.patna_processing import ROOT, inventory, check_provenance

PERIODS = (25, 50, 100, 250, 500)
CLIMATES = ('Historical', 'RCP45_2050', 'RCP85_2050')


def same_grid(info, reference):
    return (info['shape'] == reference['shape'] and info['crs_wkt'] == reference['crs_wkt']
            and info['transform'] == reference['transform'] and info['bounds'] == reference['bounds'])


def assess_source(filename, digest, provenance):
    # The existing signed-by-content recipe/provenance describes only this asset.
    source = provenance['sources']['hazard']
    verified = filename == 'FloodCAT_Patna_WRI_Historical_T100.tif' and digest == source['sha256']
    return {'verified_against_existing_recipe': verified,
            'asset_id': source.get('asset_id') if verified else None,
            'basis': 'Existing M2C-1 user-attested recipe, checksums and independent pilot overlap' if verified else
                     'Filename label only; no matching export recipe or task/source metadata supplied',
            'task_level_independently_verified': False}


def validate(directory=ROOT/'data/demo_real'):
    bundle = load_bundle()
    provenance = json.loads((ROOT/'config/patna_upload_provenance.json').read_text())
    check_provenance(provenance)
    reference, _, _ = inventory(directory/'FloodCAT_Patna_WRI_Historical_T100.tif')
    entries, depths, masks, blockers = [], {}, {}, []
    for climate in CLIMATES:
        for period in PERIODS:
            name = f'FloodCAT_Patna_WRI_{climate}_T{period}.tif'
            info, values, valid = inventory(directory/name)
            identity = assess_source(name, info['sha256'], provenance)
            geometry = same_grid(info, reference)
            numeric = bool(np.all(values[valid] >= 0) and not np.isinf(values).any())
            key = f'{climate}_T{period}'
            if not identity['verified_against_existing_recipe']: blockers.append(key+': source selection/units unverified')
            if not geometry: blockers.append(key+': grid mismatch; cannot directly reuse exposure')
            if not numeric: blockers.append(key+': invalid depth values')
            entries.append({'id': key, 'filename': name, 'metadata': info,
                'filename_claim': {'flood_type': 'riverine', 'climate': climate, 'return_period_years': period,
                                  'gcm': 'WATCH' if climate == 'Historical' else 'HadGEM2-ES (requested, not verified)',
                                  'year': 1980 if climate == 'Historical' else 2050,
                                  'depth_units': 'metres (expected, not independently stored in TIFF)'},
                'source_identity': identity, 'exact_reference_grid': geometry, 'nonnegative_depth': numeric,
                'ready_for_dashboard': identity['verified_against_existing_recipe'] and geometry and numeric})
            depths[key], masks[key] = values, valid
    diagnostics = []
    for climate in CLIMATES:
        for low, high in zip(PERIODS[:-1], PERIODS[1:]):
            x,y=f'{climate}_T{low}',f'{climate}_T{high}'
            if depths[x].shape != depths[y].shape: continue
            common=masks[x]&masks[y]
            diagnostics.append({'lower':x,'higher':y,'valid_pair_cells':int(common.sum()),
                                'higher_depth_less_than_lower_cells':int((common&(depths[y]<depths[x])).sum())})
    comparison = bundle[0]['common_valid'].copy()
    compatible = all(e['exact_reference_grid'] for e in entries)
    if compatible:
        for mask in masks.values(): comparison &= mask
    return {'schema_version':1, 'status':'blocked' if blockers else 'passed', 'ready_for_dashboard':not blockers,
            'entries':entries, 'blockers':blockers, 'ordering_diagnostic_only':diagnostics,
            'exposure_reuse_geometry_eligible':compatible,
            'candidate_common_cells':int(comparison.sum()) if compatible else None,
            'original_common_cells':int(bundle[0]['common_valid'].sum()),
            'processing_performed':False,
            'note':'No scenario exposure published until source identities are evidenced; CMIP5/RCP is not CMIP6/SSP. '
                   'Missing GEE task provenance is disclosed separately from absent source-selection evidence.'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report=validate()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(report['status'],len(report['entries']),'inputs;',len(report['blockers']),'blockers')
    raise SystemExit(2 if report['blockers'] else 0)


if __name__=='__main__': main()
