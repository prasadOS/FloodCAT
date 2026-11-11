"""Offline direct-grid reuse only after the scenario input gate passes."""
import hashlib
import json
from pathlib import Path
import numpy as np
from src.floodcat.patna import load_bundle, ROOT
from src.floodcat.patna_analysis import depth_bands, screening_summary
from src.floodcat.patna import summarize
from src.floodcat.patna_processing import inventory
from scripts.validate_multiscenario_inputs import validate


def prepare(output):
    gate=validate()
    if not gate['ready_for_dashboard'] or not gate['exposure_reuse_geometry_eligible']:
        raise ValueError('Source/grid gate failed; no row/column reuse permitted')
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    base=load_bundle();depths=[];valid=[]
    for entry in gate['entries']:
        _,a,m=inventory(ROOT/'data/demo_real'/entry['filename'])
        depths.append(a);valid.append(m)
    depths=np.stack(depths);valid=np.stack(valid)
    common=base[0]['common_valid']&valid.all(axis=0)
    records=[]
    for i,entry in enumerate(gate['entries']):
        a=dict(base[0],depth_m=depths[i],valid_depth=valid[i],common_valid=common)
        b=(a,base[1],base[2],base[3])
        records.append({'id':entry['id'],'asset_id':entry['source_identity']['asset_id'],
            'climate':entry['filename_claim']['climate'],'return_period':entry['filename_claim']['return_period_years'],
            'summary_at_0m':summarize(b,0),'bands_at_0m':depth_bands(b,0),'screening_at_0m':screening_summary(b,0)})
    artifact=output/'hazards.npz'
    np.savez_compressed(artifact,depth_m=depths,valid_depth=valid,common_valid=common)
    report={'schema_version':1,'scenarios':records,'common_cells':int(common.sum()),
            'common_area_km2':float(base[3][common].sum()),'original_common_cells':int(base[0]['common_valid'].sum()),
            'reference_transform':base[1]['target_grid']['transform'],
            'approach':'Exact CRS/affine/shape/bounds match; reuse unchanged audited extensive exposure; fixed all-scenario valid intersection',
            'exposure_epoch':2020,'provenance':json.loads((ROOT/'config/patna_multiscenario_provenance.json').read_text()),
            'hazard_sha256':hashlib.sha256(artifact.read_bytes()).hexdigest(),
            'historical_t100_original_benchmark':summarize(base,0),
            'original_budgets':base[1]['budgets'],
            'limitations':['Source selections are user-attested, not independent completed-task authentication',
              'No live per-asset GEE property query; catalog schema cross-check only',
              'Fixed 2020 exposure for future scenarios; differences are not solely attributable to climate',
              'Existing common-footprint, remapping accuracy and source uncertainty remain']}
    metadata=output/'validation.json';metadata.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (artifact,metadata)}
    (ROOT/'config/patna_scenario_checksums.json').write_text(json.dumps(pins,indent=2)+'\n')
    return report

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    print(prepare(p.parse_args().output)['common_cells'])
