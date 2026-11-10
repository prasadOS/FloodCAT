"""FloodCAT standalone Streamlit demo. Launch: python -m streamlit run app.py"""
import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from src.floodcat.demo import make_demo_data, SCENARIOS, SCENARIO_NAMES, summarize, severity
from src.floodcat.exports import table_csv, metadata_json

st.set_page_config(page_title="FloodCAT | Physical Flood Exposure", page_icon="🌊", layout="wide")

mode = st.sidebar.radio("Data mode", ["Synthetic Demo", "REAL — Patna"])
controls = st.sidebar.empty()
if mode == "REAL — Patna":
    from src.floodcat.patna_view import render

    render(sidebar=controls.container())
    st.stop()

@st.cache_data(show_spinner=False)
def cached_data():
    return make_demo_data()

data = cached_data()
st.title("FloodCAT")
st.caption("Flood hazard and physical exposure screening | Portable interview demonstration")
st.caption("SYNTHETIC DEMO · Hypothetical hazard and exposure · Not actual flood impacts")

with controls.container():
    st.header("Controls")
    section = st.radio("Module", ["Overview", "Hazard", "Exposure", "Depth severity", "Compare", "Data & methods"])
    scenario = st.selectbox("Hazard scenario (illustrative labels)", SCENARIO_NAMES, index=1)
    threshold = st.slider("Flood-depth threshold (m)", 0.0, 5.0, 0.0, 0.25,
                          help="Cells with depth strictly greater than the threshold are counted.")
    st.caption("Pilot-style grid near Patna, India. Geographic coordinates are approximate and the modeled patterns are invented.")

summary = summarize(data, scenario, threshold)

def fmt_i(n): return f"{n:,.0f}"

def metrics(s):
    a,b,c,d=st.columns(4)
    a.metric("Flooded area (km²)",f"{s['Inundated area (km²)']:,.1f}")
    b.metric("Exposed people (synthetic)",fmt_i(s['Exposed people (synthetic)']))
    c.metric("Built-up area exposed (km²)",f"{s['Exposed built-up (km²)']:,.1f}")
    d.metric("Maximum depth (m)",f"{s['Max depth (m)']:.2f}")

def heatmap(values, title, ztitle, colorscale='Blues'):
    fig=go.Figure(go.Heatmap(x=data.lon, y=data.lat, z=values, colorscale=colorscale,
                             colorbar=dict(title=ztitle), hovertemplate="Lon %{x:.3f}<br>Lat %{y:.3f}<br>Value %{z:.2f}<extra></extra>"))
    fig.update_layout(title=title, xaxis_title="Longitude (°E)", yaxis_title="Latitude (°N)",
                      height=480, margin=dict(l=30,r=25,t=55,b=30), yaxis=dict(scaleanchor='x',scaleratio=1))
    st.plotly_chart(fig, width='stretch')

if section == "Overview":
    st.subheader("Scenario snapshot")
    metrics(summary)
    st.info("Select a scenario and threshold in the sidebar. Figures are computed from synthetic 42 × 48 cell grids; these are not actual flood impact estimates.")
    l,r=st.columns([1.45,1])
    with l: heatmap(data.depths[scenario],"Illustrative flood-depth surface", "m", "Blues")
    with r:
        st.markdown("#### Prototype workflow")
        st.markdown("**Hazard:** depth raster → **Overlay:** population and built-up grids → **Metrics:** affected cells and areas → **Comparison:** supported scenarios → **Exports:** reproducible tables.")
        st.markdown("**Scientific caution:** riverine hazard estimates are not observations; exposure is not damage. This prototype does not estimate insurance or monetary losses.")
elif section == "Hazard":
    st.subheader("Flood-depth hazard")
    metrics(summary)
    heatmap(data.depths[scenario],"Depth grid — synthetic (metres)", "m", "Blues")
    st.caption("Grid size 42×48; approximate 1-km cell spacing. Display uses latitude/longitude axes, not a georeferenced GeoTIFF or validated base map.")
elif section == "Exposure":
    st.subheader("Physical exposure overlay")
    metrics(summary)
    metric = st.radio("Show", ["Population (per cell)", "Built-up area (km²/cell)"], horizontal=True)
    import numpy as np
    wet = data.depths[scenario] > threshold
    vals = np.where(wet, data.people if metric.startswith("Population") else data.builtup_km2, 0)
    heatmap(vals, f"{metric} in inundated cells (synthetic)", "people" if metric.startswith("Population") else "km²", "YlOrRd")
    st.caption("Synthetic exposure assigned to the same grid as synthetic depth. No WorldPop/GHSL raster intersection or population interpolation is performed.")
elif section == "Depth severity":
    st.subheader("Exposure by depth band")
    rows = severity(data,scenario,threshold)
    df=pd.DataFrame(rows)
    l,r=st.columns(2)
    with l: st.plotly_chart(px.bar(df,x='Depth band',y='Area (km²)',title='Area by depth band'),width='stretch')
    with r: st.plotly_chart(px.bar(df,x='Depth band',y='People (synthetic)',title='People by depth band'),width='stretch')
    st.dataframe(df,width='stretch',hide_index=True)
    st.download_button("Download severity CSV",table_csv(rows),file_name='floodcat_demo_severity.csv',mime='text/csv')
elif section == "Compare":
    st.subheader("Scenario comparison")
    rows=[summarize(data,s,threshold) for s in SCENARIO_NAMES]
    df=pd.DataFrame(rows)
    st.dataframe(df,width='stretch',hide_index=True)
    c1,c2=st.columns(2)
    with c1: st.plotly_chart(px.bar(df,x='Scenario',y='Inundated area (km²)',title='Flooded area'),width='stretch')
    with c2: st.plotly_chart(px.bar(df,x='Scenario',y='Exposed people (synthetic)',title='Exposed population'),width='stretch')
    st.caption("RCP labels are illustrative scenario names, not actual downscaled or WRI-calculated future climate projections. Do not interpret these differences as predicted change.")
    st.download_button("Download comparison CSV",table_csv(rows),file_name='floodcat_demo_comparison.csv',mime='text/csv')
else:
    st.subheader("Data, methods and limitations")
    st.markdown("""**Data classification:** synthetic, deterministic, hypothetical. This portable starter does not include the original computer's Aqueduct GeoTIFFs, Earth Engine acquisition logs, WorldPop, GHSL, or CLIMADA integration.

**Hazard:** stylized smooth depth field over a river-like corridor. Historical T25/T100/T500 depths are monotonically increasing by construction; future labels describe hypothetical examples, not climate projections.

**Exposure:** population counts and built-up surface are generated from smooth artificial settlement functions, both on the same grid as depth. A cell counts as inundated only when its depth is **strictly greater** than the selected threshold.

**Area:** cell area is estimated from spherical Earth latitude/longitude edge geometry; the calculation is analytical rather than a flat 1 km²-per-cell assumption.

**Limitations:** no river hydraulics, terrain, observed validation, calibrated depth fields, actual population, exposure uncertainty, physical vulnerability or financial loss model. This is not a production risk assessment.

**Planned real inputs:** WRI Aqueduct future riverine flood-depth maps (RCP/CMIP5-era), WorldPop population and GHSL built-up layers, with recorded source metadata, licenses, grids, and conservation tests. CMIP6/SSP requires separately verified true future depth rasters.
""")
    st.code("python -m streamlit run app.py", language="bat")
    st.caption("Review README.md and docs/PROJECT_STATUS.md for reconstruction steps.")

st.divider()
st.markdown("#### Export current results")
row = [summary]
c1,c2 = st.columns(2)
with c1:
    st.download_button("Summary CSV",table_csv(row),file_name="floodcat_demo_summary.csv",mime="text/csv")
with c2:
    st.download_button("Methods JSON",metadata_json(scenario,threshold),file_name="floodcat_demo_metadata.json",mime="application/json")
st.caption("FloodCAT portable starter v0.1 | Explicitly synthetic demonstration | No external credentials needed")
