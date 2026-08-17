"""
1_Pipe_Flow_Analyser.py
========================
Module A: Pipe Flow Analyser.

Lets the user select a fluid, define pipe geometry, and see velocity,
Reynolds number, friction factor, and pressure drop -- plus an interactive
plot of pressure drop vs flow rate, and CSV export.
"""

import io

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from engineering import Fluid, Pipe

st.set_page_config(page_title="Pipe Flow Analyser", page_icon="🔧", layout="wide")
st.title("🔧 Pipe Flow Analyser")
st.caption(
    "Darcy-Weisbach pipe flow calculator. Turbulent friction factor is "
    "solved from the implicit Colebrook-White equation using a "
    "Newton-Raphson root finder."
)

# ---------------------------------------------------------------------------
# Sidebar inputs
# ---------------------------------------------------------------------------
st.sidebar.header("Fluid Selection")

fluid_choice = st.sidebar.selectbox(
    "Fluid",
    options=list(Fluid.PRESETS.keys()) + ["Custom fluid..."],
    help="Choose a preset fluid, or define your own density/viscosity.",
)

try:
    if fluid_choice == "Custom fluid...":
        st.sidebar.markdown("**Custom fluid properties**")
        custom_name = st.sidebar.text_input("Fluid name", value="Custom Fluid")
        density = st.sidebar.number_input(
            "Density (kg/m^3)", min_value=0.001, value=850.0, step=1.0,
            help="Mass per unit volume of the fluid."
        )
        viscosity = st.sidebar.number_input(
            "Dynamic viscosity (Pa.s)", min_value=1e-6, value=0.005,
            step=0.001, format="%.6f",
            help="Resistance of the fluid to shear/flow."
        )
        fluid = Fluid(custom_name, density, viscosity)
    else:
        fluid = Fluid.from_preset(fluid_choice)
        st.sidebar.write(f"Density: **{fluid.density} kg/m³**")
        st.sidebar.write(f"Viscosity: **{fluid.viscosity:.2e} Pa·s**")
except ValueError as e:
    st.sidebar.error(f"Fluid input error: {e}")
    st.stop()

st.sidebar.header("Pipe Geometry")
diameter_mm = st.sidebar.number_input(
    "Internal diameter (mm)", min_value=1.0, value=100.0, step=1.0,
    help="Internal diameter of the pipe bore."
)
length_m = st.sidebar.number_input(
    "Pipe length (m)", min_value=0.1, value=100.0, step=1.0,
    help="Total straight-line length of the pipe run."
)
roughness_mm = st.sidebar.number_input(
    "Absolute roughness (mm)", min_value=0.0, value=0.045, step=0.001,
    format="%.4f",
    help="Internal surface roughness (e.g. ~0.045 mm for commercial steel, "
         "~0.0015 mm for drawn tubing, ~0.26 mm for rusted steel)."
)

st.sidebar.header("Flow Rate")
flow_rate_m3h = st.sidebar.number_input(
    "Flow rate (m^3/h)", min_value=0.01, value=36.0, step=1.0,
    help="Volumetric flow rate through the pipe."
)

# Convert to SI units used by engineering.py
diameter = diameter_mm / 1000.0
roughness = roughness_mm / 1000.0
flow_rate = flow_rate_m3h / 3600.0

# ---------------------------------------------------------------------------
# Calculation
# ---------------------------------------------------------------------------
try:
    pipe = Pipe(diameter=diameter, length=length_m, roughness=roughness, fluid=fluid)
    result = pipe.summary(flow_rate)
except ValueError as e:
    st.error(f"Input error: {e}")
    st.stop()
except RuntimeError as e:
    st.error(f"Calculation did not converge: {e}")
    st.stop()

# ---------------------------------------------------------------------------
# Metric displays
# ---------------------------------------------------------------------------
st.subheader("Results")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Velocity", f"{result['velocity_m_s']:.3f} m/s")
m2.metric("Reynolds Number", f"{result['reynolds_number']:,.0f}")
m3.metric("Friction Factor", f"{result['friction_factor']:.5f}")
m4.metric("Pressure Drop", f"{result['pressure_drop_kpa']:.3f} kPa")

st.info(f"Flow regime: **{result['flow_regime']}**")

# ---------------------------------------------------------------------------
# Interactive plot: pressure drop vs flow rate
# ---------------------------------------------------------------------------
st.subheader("Pressure Drop vs Flow Rate")

max_flow_m3h = st.slider(
    "Maximum flow rate to plot (m^3/h)",
    min_value=flow_rate_m3h,
    max_value=flow_rate_m3h * 5,
    value=flow_rate_m3h * 3,
    help="Sets the upper end of the flow-rate range shown in the plot below."
)

flow_range_m3h = np.linspace(0.05, max_flow_m3h, 100)
flow_range_m3s = flow_range_m3h / 3600.0

dp_values_kpa = []
for q in flow_range_m3s:
    try:
        dp_values_kpa.append(pipe.pressure_drop(q) / 1000.0)
    except (ValueError, RuntimeError):
        dp_values_kpa.append(np.nan)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=flow_range_m3h, y=dp_values_kpa,
    mode="lines", name="Pressure drop", line=dict(width=3),
))
fig.add_trace(go.Scatter(
    x=[flow_rate_m3h], y=[result["pressure_drop_kpa"]],
    mode="markers", name="Current operating point",
    marker=dict(size=12, symbol="star", color="red"),
))
fig.update_layout(
    xaxis_title="Flow rate (m^3/h)",
    yaxis_title="Pressure drop (kPa)",
    hovermode="x unified",
    height=450,
)
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------
st.subheader("Export Results")

export_df = pd.DataFrame({
    "flow_rate_m3_per_h": flow_range_m3h,
    "pressure_drop_kPa": dp_values_kpa,
})

csv_buffer = io.StringIO()
export_df.to_csv(csv_buffer, index=False)

st.download_button(
    label="Download pressure drop vs flow rate (CSV)",
    data=csv_buffer.getvalue(),
    file_name="pipe_flow_pressure_drop.csv",
    mime="text/csv",
)

with st.expander("View full results table"):
    st.dataframe(export_df, use_container_width=True)
