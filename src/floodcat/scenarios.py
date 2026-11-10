"""Compact multi-scenario runtime: NumPy only, no raster processing."""
import hashlib
import io
import json
import math
import zipfile
import numpy as np
from . import patna
from .patna_analysis import screening_summary

CLIMATES={'Historical WATCH':'Historical','RCP4.5 — HadGEM2-ES, 2050':'RCP45_2050','RCP8.5 — HadGEM2-ES, 2050':'RCP85_2050'}
PERIODS=(25,50,100,250,500)
DIRECTORY=patna.ROOT/'data/processed_real/patna_scenarios'


def load_scenarios(directory=DIRECTORY):
    base=patna.load_bundle()
    try:
        pins=json.loads((patna.ROOT/'config/patna_scenario_checksums.json').read_text())
        payload={}
        for name in ('hazards.npz','validation.json'):
            p=directory/name
            if p.stat().st_size>3_000_000:raise ValueError('Oversized scenario artifact')
            payload[name]=p.read_bytes()
            if hashlib.sha256(payload[name]).hexdigest()!=pins[name]:raise ValueError('Scenario checksum mismatch')
        report=json.loads(payload['validation.json'])
        if report['schema_version']!=1 or report['reference_transform']!=base[1]['target_grid']['transform']:
            raise ValueError('Scenario grid/schema mismatch')
        with zipfile.ZipFile(io.BytesIO(payload['hazards.npz'])) as z:
            if sum(x.file_size for x in z.infolist())>10_000_000:raise ValueError('Expanded scenarios too large')
        with np.load(io.BytesIO(payload['hazards.npz']),allow_pickle=False) as z:
            if set(z.files)!={'depth_m','valid_depth','common_valid'}:raise ValueError('Scenario schema mismatch')
            depth,valid,common=z['depth_m'],z['valid_depth'],z['common_valid']
        if depth.shape!=(15,65,168) or depth.dtype.kind!='f' or valid.shape!=depth.shape or valid.dtype.kind!='b' or common.shape!=(65,168) or common.dtype.kind!='b':
            raise ValueError('Scenario array schema mismatch')
        if np.any(valid&(~np.isfinite(depth)|(depth<0))) or not np.array_equal(common,base[0]['common_valid']&valid.all(axis=0)):
            raise ValueError('Invalid scenario values or common footprint')
        entries=report['scenarios'];expected={f'{c}_T{p}' for c in CLIMATES.values() for p in PERIODS}
        if len(entries)!=15 or {e['id'] for e in entries}!=expected or int(common.sum())!=report['common_cells']:
            raise ValueError('Incomplete scenario catalog')
        bundles={}
        for i,e in enumerate(entries):
            if e['id']!=f"{e['climate']}_T{e['return_period']}":raise ValueError('Scenario identifier mismatch')
            a=dict(base[0],depth_m=depth[i],valid_depth=valid[i],common_valid=common)
            r=dict(base[1],scenario_id=e['id'],asset_id=e['asset_id'],exposure_epoch=2020)
            bundles[e['id']]=(a,r,base[2],base[3])
        for a in (depth,valid,common):a.flags.writeable=False
        historical=bundles['Historical_T100'][0]
        if not np.array_equal(historical['depth_m'],base[0]['depth_m'],equal_nan=True):raise ValueError('Historical benchmark changed')
        return bundles,report
    except (OSError,ValueError,KeyError,TypeError,zipfile.BadZipFile,EOFError) as error:
        raise patna.BundleError(f'Multi-scenario bundle unavailable or invalid: {error}') from error


def comparison_row(bundle,threshold):
    return {'Scenario ID':bundle[1]['scenario_id'],'Source asset':bundle[1]['asset_id'],'Exposure year':2020,
            **patna.summarize(bundle,threshold),**screening_summary(bundle,threshold)}


def differences(reference,selected,keys):
    return [{'Metric':k,'Reference':reference[k],'Selected':selected[k],
             'Absolute difference':selected[k]-reference[k],
             'Percentage difference':100*(selected[k]-reference[k])/reference[k] if reference[k]!=0 else None} for k in keys]
