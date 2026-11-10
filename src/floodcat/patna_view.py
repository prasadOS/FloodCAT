"""Two-mode dashboard's real Patna modules, using only verified local arrays."""
import json
import zlib

import pandas as pd
import plotly.express as px
import streamlit as st

from . import patna, wri
from .exports import table_csv
from .geographic_map import render_map
from .patna_analysis import MODULES, depth_bands


def pilot_reference(threshold):
    """Preserve the small independently verified pilot's metrics and downloads."""
    with st.expander('Verified small WRI pilot · reference & downloads'):
        try:
            depth, nodata, manifest, tiff, metadata = wri.load_pilot()
            summary = wri.summarize(depth, nodata, threshold)
        except (OSError, ValueError, KeyError, TypeError, zlib.error) as error:
            st.warning(f'Small WRI pilot unavailable: {error}')
            return
        st.caption('Separate historical WATCH T100 pilot; hazard only. Its area is not the common exposure domain.')
        st.dataframe(pd.DataFrame([summary]), hide_index=True, width='stretch')
        st.markdown(f"{manifest['attribution']}. [Catalog and terms]({wri.SOURCE})")
        st.download_button('Download pilot GeoTIFF', tiff, wri.TIFF, 'image/tiff')
        st.download_button('Download pilot manifest', metadata, wri.MANIFEST, 'application/json')
        st.download_button('Download pilot summary CSV', table_csv([{'Asset': manifest['asset_id'], **summary}]),
                           'patna_pilot_summary.csv', 'text/csv')


def kpis(s):
    a, b, c, d = st.columns(4)
    a.metric('Estimated people exposed', f"{s['Estimated exposed population (people)']:,.0f}")
    b.metric('Built-up surface exposed (km²)', f"{s['Exposed built-up surface (m²)']/1e6:,.3f}")
    c.metric('Flooded area (km²)', f"{s['Common flooded area (km²)']:,.2f}")
    d.metric('Flooded cells', f"{s['Common flooded cells']:,}")


def band_charts(rows):
    frame = pd.DataFrame(rows)
    a, b = st.columns(2)
    with a:
        st.plotly_chart(px.bar(frame, x='Depth band', y='Estimated people', color_discrete_sequence=['#168078']), width='stretch')
    with b:
        built = frame.assign(**{'Built-up surface (km²)': frame['Built-up surface (m²)']/1e6})
        st.plotly_chart(px.bar(built, x='Depth band', y='Built-up surface (km²)', color_discrete_sequence=['#2879b9']), width='stretch')


def methods(bundle):
    _, report, audit, _ = bundle
    st.subheader('Data & methods')
    st.markdown('**Analysis domain.** Complete common WRI cells in the uploaded buffered bounding rectangle, '
                '**not all of Patna district**. No district polygon is bundled. Joint coverage is by '
                'valid uploaded hazard-cell count, not area or population. Excluded flooded cells have '
                'unknown joint exposure; their quantities are not redistributed. Coverage selection may '
                'bias regional interpretation. Valid zero is retained; partial, missing, NaN and '
                'geometrically uncertain cells never become zero exposure.\n\n'
                '**Hazard.** WRI Aqueduct Floods Hazard Maps V2, historical WATCH T100 '
                '(100-year return period), inundation depth in metres. This is modeled screening, '
                'not an observed event. Flood protection is not represented and backwater effects are omitted.\n\n'
                '**Exposure.** WorldPop / University of Southampton, legacy India 2020 population '
                'counts, `WorldPop/GP/100m/pop/IND_2020`, CC BY 4.0; not R2025A. European Commission '
                'JRC, Pesaresi and Politis (2023), GHS-BUILT-S R2023A, '
                '`JRC/GHSL/P2023A/GHS_BUILT_S/2020`, total `built_surface` m²/cell. Reuse with source '
                'acknowledgement; DOI 10.2905/9F06F36F-4B11-47EC-ABB0-4F8B7B1D72EA.\n\n'
                '**Allocation.** Preprocessed conservative physical-area intersections: population '
                'on the shared CRS, GHSL actual World Mollweide to WRI WGS84. Exposure is uniform '
                'inside each source pixel. No ordinary interpolation, imputation or runtime remapping. '
                'Whole common cells contribute at **depth > threshold**; area uses the WGS84 ellipsoid. '
                'Depth bands use lower-exclusive, upper-inclusive intervals and reconcile to the selected '
                'threshold total.\n\n'
                '**Map.** Locally bundled Leaflet 1.9.4 (BSD-2-Clause), OSM geographic basemap and '
                'flat-shaded native grid cells. EPSG:4326 cell edges are displayed in Web Mercator, '
                'without smoothing or invented detail. Diagonals identify incomplete joint exposure. '
                'Zoom/pan/layers/fit and hover/click inspect native cells. Gray surroundings are outside '
                'the export, not a district boundary. Tiles load only for the current viewport; no '
                'prefetch or bulk download. [OSM attribution](https://www.openstreetmap.org/copyright) · '
                '[Tile policy](https://operations.osmfoundation.org/policies/tiles/). A tile failure '
                'does not remove scientific layers.\n\n'
                '**Uncertainty.** User-supplied export recipe and bitwise pilot overlap checks support '
                'source identity; export task IDs/times and upstream GHSL NaN cause remain unverified. '
                'Sampled geometric convergence is not a global accuracy bound. Exposure is not damage '
                'or monetary loss. T50/T500 and future RCP rasters are not available in this bundle.')
    st.markdown('[WRI catalog and terms](https://developers.google.com/earth-engine/datasets/catalog/WRI_Aqueduct_Flood_Hazard_Maps_V2) · '
                '[WorldPop catalog](https://developers.google.com/earth-engine/datasets/catalog/WorldPop_GP_100m_pop) · '
                '[GHSL catalog](https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S)')
    with st.expander('Audit, provenance & conservation budgets'):
        st.json({'audit': audit['status'], 'known_source_budgets': report['budgets'],
                 'target_grid': report['target_grid'], 'provenance': report['provenance'],
                 'limitations': report['limitations']})
    st.download_button('Download validation record', json.dumps(report, indent=2),
                       'patna_validation.json', 'application/json')


def render(sidebar=st.sidebar):
    section = sidebar.radio('Module', MODULES)
    threshold = sidebar.slider('Flood-depth threshold (m)', 0.0, 8.0, 0.0, 0.25,
                               help='Strict depth > threshold. Exposure and area use complete common cells only.')
    sidebar.caption('Historical WATCH T100 · WorldPop 2020 · GHSL 2020')
    st.title('Patna | Flood exposure')
    st.caption('Historical T100 · Common-data footprint · Modeled screening')
    try:
        bundle = patna.load_bundle()
    except patna.BundleError as error:
        st.warning(f'{error}. Restore the verified processed bundle and checksum manifest; no exposure results are shown.')
        pilot_reference(threshold)
        return
    a, report, audit, area = bundle
    s = patna.summarize(bundle, threshold)
    kpis(s)
    st.caption(f"Joint coverage **{s['Joint coverage (% of valid hazard cells)']:.2f}%** · "
               f"{s['Common cells']:,}/{s['Valid uploaded hazard cells']:,} uploaded hazard cells · "
               f"{s['Common domain area (km²)']:,.2f} km² · **Not all of Patna district**")
    st.markdown(f"⚠ **{s['Excluded flooded cells (incomplete joint coverage)']:,} excluded flooded cells** "
                f"of {s['Uploaded hazard flooded cells']:,} above {threshold:g} m · incomplete joint coverage; exposure unknown.")
    if section in ('Overview', 'Hazard'):
        st.subheader('Historical riverine hazard' if section == 'Hazard' else 'Study-area snapshot')
        render_map(a['depth_m'], a['valid_depth'], a['common_valid'], report['target_grid']['transform'],
                   height=540 if section == 'Hazard' else 430)
        st.caption('Native modeled depths, including excluded exposure cells. Threshold affects summaries, not map values. '
                   'Switch layers to inspect joint coverage; diagonals mark incomplete exposure.')
        if section == 'Hazard':
            pilot_reference(threshold)
    elif section in ('Exposure', 'Depth severity'):
        st.subheader('Exposure by depth' if section == 'Exposure' else 'Depth severity')
        rows = depth_bands(bundle, threshold)
        st.caption(f'Non-overlapping bands, clipped to depth > {threshold:g} m. Values sum to the KPIs above.')
        band_charts(rows)
        st.dataframe(pd.DataFrame(rows), hide_index=True, width='stretch')
        st.download_button('Download depth-band CSV', table_csv(rows), 'patna_common_depth_bands.csv', 'text/csv')
    elif section == 'Compare':
        st.subheader('T100 threshold comparison')
        st.caption('One verified historical hazard raster; thresholds are screening choices, not separate events or climate scenarios.')
        comparisons = [patna.summarize(bundle, t) for t in sorted({0., 1., 2., 5., threshold})]
        frame = pd.DataFrame(comparisons)
        st.dataframe(frame[['Depth strictly greater than (m)', 'Estimated exposed population (people)',
                            'Exposed built-up surface (m²)', 'Common flooded area (km²)', 'Common flooded cells',
                            'Excluded flooded cells (incomplete joint coverage)']], hide_index=True, width='stretch')
        st.plotly_chart(px.bar(frame, x='Depth strictly greater than (m)', y='Estimated exposed population (people)',
                               color_discrete_sequence=['#168078']), width='stretch')
        st.caption('Future genuine T50/T500/RCP4.5/RCP8.5 comparisons require separately verified compatible inputs.')
    else:
        methods(bundle)
        pilot_reference(threshold)
    with st.expander('Export summaries', expanded=section == 'Data & methods'):
        st.download_button('Download current exposure CSV', table_csv([s]), 'patna_common_exposure.csv', 'text/csv')
        st.download_button('Download threshold comparison CSV',
                           table_csv([patna.summarize(bundle, t) for t in (0., 1., 2., 5.)]),
                           'patna_common_thresholds.csv', 'text/csv')
    st.caption('Estimated physical exposure · not observed impacts, measured damage or financial loss. '
               'Display values are rounded; CSVs retain numerical precision.')
