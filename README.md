# Fluid Flow & Heat Transfer Engineering Suite

**PE 262 — Computer Programming for Petroleum Engineers, Capstone Project**
KNUST, Department of Petroleum Engineering

**Live app:** _[add your Streamlit Community Cloud URL here after deployment]_

## Overview

A multi-page Streamlit web application integrating fluid mechanics, heat
transfer, data analysis, object-oriented programming, and numerical methods
covered across PE 262. Built as a portfolio-quality engineering tool.

## Modules

### Module A — Pipe Flow Analyser
Calculates velocity, Reynolds number, Darcy friction factor, and pressure
drop for flow through a circular pipe using the Darcy-Weisbach equation.
Supports water, air, crude oil (built-in presets), or a fully custom fluid.
The turbulent friction factor is solved from the **implicit Colebrook-White
equation using a hand-written Newton-Raphson root finder** (consistent with
the solver built in Project 7), rather than an explicit approximation
alone. Includes an interactive pressure-drop-vs-flow-rate plot and CSV
export.

### Module B — Heat Transfer Calculator
- **Steady-state conduction** through a single flat layer via Fourier's Law.
- **Newton's Law of Cooling** — computes the time required for a body to
  cool (or warm) from an initial temperature to a target temperature in a
  given ambient environment, with a live-updating cooling curve driven by
  slider inputs.

### Module C — Rock & Fluid Data Dashboard
Upload a CSV of rock or fluid property data (e.g. core analysis results),
view summary statistics, filter samples by a numeric threshold, and
visualize a histogram and a configurable crossplot (defaults to the
classic porosity-permeability relationship, with optional log scale and
categorical coloring). Filtered data can be downloaded as CSV. A synthetic
sample dataset (`sample_data/sample_core_data.csv`) is included for testing.

## Architecture

```
capstone-fluid-heat-suite/
├── app.py                          # Home page
├── pages/
│   ├── 1_Pipe_Flow_Analyser.py
│   ├── 2_Heat_Transfer_Calculator.py
│   └── 3_Rock_Fluid_Dashboard.py
├── engineering.py                  # OOP backend (Fluid, Pipe, ConductionWall, CoolingProcess)
├── verify_calculations.py          # Hand-calculation verification script
├── sample_data/
│   └── sample_core_data.csv
├── requirements.txt
└── README.md
```

All engineering logic lives in `engineering.py` and is imported by the
Streamlit pages — the pages themselves only handle UI and I/O. Classes:

- **`Fluid`** — fluid properties (density, viscosity, thermal conductivity,
  specific heat), with built-in presets and custom fluid support.
- **`Pipe`** — takes a `Fluid` and pipe geometry; computes velocity,
  Reynolds number, friction factor, and pressure drop.
- **`ConductionWall`** — steady-state 1-D Fourier conduction.
- **`CoolingProcess`** — lumped-capacitance Newton cooling, with analytical
  time-to-target and curve generation for plotting.
- A standalone **`newton_raphson()`** function implements the generic
  Newton-Raphson solver used by `Pipe.friction_factor()`.

## Verification

Both Module A and Module B calculations were checked against independent
hand calculations. Run:

```bash
python3 verify_calculations.py
```

Summary of results (full output in the script):

| Check | Hand calc | Code result | Difference |
|---|---|---|---|
| Pipe velocity (water, D=0.1m, Q=0.01 m³/s) | 1.2732 m/s | 1.2732 m/s | 0.00% |
| Reynolds number | 126,816 | 126,816 | 0.00% |
| Friction factor (turbulent) | 0.019599 (Swamee-Jain) | 0.019511 (Colebrook/Newton-Raphson) | 0.44% (expected — Colebrook is the more exact implicit solution) |
| Friction factor (laminar, 64/Re) | 0.100934 | 0.100934 | exact match |
| Conduction heat rate (Fourier's Law) | 540,000 W | 540,000 W | exact match |
| Cooling time constant τ | 400.0 s | 400.0 s | exact match |
| Time to reach target temperature | 501.11 s | 501.11 s | exact match |

## Running Locally

```bash
git clone <your-repo-url>
cd capstone-fluid-heat-suite
pip install -r requirements.txt
streamlit run app.py
```

## Deployment

Deployed on **Streamlit Community Cloud**, connected to this GitHub
repository, with `app.py` as the main file.

## AI Usage Documentation

This project was built with AI assistance (Claude). Every function was
reviewed, tested against hand calculations or analytical solutions, and
understood before being included. Representative examples:

1. **Prompt:** "Implement the turbulent Darcy friction factor by solving
   the implicit Colebrook-White equation with a Newton-Raphson root
   finder, using Swamee-Jain as the initial guess."
   **Verified:** Ran `verify_calculations.py` comparing the Newton-Raphson
   Colebrook result against an independent Swamee-Jain hand calculation —
   agreed to within 0.44%, which is the expected gap between the exact
   implicit solution and the explicit approximation.
   **Corrected:** The first version used an analytically differentiated
   form of the Colebrook residual for the Newton-Raphson derivative step,
   which was fragile near the initial guess; switched to a simple
   central-difference numerical derivative for robustness.

2. **Prompt:** "Add a `time_to_reach` method to `CoolingProcess` that
   solves Newton's Law of Cooling analytically for the time to reach a
   target temperature."
   **Verified:** Cross-checked `time_to_reach()` against a manual
   calculation of τ = mc/(hA) and t = −τ·ln((T−T∞)/(T0−T∞)) for a test
   case (steel sphere, 90°C → 40°C in 20°C air) — matched exactly.
   **Corrected:** Original version didn't validate that `T_target` lies
   strictly between `T0` and `T_inf`; added a `ValueError` check, since a
   body asymptotically approaches ambient and can never reach a target
   temperature outside that range (avoids a silent `math domain error`
   from `log()` of a negative or >1 ratio).

3. **Prompt:** "Build the Rock & Fluid Data Dashboard page with file
   upload, summary statistics, a numeric filter, a histogram, and a
   porosity-permeability crossplot with optional log scale."
   **Verified:** Tested with the synthetic `sample_core_data.csv` dataset
   and confirmed the filter slider correctly reduces the row count, and
   that the crossplot auto-selects porosity/permeability columns when
   present.
   **Corrected:** Initial version crashed with a `KeyError` if the
   uploaded CSV had no numeric columns at all; added an explicit check
   that stops with a clear `st.warning()` message instead of an
   unhandled exception.

_(Update this section with your own prompt wording and specifics if you
iterate further — grading requires this to reflect your actual process.)_
