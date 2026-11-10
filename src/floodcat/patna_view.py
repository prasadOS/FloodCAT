"""Two-mode dashboard's real Patna modules, using only verified local arrays."""
import json
import zlib

import pandas as pd
import plotly.express as px
import streamlit as st

from . import patna, wri
from .exports import table_csv
from .geographic_map import render_map
from .patna_analysis import (MODULES, depth_bands, weighted_cells, screening_summary, priority_cells,
                             SCREENING_LABEL, POP_WEIGHT_LABEL, BUILT_WEIGHT_LABEL)


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
    frame['Built-up surface (km²)'] = frame['Built-up surface (m²)']/1e6
    for column, (value, title, unit, color) in zip(st.columns(3), (
            ('Estimated people', 'Estimated population', 'People', '#168078'),
            ('Built-up surface (km²)', 'Built-up surface', 'km²', '#2879b9'),
            ('Area (km²)', 'Flooded area', 'km²', '#6366a3'))):
        figure = px.bar(frame, x='Depth band', y=value, title=title,
                        color_discrete_sequence=[color], labels={value: unit})
        figure.update_traces(hovertemplate='%{x}<br>%{y:,.2f} '+unit+'<extra></extra>')
        figure.update_layout(height=310, margin=dict(l=20,r=10,t=55,b=30), xaxis_title=None)
        with column:
            st.plotly_chart(figure, width='stretch')


def vulnerability_screening(bundle, threshold):
    st.subheader(SCREENING_LABEL)
    indicators = screening_summary(bundle, threshold)
    st.caption('Deeper-water population exposure below uses fixed strict depth thresholds, independent of the sidebar selection.')
    for column, t in zip(st.columns(3), (1., 2., 5.)):
        column.metric(f'Population >{t:g} m (people)', f"{indicators[f'Population at depth >{t:g} m (people)']:,.0f}")
    st.caption(f'Weighted indicators below use common cells with modeled depth > {threshold:g} m.')
    first, second = st.columns(2)
    first.metric(POP_WEIGHT_LABEL, f"{indicators[POP_WEIGHT_LABEL]:,.0f}")
    second.metric(BUILT_WEIGHT_LABEL, f"{indicators[BUILT_WEIGHT_LABEL]:,.0f}")
    st.caption('Built-up weighting is m²·m (dimensionally m³), not flood volume or physical building damage.')
    st.markdown('Highlights cells combining greater modeled flood depth and more exposed population; '
                'not a prediction of casualties or damage.')
    a, report, _, _ = bundle
    _, pop_weights, _ = weighted_cells(bundle, threshold)
    render_map(a['depth_m'], a['valid_depth'], a['common_valid'], report['target_grid']['transform'],
               population=a['population_count'], weighted_population=pop_weights,
               threshold_m=threshold, initial_layer='weighted', height=510)
    st.caption('Native raster-cell screening only; coarse WRI cells are not neighborhood-level risk estimates.')
    rows = priority_cells(bundle, threshold)
    st.markdown('**Top 10 complete-cell screening priorities**')
    st.caption('Ranked by person-metres within the selected flooded common cells; not administrative or community rankings. '
               'Coordinates are native cell centres. Ties use row then column.')
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, width='stretch', column_config={
            'Longitude (°E)': st.column_config.NumberColumn(format='%.5f'),
            'Latitude (°N)': st.column_config.NumberColumn(format='%.5f'),
            'Modeled flood depth (m)': st.column_config.NumberColumn(format='%.3f'),
            'Estimated population (people/cell)': st.column_config.NumberColumn(format='%.0f'),
            POP_WEIGHT_LABEL: st.column_config.NumberColumn(format='%.1f')})
        st.download_button('Download raster-cell priorities CSV',
                           table_csv([{'Screening definition': SCREENING_LABEL, 'Depth strictly greater than (m)': threshold,
                                       'Domain': 'Common-data footprint; not all of Patna district.', **row} for row in rows]),
                           'patna_cell_priorities.csv', 'text/csv')
    else:
        st.caption('No complete flooded cells above the selected threshold; no cell priorities are ranked.')
    st.download_button('Download screening indicators CSV', table_csv([indicators]), 'patna_depth_weighted_screening.csv', 'text/csv')
    with st.expander('What would a validated vulnerability model need?'):
        st.markdown('UNDRR defines vulnerability as susceptibility to harm, distinct from hazard and exposure. '
                    'These inputs lack validated social vulnerability, building types/fragility, floor elevations, '
                    'occupancy, warning/evacuation capacity and locally validated depth-impact functions. '
                    'Genuine impact estimation needs those data, outcome-specific calibration/validation and '
                    'uncertainty analysis. No susceptibility coefficient, casualty, displacement, damage ratio '
                    'or monetary loss is inferred here. T100 is not an annualized expected impact.')


def methods(bundle):
    _, report, audit, _ = bundle
    st.subheader('Data & methods')
    st.markdown('**Analysis domain.** Complete common WRI cells in the uploaded buffered bounding rectangle, '
                '**not all of Patna district**. No district polygon is bundled. Joint coverage is by '
                'valid uploaded hazard-cell count, not area or population. Excluded flooded cells have '
                'unknown joint exposure; their quantities are not redistributed. Coverage selection may '
                'bias regional interpretation. Valid zero is retained; partial, missing, NaN and '
                'geometrically uncertain cells never become zero exposure.\n\n'
                '**Hazard.** WRI Aqueduct V2 — WATCH T100 (Aqueduct Floods Hazard Maps V2), '
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
    with st.expander('Hazard, exposure, vulnerability and risk · definitions & formulas'):
        st.markdown('**Hazard** is the potentially damaging flood process; here, a modeled depth scenario. '
                    '**Exposure** is people/assets located in hazard-prone cells. **Vulnerability**, per '
                    '[UNDRR](https://www.undrr.org/terminology/vulnerability), is susceptibility to harm '
                    'from physical, social, economic and environmental conditions. **Risk** concerns potential '
                    'losses arising from hazard, exposure, vulnerability and capacity; these products alone '
                    'do not estimate comprehensive or probabilistic risk.\n\n'
                    'For S = complete common cells with depthᵢ > selected threshold: '
                    '**population weighting = Σᵢ∈S populationᵢ × depthᵢ**, in **person-metres**; '
                    '**built-up weighting = Σᵢ∈S built_surface_m²ᵢ × depthᵢ**, in **m²·m** '
                    '(dimensionally m³). This is exposure weighting, not flood volume, building damage, '
                    'affected population, mortality or displacement. The map and rankings use the same '
                    'native-cell population products; no high-resolution hotspots are interpolated. '
                    'Common cells below the selected threshold have a zero indicator by definition; '
                    'incomplete cells remain unavailable, never zero-filled. Fixed >1, >2 and >5 m '
                    'population indicators are separate strict-threshold sums. No annualized expected '
                    'impacts are calculated from the T100 scenario.\n\n'
                    'Methodological context: [UNDRR exposure](https://www.undrr.org/terminology/exposure) · '
                    '[UNDRR disaster risk](https://www.undrr.org/terminology/disaster-risk); '
                    'Huizinga, de Moel & Szewczyk (2017), *Global flood depth-damage functions: '
                    'Methodology and the database with guidelines*, JRC, '
                    '[doi:10.2760/16510](https://doi.org/10.2760/16510); Merz et al. (2010), '
                    '*Assessment of economic flood damage*, '
                    '[doi:10.5194/nhess-10-1697-2010](https://doi.org/10.5194/nhess-10-1697-2010). '
                    'These references explain additional impact-model requirements; **no cited damage '
                    'function is implemented or borrowed as a local vulnerability model**.')
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
    sidebar.caption('Historical 100-year riverine flood scenario · WorldPop 2020 · GHSL 2020')
    st.title('Patna | Flood exposure')
    st.caption('Historical 100-year riverine flood scenario · WRI Aqueduct V2 — WATCH T100 · Modeled screening')
    st.caption('Common-data footprint; not all of Patna district.')
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
        st.subheader('Flood Depth (m)')
        _, pop_weights, _ = weighted_cells(bundle, threshold)
        render_map(a['depth_m'], a['valid_depth'], a['common_valid'], report['target_grid']['transform'],
                   population=a['population_count'], weighted_population=pop_weights, threshold_m=threshold,
                   height=540 if section == 'Hazard' else 430)
        st.caption('Native modeled depths, including excluded exposure cells. Threshold affects summaries, not map values. '
                   'Switch layers for coverage or depth-weighted population exposure; diagonals mark incomplete exposure.')
        if section == 'Hazard':
            pilot_reference(threshold)
    elif section == 'Exposure':
        st.subheader('Exposure by depth')
        rows = depth_bands(bundle, threshold)
        st.caption(f'Non-overlapping bands, clipped to depth > {threshold:g} m. Values sum to the KPIs above.')
        band_charts(rows)
        with st.expander('Detailed depth-band values'):
            st.dataframe(pd.DataFrame(rows), hide_index=True, width='stretch')
        st.download_button('Download depth-band CSV', table_csv(rows), 'patna_common_depth_bands.csv', 'text/csv')
    elif section == 'Vulnerability':
        vulnerability_screening(bundle, threshold)
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
