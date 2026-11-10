"""Streamlit view for the independently validated local WRI pilot."""

import zlib

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from . import wri
from .exports import table_csv


def render():
    st.title("FloodCAT | REAL — WRI")
    st.subheader("Patna historical riverine hazard · WATCH T100")
    st.caption("WRI Aqueduct V2 modeled depth in metres for a 100-year return period. "
               "Use for regional screening. The model omits backwater effects and "
               "the hazard layer does not account for flood protection.")
    try:
        depth, nodata, manifest, tiff, metadata = wri.load_pilot()
    except FileNotFoundError:
        st.warning("The local WRI GeoTIFF or source manifest is missing. Select Synthetic demo to explore the demonstration.")
        return
    except (OSError, ValueError, KeyError, TypeError, zlib.error) as error:
        st.error(f"The local WRI assets failed validation. {error}")
        return

    threshold = st.sidebar.slider("Flood-depth threshold (m)", 0.0, 6.0, 0.0, 0.25,
                                  help="Flooded area counts valid cells with depth strictly above this threshold.")
    summary = wri.summarize(depth, nodata, threshold)
    area, cells, maximum = st.columns(3)
    area.metric("Flooded area (km²)", f"{summary['Flooded area (km²)']:,.2f}")
    cells.metric("Flooded cells", f"{summary['Flooded cells']:,}")
    maximum.metric("Maximum valid depth (m)", f"{summary['Maximum valid depth (m)']:.2f}")
    dx, _, west, _, dy, north = wri.TRANSFORM
    rows, cols = depth.shape
    displayed = np.where(np.isfinite(depth) & (depth != nodata), depth, np.nan)
    figure = go.Figure(go.Heatmap(
        x=west + dx * (np.arange(cols) + 0.5),
        y=north + dy * (np.arange(rows) + 0.5),
        z=displayed, colorscale="Blues", zmin=0, colorbar=dict(title="Depth (m)"),
        hoverongaps=False,
        hovertemplate="Lon %{x:.4f}° E<br>Lat %{y:.4f}° N<br>Depth %{z:.2f} m<extra></extra>",
    ))
    figure.update_layout(
        title="Modeled flood depth · WRI Aqueduct V2",
        xaxis_title="Longitude (°E)", yaxis_title="Latitude (°N)",
        yaxis=dict(scaleanchor="x", scaleratio=1), height=500,
        plot_bgcolor="#d1d5db",
    )
    st.plotly_chart(figure, use_container_width=True)
    st.caption(
        f"{summary['Valid dry cells']:,} valid dry cells at 0 m. "
        f"{summary['Nodata cells']:,} nodata cells, shown in gray where present. "
        "The map shows all valid depths. The threshold applies to area and flooded-cell count. "
        "Area uses whole native cells on the WGS84 ellipsoid."
    )
    with st.expander("Source and acquisition metadata"):
        st.markdown(f"{manifest['attribution']}. [Catalog and terms]({wri.SOURCE})")
        st.json(manifest)
    a, b, c = st.columns(3)
    a.download_button("Download GeoTIFF", tiff, wri.TIFF, "image/tiff")
    b.download_button("Download source manifest", metadata, wri.MANIFEST, "application/json")
    c.download_button("Download summary CSV", table_csv([{"Asset": manifest["asset_id"], **summary}]),
                      "patna_wri_watch_t100_summary.csv", "text/csv")
