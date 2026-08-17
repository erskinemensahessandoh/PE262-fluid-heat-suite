"""
engineering.py
================
Core object-oriented engineering classes for the Fluid Flow & Heat Transfer
Engineering Suite (PE 262 Capstone Project).

Classes
-------
Fluid           : Represents a working fluid with the physical properties
                  needed for flow and heat transfer calculations.
Pipe            : Represents a circular pipe carrying a Fluid and computes
                  velocity, Reynolds number, friction factor, and pressure drop.
ConductionWall  : Steady-state 1-D conduction through a single flat layer
                  (Fourier's Law).
CoolingProcess  : Lumped-capacitance transient cooling (Newton's Law of
                  Cooling).

All numerical root-finding (turbulent friction factor) is done with a
hand-written Newton-Raphson solver, consistent with the solver built in
Project 7 of this course.
"""

import math


# ---------------------------------------------------------------------------
# Generic Newton-Raphson root finder (reused from Project 7 methodology)
# ---------------------------------------------------------------------------
def newton_raphson(f, df, x0, tol=1e-8, max_iter=100):
    """
    Solve f(x) = 0 using the Newton-Raphson method.

    Parameters
    ----------
    f : callable
        Function whose root is sought, f(x).
    df : callable
        Derivative of f with respect to x, f'(x).
    x0 : float
        Initial guess.
    tol : float, optional
        Convergence tolerance on |f(x)|. Default 1e-8.
    max_iter : int, optional
        Maximum number of iterations before giving up. Default 100.

    Returns
    -------
    float
        The estimated root.

    Raises
    ------
    RuntimeError
        If the method fails to converge within max_iter iterations or the
        derivative becomes numerically zero.
    """
    x = x0
    for _ in range(max_iter):
        fx = f(x)
        if abs(fx) < tol:
            return x
        dfx = df(x)
        if abs(dfx) < 1e-14:
            raise RuntimeError("Newton-Raphson failed: derivative near zero.")
        x = x - fx / dfx
    raise RuntimeError(f"Newton-Raphson did not converge after {max_iter} iterations.")


# ---------------------------------------------------------------------------
# Fluid
# ---------------------------------------------------------------------------
class Fluid:
    """
    Represents a fluid and its physical properties for flow and heat
    transfer calculations.

    Attributes
    ----------
    name : str
        Descriptive name of the fluid.
    density : float
        Fluid density, kg/m^3.
    viscosity : float
        Dynamic viscosity, Pa.s (kg/m.s).
    thermal_conductivity : float or None
        Thermal conductivity, W/m.K (used by heat transfer module).
    specific_heat : float or None
        Specific heat capacity, J/kg.K (used by cooling module).
    """

    #: Built-in reference fluids at approximately room temperature / 1 atm.
    PRESETS = {
        "Water (20 degC)": {
            "density": 998.0,
            "viscosity": 1.002e-3,
            "thermal_conductivity": 0.598,
            "specific_heat": 4182.0,
        },
        "Air (20 degC, 1 atm)": {
            "density": 1.204,
            "viscosity": 1.825e-5,
            "thermal_conductivity": 0.0257,
            "specific_heat": 1005.0,
        },
        "Crude Oil (medium, 20 degC)": {
            "density": 870.0,
            "viscosity": 1.0e-2,
            "thermal_conductivity": 0.14,
            "specific_heat": 2000.0,
        },
    }

    def __init__(self, name, density, viscosity,
                 thermal_conductivity=None, specific_heat=None):
        """
        Create a Fluid object.

        Parameters
        ----------
        name : str
            Descriptive name of the fluid.
        density : float
            Density in kg/m^3. Must be positive.
        viscosity : float
            Dynamic viscosity in Pa.s. Must be positive.
        thermal_conductivity : float, optional
            Thermal conductivity in W/m.K.
        specific_heat : float, optional
            Specific heat capacity in J/kg.K.

        Raises
        ------
        ValueError
            If density or viscosity is not a positive number.
        """
        if density is None or density <= 0:
            raise ValueError("Fluid density must be a positive number (kg/m^3).")
        if viscosity is None or viscosity <= 0:
            raise ValueError("Fluid viscosity must be a positive number (Pa.s).")

        self.name = name
        self.density = float(density)
        self.viscosity = float(viscosity)
        self.thermal_conductivity = thermal_conductivity
        self.specific_heat = specific_heat

    @classmethod
    def from_preset(cls, preset_name):
        """
        Build a Fluid from one of the built-in PRESETS.

        Parameters
        ----------
        preset_name : str
            Key into Fluid.PRESETS (e.g. "Water (20 degC)").

        Returns
        -------
        Fluid

        Raises
        ------
        KeyError
            If preset_name is not a recognised preset.
        """
        if preset_name not in cls.PRESETS:
            raise KeyError(f"Unknown fluid preset: {preset_name}")
        props = cls.PRESETS[preset_name]
        return cls(preset_name, **props)

    def __repr__(self):
        return f"Fluid(name={self.name!r}, density={self.density}, viscosity={self.viscosity})"


# ---------------------------------------------------------------------------
# Pipe
# ---------------------------------------------------------------------------
class Pipe:
    """
    Represents a straight circular pipe carrying a Fluid, and computes
    flow characteristics using the Darcy-Weisbach framework.

    Attributes
    ----------
    diameter : float
        Internal pipe diameter, m.
    length : float
        Pipe length, m.
    roughness : float
        Absolute internal roughness, m.
    fluid : Fluid
        The Fluid object flowing through the pipe.
    """

    def __init__(self, diameter, length, roughness, fluid):
        """
        Parameters
        ----------
        diameter : float
            Internal diameter in m. Must be positive.
        length : float
            Pipe length in m. Must be positive.
        roughness : float
            Absolute roughness in m. Must be >= 0.
        fluid : Fluid
            Fluid object for the flowing medium.

        Raises
        ------
        ValueError
            If diameter/length are not positive, roughness is negative,
            or fluid is not a Fluid instance.
        """
        if diameter is None or diameter <= 0:
            raise ValueError("Pipe diameter must be a positive number (m).")
        if length is None or length <= 0:
            raise ValueError("Pipe length must be a positive number (m).")
        if roughness is None or roughness < 0:
            raise ValueError("Pipe roughness must be zero or a positive number (m).")
        if not isinstance(fluid, Fluid):
            raise ValueError("fluid must be a Fluid instance.")

        self.diameter = float(diameter)
        self.length = float(length)
        self.roughness = float(roughness)
        self.fluid = fluid

    def area(self):
        """Cross-sectional flow area, m^2."""
        return math.pi / 4.0 * self.diameter ** 2

    def velocity(self, flow_rate):
        """
        Mean flow velocity for a given volumetric flow rate.

        Parameters
        ----------
        flow_rate : float
            Volumetric flow rate, m^3/s. Must be positive.

        Returns
        -------
        float
            Mean velocity, m/s.
        """
        if flow_rate is None or flow_rate <= 0:
            raise ValueError("Flow rate must be a positive number (m^3/s).")
        return flow_rate / self.area()

    def reynolds_number(self, flow_rate):
        """
        Reynolds number for the given flow rate.

        Re = rho * v * D / mu

        Parameters
        ----------
        flow_rate : float
            Volumetric flow rate, m^3/s.

        Returns
        -------
        float
            Dimensionless Reynolds number.
        """
        v = self.velocity(flow_rate)
        return self.fluid.density * v * self.diameter / self.fluid.viscosity

    def friction_factor(self, flow_rate):
        """
        Darcy friction factor for the given flow rate.

        Laminar flow (Re < 2300):  f = 64 / Re
        Turbulent flow (Re >= 2300): solves the implicit Colebrook-White
        equation via Newton-Raphson, using the explicit Swamee-Jain
        correlation as the initial guess:

            1/sqrt(f) = -2*log10( (eps/D)/3.7 + 2.51/(Re*sqrt(f)) )

        Parameters
        ----------
        flow_rate : float
            Volumetric flow rate, m^3/s.

        Returns
        -------
        float
            Dimensionless Darcy friction factor.
        """
        Re = self.reynolds_number(flow_rate)
        rel_roughness = self.roughness / self.diameter

        if Re < 2300:
            # Laminar flow: exact analytical solution
            return 64.0 / Re

        # Turbulent flow: solve Colebrook-White implicitly for f
        # Work in terms of x = 1/sqrt(f) to keep the function well-behaved.
        def colebrook_residual(x):
            # x = 1/sqrt(f)
            return x + 2.0 * math.log10(rel_roughness / 3.7 + 2.51 * x / Re)

        def colebrook_derivative(x):
            # Numerical derivative is simplest and robust here
            h = 1e-6
            return (colebrook_residual(x + h) - colebrook_residual(x - h)) / (2 * h)

        # Swamee-Jain explicit correlation for the initial guess
        f_guess = 0.25 / (math.log10(rel_roughness / 3.7 + 5.74 / Re ** 0.9)) ** 2
        x0 = 1.0 / math.sqrt(f_guess)

        x_root = newton_raphson(colebrook_residual, colebrook_derivative, x0)
        f = 1.0 / x_root ** 2
        return f

    def pressure_drop(self, flow_rate):
        """
        Frictional pressure drop over the pipe length via the
        Darcy-Weisbach equation:

            dP = f * (L/D) * (rho * v^2 / 2)

        Parameters
        ----------
        flow_rate : float
            Volumetric flow rate, m^3/s.

        Returns
        -------
        float
            Pressure drop, Pa.
        """
        v = self.velocity(flow_rate)
        f = self.friction_factor(flow_rate)
        return f * (self.length / self.diameter) * (self.fluid.density * v ** 2 / 2.0)

    def summary(self, flow_rate):
        """
        Compute all key flow results at once for a given flow rate.

        Parameters
        ----------
        flow_rate : float
            Volumetric flow rate, m^3/s.

        Returns
        -------
        dict
            Dictionary with velocity, reynolds_number, friction_factor,
            pressure_drop_pa, and pressure_drop_kpa.
        """
        v = self.velocity(flow_rate)
        Re = self.reynolds_number(flow_rate)
        f = self.friction_factor(flow_rate)
        dp = self.pressure_drop(flow_rate)
        return {
            "velocity_m_s": v,
            "reynolds_number": Re,
            "friction_factor": f,
            "flow_regime": "Laminar" if Re < 2300 else ("Transitional" if Re < 4000 else "Turbulent"),
            "pressure_drop_pa": dp,
            "pressure_drop_kpa": dp / 1000.0,
        }


# ---------------------------------------------------------------------------
# ConductionWall
# ---------------------------------------------------------------------------
class ConductionWall:
    """
    Steady-state, one-dimensional conduction through a single flat layer
    (Fourier's Law).

    Attributes
    ----------
    thermal_conductivity : float
        Material thermal conductivity, W/m.K.
    area : float
        Cross-sectional area normal to heat flow, m^2.
    thickness : float
        Wall thickness (conduction path length), m.
    """

    def __init__(self, thermal_conductivity, area, thickness):
        """
        Parameters
        ----------
        thermal_conductivity : float
            W/m.K. Must be positive.
        area : float
            m^2. Must be positive.
        thickness : float
            m. Must be positive.

        Raises
        ------
        ValueError
            If any parameter is not a positive number.
        """
        if thermal_conductivity is None or thermal_conductivity <= 0:
            raise ValueError("Thermal conductivity must be a positive number (W/m.K).")
        if area is None or area <= 0:
            raise ValueError("Area must be a positive number (m^2).")
        if thickness is None or thickness <= 0:
            raise ValueError("Thickness must be a positive number (m).")

        self.thermal_conductivity = float(thermal_conductivity)
        self.area = float(area)
        self.thickness = float(thickness)

    def heat_transfer_rate(self, T_hot, T_cold):
        """
        Steady-state conduction heat transfer rate via Fourier's Law:

            Q = k * A * (T_hot - T_cold) / L

        Parameters
        ----------
        T_hot : float
            Hot-face temperature, K or degC (consistent with T_cold).
        T_cold : float
            Cold-face temperature, same units as T_hot.

        Returns
        -------
        float
            Heat transfer rate, W. Positive means heat flows from the hot
            face to the cold face.
        """
        return (self.thermal_conductivity * self.area *
                (T_hot - T_cold) / self.thickness)

    def heat_flux(self, T_hot, T_cold):
        """
        Heat flux (rate per unit area), W/m^2.

        Parameters
        ----------
        T_hot : float
            Hot-face temperature.
        T_cold : float
            Cold-face temperature.

        Returns
        -------
        float
            Heat flux, W/m^2.
        """
        return self.heat_transfer_rate(T_hot, T_cold) / self.area


# ---------------------------------------------------------------------------
# CoolingProcess
# ---------------------------------------------------------------------------
class CoolingProcess:
    """
    Lumped-capacitance transient cooling of a solid body per Newton's
    Law of Cooling.

    Governing equation:
        m * cp * dT/dt = -h * A * (T - T_inf)

    Solution:
        T(t) = T_inf + (T0 - T_inf) * exp(-t / tau)
        tau  = m * cp / (h * A)

    Attributes
    ----------
    T0 : float
        Initial body temperature, degC (or K).
    T_inf : float
        Ambient (surrounding fluid) temperature, same units as T0.
    h : float
        Convective heat transfer coefficient, W/m^2.K.
    area : float
        Surface area exposed to the ambient fluid, m^2.
    mass : float
        Mass of the body, kg.
    specific_heat : float
        Specific heat capacity of the body, J/kg.K.
    tau : float
        Thermal time constant, s (computed automatically).
    """

    def __init__(self, T0, T_inf, h, area, mass, specific_heat):
        """
        Parameters
        ----------
        T0 : float
            Initial temperature.
        T_inf : float
            Ambient temperature. Must differ from T0.
        h : float
            Convective heat transfer coefficient, W/m^2.K. Must be positive.
        area : float
            Surface area, m^2. Must be positive.
        mass : float
            Mass, kg. Must be positive.
        specific_heat : float
            Specific heat, J/kg.K. Must be positive.

        Raises
        ------
        ValueError
            If any physical parameter is non-positive, or T0 == T_inf.
        """
        if h is None or h <= 0:
            raise ValueError("Heat transfer coefficient h must be a positive number (W/m^2.K).")
        if area is None or area <= 0:
            raise ValueError("Area must be a positive number (m^2).")
        if mass is None or mass <= 0:
            raise ValueError("Mass must be a positive number (kg).")
        if specific_heat is None or specific_heat <= 0:
            raise ValueError("Specific heat must be a positive number (J/kg.K).")
        if T0 == T_inf:
            raise ValueError("Initial temperature T0 cannot equal ambient temperature T_inf.")

        self.T0 = float(T0)
        self.T_inf = float(T_inf)
        self.h = float(h)
        self.area = float(area)
        self.mass = float(mass)
        self.specific_heat = float(specific_heat)
        self.tau = (self.mass * self.specific_heat) / (self.h * self.area)

    def temperature_at(self, t):
        """
        Body temperature at time t.

        Parameters
        ----------
        t : float
            Time, s. Must be >= 0.

        Returns
        -------
        float
            Temperature at time t.
        """
        if t < 0:
            raise ValueError("Time t must be zero or positive (s).")
        return self.T_inf + (self.T0 - self.T_inf) * math.exp(-t / self.tau)

    def time_to_reach(self, T_target):
        """
        Analytical time required to reach a target temperature.

            t = -tau * ln( (T_target - T_inf) / (T0 - T_inf) )

        Parameters
        ----------
        T_target : float
            Target temperature. Must lie strictly between T_inf and T0
            (exclusive), since the body asymptotically approaches T_inf
            and never overshoots it.

        Returns
        -------
        float
            Time in seconds to reach T_target.

        Raises
        ------
        ValueError
            If T_target is not strictly between T0 and T_inf.
        """
        lo, hi = sorted([self.T_inf, self.T0])
        if not (lo < T_target < hi):
            raise ValueError(
                f"T_target must be strictly between T_inf ({self.T_inf}) "
                f"and T0 ({self.T0})."
            )
        ratio = (T_target - self.T_inf) / (self.T0 - self.T_inf)
        return -self.tau * math.log(ratio)

    def generate_curve(self, t_max, n_points=200):
        """
        Generate time and temperature arrays for plotting the cooling curve.

        Parameters
        ----------
        t_max : float
            Maximum time to plot, s. Must be positive.
        n_points : int, optional
            Number of points to generate. Default 200.

        Returns
        -------
        tuple of (list, list)
            (time_values, temperature_values)
        """
        if t_max is None or t_max <= 0:
            raise ValueError("t_max must be a positive number (s).")
        if n_points < 2:
            raise ValueError("n_points must be at least 2.")

        dt = t_max / (n_points - 1)
        times = [i * dt for i in range(n_points)]
        temps = [self.temperature_at(t) for t in times]
        return times, temps
