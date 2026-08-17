"""
app.py
======
Home page for the Fluid Flow & Heat Transfer Engineering Suite.
PE 262 Capstone Project.
"""

import streamlit as st

st.set_page_config(
    page_title="Fluid Flow & Heat Transfer Suite",
    page_icon="🛢️",
    layout="wide",
)

st.title("🛢️ Fluid Flow & Heat Transfer Engineering Suite")

st.markdown(
    """
    Welcome! This application is a multi-page engineering toolkit built for
    **PE 262 — Computer Programming for Petroleum Engineers** (Capstone
    Project), integrating fluid mechanics, heat transfer, data analysis,
    object-oriented programming, and numerical methods developed across
    the course.

    Use the sidebar to navigate between modules.
    """
)

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🔧 Pipe Flow Analyser")
    st.write(
        "Calculate velocity, Reynolds number, friction factor, and "
        "pressure drop for flow through a pipe. Compare water, air, "
        "crude oil, or a custom fluid, and visualize how pressure drop "
        "scales with flow rate."
    )

with col2:
    st.subheader("🌡️ Heat Transfer Calculator")
    st.write(
        "Compute steady-state conduction through a flat wall (Fourier's "
        "Law) and simulate transient cooling of a body in an ambient "
        "fluid (Newton's Law of Cooling), with a live cooling curve."
    )

with col3:
    st.subheader("📊 Rock & Fluid Data Dashboard")
    st.write(
        "Upload your own rock or fluid property data (CSV), explore "
        "summary statistics, filter samples, and visualize relationships "
        "like the classic porosity-permeability crossplot."
    )

st.markdown("---")

with st.expander("About this project / engineering.py"):
    st.markdown(
        """
        All engineering calculations are implemented in an object-oriented
        backend module, `engineering.py`, containing the following classes:

        - **`Fluid`** — represents a working fluid (water, air, crude oil,
          or custom) with the density, viscosity, thermal conductivity,
          and specific heat needed by the other classes.
        - **`Pipe`** — represents a circular pipe carrying a `Fluid`;
          computes velocity, Reynolds number, Darcy friction factor
          (solved via a hand-written **Newton-Raphson** solver for the
          implicit Colebrook-White equation in turbulent flow), and
          pressure drop via the Darcy-Weisbach equation.
        - **`ConductionWall`** — steady-state 1-D conduction through a
          single flat layer, via Fourier's Law.
        - **`CoolingProcess`** — transient lumped-capacitance cooling of a
          body, via Newton's Law of Cooling.

        All calculations were verified against independent hand
        calculations — see `verify_calculations.py` in the repository.
        """
    )
