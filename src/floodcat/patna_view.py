"""Opt-in real common-footprint screening, without runtime remapping."""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from . import patna
from .exports import table_csv


def render(sidebar=st.sidebar):
    st.title('FloodCAT | REAL — Patna exposure')
    st.caption('Historical WRI Aqueduct V2 · WATCH T100 · WorldPop 2020 · GHSL 2020')
    st.info(patna.DOMAIN)
    try:
        bundle = patna.load_bundle()
    except patna.BundleError as error:
        st.warning(f'{error}. Restore the verified processed bundle and checksum manifest. '
                   'Synthetic demo and REAL — WRI remain available from Data mode.')
        return
    arrays, report, audit, area = bundle
    threshold = sidebar.slider('Flood-depth threshold (m)', 0.0, 8.0, 0.0, 0.25,
                                  help='Only common-valid cells with modeled depth strictly greater than this value contribute to exposure.')
    summary = patna.summarize(bundle, threshold)
    st.warning('Modeled physical exposure screening only. These estimates are not observed flood impacts, '
               'measured damage or monetary losses. Missing coverage can bias regional interpretation.')
    a, b, c, d = st.columns(4)
    a.metric('Estimated exposed population', f"{summary['Estimated exposed population (people)']:,.0f}")
    b.metric('Exposed built-up surface (km²)', f"{summary['Exposed built-up surface (m²)']/1e6:,.3f}")
    c.metric('Common flooded area (km²)', f"{summary['Common flooded area (km²)']:,.2f}")
    d.metric('Common flooded cells', f"{summary['Common flooded cells']:,}")
    st.markdown(f"**Joint coverage: {summary['Joint coverage (% of valid hazard cells)']:.2f}% of valid uploaded hazard cells** "
                f"({summary['Common cells']:,} / {summary['Valid uploaded hazard cells']:,}; "
                f"{summary['Common domain area (km²)']:,.2f} km²). This is a cell-count coverage percentage.")
    excluded = summary['Excluded flooded cells (incomplete joint coverage)']
    st.warning(f"Excluded flooded cells: {excluded:,} of {summary['Uploaded hazard flooded cells']:,} "
               f"uploaded hazard cells above {threshold:g} m have incomplete joint exposure coverage. "
               'Their exposure is unknown and is not included or redistributed.')
    dx, _, west, _, dy, north = report['target_grid']['transform']
    rows, cols = arrays['depth_m'].shape
    x = west + dx * (np.arange(cols) + .5)
    y = north + dy * (np.arange(rows) + .5)
    depth = np.where(arrays['valid_depth'], arrays['depth_m'], np.nan)
    figure = go.Figure(go.Heatmap(x=x, y=y, z=depth, colorscale='Blues', zmin=0,
        colorbar=dict(title='Depth (m)'), hoverongaps=False,
        hovertemplate='Lon %{x:.4f}° E<br>Lat %{y:.4f}° N<br>Depth %{z:.2f} m<extra></extra>'))
    figure.update_layout(title='Historical WRI T100 modeled depth — full uploaded rectangle',
        xaxis_title='Longitude (°E)', yaxis_title='Latitude (°N)', height=450)
    st.plotly_chart(figure, width='stretch')
    st.caption('The map shows all valid modeled depths, including cells excluded from exposure. '
               'The threshold changes summaries, not the depth map; valid dry zero is retained. '
               'Longitude/latitude grid display, not a district boundary map.')
    coverage = go.Figure(go.Heatmap(x=x, y=y, z=arrays['common_valid'].astype(int),
        zmin=0, zmax=1, colorscale=[[0, '#d1d5db'], [.499, '#d1d5db'], [.5, '#168078'], [1, '#168078']],
        colorbar=dict(title='Joint coverage', tickvals=[0, 1], ticktext=['Excluded', 'Complete']),
        hovertemplate='Lon %{x:.4f}<br>Lat %{y:.4f}<br>Complete joint cell: %{z}<extra></extra>'))
    coverage.update_layout(title='Exposure analysis footprint — complete joint cells only', height=300,
                           xaxis_title='Longitude (°E)', yaxis_title='Latitude (°N)')
    st.plotly_chart(coverage, width='stretch')
    with st.expander('Sources, methodology and uncertainty'):
        st.markdown('**WRI Aqueduct Floods Hazard Maps V2:** historical WATCH 100-year return-period '
                    'modeled riverine depth (m); not an observed event. Flood protection is not represented '
                    'and the model omits backwater effects.\n\n'
                    '**WorldPop / University of Southampton:** legacy India 2020 population counts '
                    '(`WorldPop/GP/100m/pop/IND_2020`), CC BY 4.0; not R2025A.\n\n'
                    '**European Commission JRC, Pesaresi and Politis (2023):** GHS-BUILT-S R2023A, '
                    '`JRC/GHSL/P2023A/GHS_BUILT_S/2020`, total `built_surface` m²/cell; '
                    'reuse with source acknowledgement. DOI: 10.2905/9F06F36F-4B11-47EC-ABB0-4F8B7B1D72EA.\n\n'
                    '**Method:** preprocessed conservative physical-area intersections, population on '
                    'the shared CRS and GHSL from actual World Mollweide to WRI WGS84. Source-pixel '
                    'exposure is assumed spatially uniform. Whole WRI-cell exposure counts only at '
                    'depth strictly above the selected threshold. Area uses the WGS84 ellipsoid. '
                    'The application sums the verified arrays; it performs no resampling. Valid zero '
                    'is preserved; missing, partial or uncertain cells are excluded, never filled.\n\n'
                    '**Limitations:** the export is a district-buffered bounding rectangle; no district '
                    'polygon is bundled. Export task IDs/times and upstream GHSL NaN cause remain '
                    'unverified. Source identity includes a user-supplied export recipe and exact pilot '
                    'overlap checks. Geometric refinement was sampled, not a global error bound. '
                    'No vulnerability, damage or financial model is used.')
        st.json({'audit': audit['status'], 'known_source_budgets': report['budgets'],
                 'provenance': report['provenance'], 'limitations': report['limitations']})
    st.download_button('Download current exposure CSV', table_csv([summary]),
                       'patna_common_exposure.csv', 'text/csv')
    st.download_button('Download threshold comparison CSV',
                       table_csv([patna.summarize(bundle, t) for t in (0., 1., 2., 5.)]),
                       'patna_common_thresholds.csv', 'text/csv')
    st.caption('CSV values retain numerical precision; displayed estimates are rounded. '
               'Checksums and the passing M2C-1 audit were verified for this render.')
