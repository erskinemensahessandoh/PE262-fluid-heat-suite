"""
2_Heat_Transfer_Calculator.py
==============================
Module B: Heat Transfer Calculator.

Two sub-tools:
1. Steady-state conduction through a flat wall (Fourier's Law).
2. Newton's Law of Cooling -- time to reach a target temperature, plus a
   live-updating cooling curve.
"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from engineering import ConductionWall, CoolingProcess

st.set_page_config(page_title="Heat Transfer Calculator", page_icon="🌡️", layout="wide")
st.title("🌡️ Heat Transfer Calculator")

tab1, tab2 = st.tabs(["Conduction Through a Wall", "Newton's Law of Cooling"])

# ---------------------------------------------------------------------------
# TAB 1: Steady-state conduction (Fourier's Law)
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("Steady-State Conduction (Fourier's Law)")
    st.write(
        "Calculates the rate of heat flow through a single flat layer of "
        "material once the temperature on each face has stabilised "
        "(steady state)."
    )

    c1, c2 = st.columns(2)
    with c1:
        k = st.number_input(
            "Thermal conductivity, k (W/m·K)", min_value=0.001, value=45.0,
            step=1.0,
            help="How well the material conducts heat. Higher = better "
                 "conductor. Steel ≈ 45, concrete ≈ 1.7, insulation ≈ 0.04."
        )
        area = st.number_input(
            "Cross-sectional area, A (m^2)", min_value=0.001, value=2.0,
            step=0.1,
            help="Area of the wall face through which heat is flowing, "
                 "measured perpendicular to the direction of heat flow."
        )
        thickness = st.number_input(
            "Wall thickness, L (m)", min_value=0.001, value=0.02, step=0.001,
            format="%.4f",
            help="Distance the heat travels through the material, from the "
                 "hot face to the cold face."
        )
    with c2:
        T_hot = st.number_input(
            "Hot face temperature (°C)", value=150.0, step=5.0,
            help="Temperature of the warmer side of the wall."
        )
        T_cold = st.number_input(
            "Cold face temperature (°C)", value=30.0, step=5.0,
            help="Temperature of the cooler side of the wall."
        )

    try:
        wall = ConductionWall(thermal_conductivity=k, area=area, thickness=thickness)
        Q = wall.heat_transfer_rate(T_hot, T_cold)
        flux = wall.heat_flux(T_hot, T_cold)

        r1, r2 = st.columns(2)
        r1.metric("Heat Transfer Rate, Q", f"{Q:,.2f} W")
        r2.metric("Heat Flux, q\"", f"{flux:,.2f} W/m²")

        if Q < 0:
            st.warning(
                "Heat transfer rate is negative: heat is flowing from the "
                "'cold' face to the 'hot' face because the cold-face "
                "temperature you entered is actually higher. Check your "
                "temperature inputs."
            )
    except ValueError as e:
        st.error(f"Input error: {e}")

# ---------------------------------------------------------------------------
# TAB 2: Newton's Law of Cooling
# ---------------------------------------------------------------------------
with tab2:
    st.subheader("Newton's Law of Cooling")
    st.write(
        "Models how a body's temperature decays exponentially toward the "
        "ambient temperature over time, driven by convective heat loss "
        "from its surface."
    )

    c1, c2 = st.columns(2)
    with c1:
        T0 = st.slider(
            "Initial body temperature, T0 (°C)", min_value=-50.0, max_value=300.0,
            value=90.0, step=1.0,
            help="Starting temperature of the body before cooling begins."
        )
        T_inf = st.slider(
            "Ambient temperature, T∞ (°C)", min_value=-50.0, max_value=100.0,
            value=20.0, step=1.0,
            help="Temperature of the surrounding fluid (air/water) far from "
                 "the body -- the temperature the body eventually settles to."
        )
        h = st.slider(
            "Convective heat transfer coefficient, h (W/m²·K)",
            min_value=1.0, max_value=500.0, value=15.0, step=1.0,
            help="How effectively the surrounding fluid carries heat away "
                 "from the surface. Still air ≈ 5-25, moving air ≈ 25-250, "
                 "water ≈ 500-10,000."
        )
    with c2:
        area_c = st.number_input(
            "Surface area, A (m^2)", min_value=0.0001, value=0.03, step=0.01,
            format="%.4f",
            help="Surface area of the body exposed to the ambient fluid."
        )
        mass = st.number_input(
            "Mass, m (kg)", min_value=0.001, value=0.4, step=0.1,
            help="Mass of the body being cooled."
        )
        cp = st.number_input(
            "Specific heat, cp (J/kg·K)", min_value=1.0, value=450.0, step=10.0,
            help="Energy required to raise 1 kg of the body's material by "
                 "1°C. Steel ≈ 450, water ≈ 4182, aluminum ≈ 900."
        )

    try:
        cooling = CoolingProcess(T0=T0, T_inf=T_inf, h=h, area=area_c,
                                  mass=mass, specific_heat=cp)

        st.metric("Thermal Time Constant, τ", f"{cooling.tau:,.1f} s "
                                                f"({cooling.tau/60:.2f} min)")

        lo, hi = sorted([T_inf, T0])
        default_target = lo + 0.5 * (hi - lo)
        T_target = st.slider(
            "Target temperature to cool/warm to (°C)",
            min_value=lo + 0.01 * (hi - lo),
            max_value=hi - 0.01 * (hi - lo),
            value=float(default_target),
            help="Must be strictly between the ambient and initial "
                 "temperatures -- the body can never overshoot ambient."
        )

        t_target = cooling.time_to_reach(T_target)
        st.success(
            f"Time to reach {T_target:.1f} °C: **{t_target:,.1f} s** "
            f"({t_target/60:.2f} min)"
        )

        # Live-updating cooling curve
        t_max = st.slider(
            "Plot time range (s)", min_value=int(t_target * 1.2) + 10,
            max_value=int(cooling.tau * 8) + 10,
            value=int(cooling.tau * 5) + 10,
            help="How far in time the cooling curve below is plotted."
        )

        times, temps = cooling.generate_curve(t_max)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=times, y=temps, mode="lines", name="Body temperature",
            line=dict(width=3, color="firebrick"),
        ))
        fig.add_hline(y=T_inf, line_dash="dash", line_color="gray",
                       annotation_text="Ambient T∞")
        fig.add_trace(go.Scatter(
            x=[t_target], y=[T_target], mode="markers",
            name=f"Target reached at t={t_target:.0f}s",
            marker=dict(size=12, symbol="star", color="blue"),
        ))
        fig.update_layout(
            xaxis_title="Time (s)",
            yaxis_title="Temperature (°C)",
            hovermode="x unified",
            height=450,
        )
        st.plotly_chart(fig, use_container_width=True)

    except ValueError as e:
        st.error(f"Input error: {e}")
