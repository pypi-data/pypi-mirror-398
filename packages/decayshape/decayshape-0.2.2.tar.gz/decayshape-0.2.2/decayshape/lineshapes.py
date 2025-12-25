"""
Lineshape implementations for hadron physics.

Contains various lineshapes commonly used in amplitude analysis:
- Relativistic Breit-Wigner
- Flatté
- K-matrix
"""

from typing import Any, Optional, Union

from pydantic import Field, model_validator

from decayshape import config

from .base import FixedParam, Lineshape
from .particles import Channel
from .utils import (
    angular_momentum_barrier_factor,
    blatt_weiskopf_form_factor,
    mass_dependent_width,
    relativistic_breit_wigner_denominator,
)


class RelativisticBreitWigner(Lineshape):
    """
    Relativistic Breit-Wigner lineshape.

    The most common lineshape for hadron resonances, accounting for
    the finite width and relativistic effects.
    """

    # Fixed parameters (don't change during optimization)
    channel: FixedParam[Channel] = Field(..., description="Decay channel for the resonance")

    # Optimization parameters
    pole_mass: float = Field(default=0.775, description="Pole mass of the resonance")
    width: float = Field(default=0.15, description="Resonance width")
    r: float = Field(default=1.0, description="Hadron radius parameter for Blatt-Weiskopf form factor")
    q0: Optional[float] = Field(default=None, description="Reference momentum (calculated from channel if None)")

    @property
    def parameter_order(self) -> list[str]:
        """Return the order of parameters for positional arguments."""
        params = ["pole_mass", "width", "r"]
        if self.q0 is not None:
            params.append("q0")
        return params

    def function(self, angular_momentum, spin, s, *args, **kwargs) -> Union[float, Any]:
        """
        Evaluate the Relativistic Breit-Wigner at given s values.

        Args:
            angular_momentum: Angular momentum parameter (doubled values: 0, 2, 4, ...)
            spin: Spin parameter (doubled values: 1, 3, 5, ...)
            s: Mandelstam variable s (mass squared) or array of s values
            *args: Positional parameter overrides (width, r, q0)
            **kwargs: Keyword parameter overrides

        Returns:
            Breit-Wigner amplitude
        """
        # Get parameters with overrides
        params = self._get_parameters(*args, **kwargs)

        if params["q0"] is None:
            params["q0"] = self.channel.value.momentum(params["pole_mass"] ** 2)

        # Calculate momentum in the decay frame using channel masses
        q = self.channel.momentum(s)

        # Convert doubled angular momentum to actual L value
        L = angular_momentum // 2

        # Blatt-Weiskopf form factor
        F = blatt_weiskopf_form_factor(q, params["r"], L)

        # Angular momentum barrier factor
        B = angular_momentum_barrier_factor(q, params["q0"], L)

        gamma_s = mass_dependent_width(q, s, params["q0"], params["pole_mass"], params["width"], L, params["r"])

        # Breit-Wigner denominator (use optimization parameter pole_mass)
        denominator = relativistic_breit_wigner_denominator(s, params["pole_mass"], gamma_s)

        return F * B / denominator

    def __call__(self, angular_momentum, spin, *args, s=None, **kwargs) -> Union[float, Any]:
        # Resolve s: prefer call-time s, else field value
        s_val = s if s is not None else (self.s.value if self.s is not None else None)
        if s_val is None:
            raise ValueError("s must be provided either at construction or call time")
        return self.function(angular_momentum, spin, s_val, *args, **kwargs)


class GounarisSakurai(Lineshape):
    """
    Gounaris-Sakurai lineshape.

    A modification of the Breit-Wigner shape used to describe the rho meson
    in the pi-pi spectrum, accounting for the energy dependence of the width
    and phase space factors.

    The lineshape is defined as:

    .. math::
        T(s) = \\frac{1 + d \\frac{\\Gamma_0}{m_0}}{m_0^2 - s + f(s) - i m_0 \\Gamma(s)}

    where :math:`\\Gamma(s)` is the energy-dependent width:

    .. math::
        \\Gamma(s) = \\Gamma_0 \\left(\\frac{q}{q_0}\\right)^3 \\frac{m_0}{\\sqrt{s}}

    and the function :math:`f(s)` is given by:

    .. math::
        f(s) = \\frac{\\Gamma_0 m_0^2}{q_0^3} \\left[ q^2 (h(s) - h(m_0^2)) + (m_0^2 - s) q_0^2 h'(m_0^2) \\right]

    with :math:`h(s)` defined as:

    .. math::
        h(s) = \\frac{2}{\\pi} \\frac{q}{\\sqrt{s}} \\ln\\left(\\frac{\\sqrt{s} + 2q}{2m_\\pi}\\right)

    and :math:`d = h'(m_0^2)`.

    This implementation also includes an optional :math:`\\omega` interference term:

    .. math::
        T_{total}(s) = T(s) \\times \\frac{1 + \\delta \\frac{s}{m_\\omega^2 - s - i m_\\omega \\Gamma_\\omega}}{1 + \\delta}
    """

    # Fixed parameters
    channel: FixedParam[Channel] = Field(..., description="Decay channel (usually pi+pi-)")

    # Optimization parameters
    pole_mass: float = Field(default=775, description="Pole mass of the resonance (m0)")
    width: float = Field(default=150, description="Resonance width (Gamma0)")
    omega_mass: float = Field(default=782.65, description="Omega mass or mass of interfering particle")
    omega_width: float = Field(default=8.49, description="Omega width or width of interfering particle")
    delta_mag: float = Field(default=0.0002, description="Magnitude of interfering particle")
    delta_phi: float = Field(default=1.65, description="Phase of interfering particle in radians")
    q0: Optional[float] = Field(default=None, description="Reference momentum (calculated from channel if None)")
    r: float = Field(default=1.0, description="Hadron radius parameter for Blatt-Weiskopf form factor")

    @property
    def parameter_order(self) -> list[str]:
        """Return the order of parameters for positional arguments."""
        params = ["pole_mass", "width", "omega_mass", "omega_width", "delta_mag", "delta_phi", "r"]
        if self.q0 is not None:
            params.append("q0")
        return params

    def function(self, angular_momentum, spin, s, *args, **kwargs) -> Union[float, Any]:
        """
        Evaluate the Gounaris-Sakurai lineshape at given s values.

        Args:
            angular_momentum: Angular momentum parameter (usually 2 for P-wave)
            spin: Spin parameter (usually 2 for rho)
            s: Mandelstam variable s (mass squared) or array of s values
            *args: Positional parameter overrides (pole_mass, width, q0)
            **kwargs: Keyword parameter overrides

        Returns:
            Gounaris-Sakurai amplitude
        """
        # Get parameters with overrides
        params = self._get_parameters(*args, **kwargs)

        L = angular_momentum // 2
        m0 = params["pole_mass"]
        gamma0 = params["width"]
        omega_mass = params["omega_mass"]
        omega_width = params["omega_width"]
        delta_mag = params["delta_mag"]
        delta_phi = params["delta_phi"]
        s_val = s

        # Calculate derived quantities
        m0_sq = m0**2

        # If q0 is not provided, calculate it at pole mass
        if params["q0"] is None:
            params["q0"] = self.channel.value.momentum(m0_sq)

        q0 = params["q0"]
        q = self.channel.momentum(s_val)

        # Get backend
        np = config.backend

        # Determine pion mass (assume channel is pi+pi- or similar symmetric channel)
        # Using particle1 mass as pion mass
        m_pi = self.channel.value.particle1.value.mass

        # correction terms to the mass
        m = np.sqrt(s_val)
        logTerm = np.log((m + q) / (2 * m_pi))
        logTerm0 = np.log((m0 + q0) / (2 * m_pi))

        t1 = 2 * m0_sq * q**3 * logTerm / (m * self.channel.value.momentum(m0_sq) ** 3)
        t2 = logTerm0 * (q**2 * (s - 3 * m0_sq) + s * (m0_sq - s)) / (m * q0**2)
        t3 = (m0_sq - s) / q0

        m2_corr = m0_sq + gamma0 * (t1 + t2 + t3)
        gamma_s = mass_dependent_width(q, s_val, q0, m0, gamma0, L, params["r"])

        denominator = m2_corr - 1j * m * gamma_s - s

        F = blatt_weiskopf_form_factor(q, params["r"], L)
        B = angular_momentum_barrier_factor(q, params["q0"], L)

        # Rho-Omega Interference
        delta = delta_mag * np.exp(1j * delta_phi)
        # Omega width also follows L=1 barrier scaling
        q_om = self.channel.value.momentum(omega_mass**2)
        gamma_om_s = mass_dependent_width(q, s_val, q_om, omega_mass, omega_width, L, params["r"])

        omega_term = (1 + delta * s / (omega_mass**2 - s - 1j * m * gamma_om_s)) / (1 + delta)

        return (F * B / denominator) * omega_term

    def __call__(self, angular_momentum, spin, *args, s=None, **kwargs) -> Union[float, Any]:
        s_val = s if s is not None else (self.s.value if self.s is not None else None)
        if s_val is None:
            raise ValueError("s must be provided either at construction or call time")
        return self.function(angular_momentum, spin, s_val, *args, **kwargs)


class Flatte(Lineshape):
    """
    Flatté lineshape for coupled-channel resonances.

    Used for resonances that can decay into multiple channels,
    such as the f0(980) which couples to both ππ and KK.
    """

    # Fixed parameters (don't change during optimization)
    channel1: FixedParam[Channel] = Field(..., description="First decay channel")
    channel2: FixedParam[Channel] = Field(..., description="Second decay channel")

    # Optimization parameters
    pole_mass: float = Field(description="Pole mass of the resonance")
    width1: float = Field(description="Width for first channel")
    width2: float = Field(description="Width for second channel")
    r1: float = Field(description="Hadron radius for first channel")
    r2: float = Field(description="Hadron radius for second channel")
    q01: Optional[float] = Field(default=None, description="Reference momentum for first channel")
    q02: Optional[float] = Field(default=None, description="Reference momentum for second channel")

    @property
    def parameter_order(self) -> list[str]:
        """Return the order of parameters for positional arguments."""
        params = ["pole_mass", "width1", "width2", "r1", "r2"]
        if self.q01 is not None:
            params.append("q01")
        if self.q02 is not None:
            params.append("q02")
        return params

    def function(self, angular_momentum, spin, s, *args, **kwargs) -> Union[float, Any]:
        """
        Evaluate the Flatté lineshape at given s values.

        Args:
            angular_momentum: Angular momentum parameter (doubled values: 0, 2, 4, ...)
            spin: Spin parameter (doubled values: 1, 3, 5, ...)
            s: Mandelstam variable s (mass squared) or array of s values
            *args: Positional parameter overrides (width1, width2, r1, r2, q01, q02)
            **kwargs: Keyword parameter overrides

        Returns:
            Flatté amplitude
        """
        # Get parameters with overrides
        params = self._get_parameters(*args, **kwargs)

        if params["q01"] is None:
            params["q01"] = self.channel1.value.momentum(params["pole_mass"] ** 2)
        if params["q02"] is None:
            params["q02"] = self.channel2.value.momentum(params["pole_mass"] ** 2)

        # Calculate momenta in both channels using Channel objects
        # Channel 1 momentum
        channel1 = self.channel1.value
        channel1.particle1.value.mass
        channel1.particle2.value.mass
        q1 = channel1.momentum(s)

        # Channel 2 momentum
        channel2 = self.channel2.value
        channel2.particle1.value.mass
        channel2.particle2.value.mass
        q2 = channel2.momentum(s)

        # Convert doubled angular momentum to actual L value
        L = angular_momentum // 2

        # Form factors and barrier factors for both channels
        blatt_weiskopf_form_factor(q1, params["r1"], L)
        blatt_weiskopf_form_factor(q2, params["r2"], L)
        angular_momentum_barrier_factor(q1, params["q01"], L)
        angular_momentum_barrier_factor(q2, params["q02"], L)

        gamma1 = mass_dependent_width(q1, s, params["q01"], params["pole_mass"], params["width1"], L, params["r1"])
        gamma2 = mass_dependent_width(q2, s, params["q02"], params["pole_mass"], params["width2"], L, params["r2"])

        # Total width
        total_width = gamma1 + gamma2
        # Flatté denominator (use optimization parameter pole_mass)
        denominator = params["pole_mass"] ** 2 - s - 1j * params["pole_mass"] * total_width

        numerator = params["pole_mass"] * mass_dependent_width(
            q1, s, params["q01"], params["pole_mass"], gamma1, L, params["r1"]
        )
        return numerator / denominator

    def __call__(self, angular_momentum, spin, *args, s=None, **kwargs) -> Union[float, Any]:
        s_val = s if s is not None else (self.s.value if self.s is not None else None)
        if s_val is None:
            raise ValueError("s must be provided either at construction or call time")
        return self.function(angular_momentum, spin, s_val, *args, **kwargs)


class Gaussian(Lineshape):
    """
    Square-root Gaussian lineshape.

    Returns the square root of a Gaussian probability density function.
    This is useful for amplitude analysis where the amplitude is proportional
    to the square root of the probability density.
    """

    # Optimization parameters
    mean: float = Field(default=0.0, description="Mean of the Gaussian")
    width: float = Field(default=1.0, description="Width (standard deviation) of the Gaussian")

    @property
    def parameter_order(self) -> list[str]:
        """Return the order of parameters for positional arguments."""
        return ["mean", "width"]

    def function(self, angular_momentum, spin, s, *args, **kwargs) -> Union[float, Any]:
        """
        Evaluate the square-root Gaussian at given s values.

        Args:
            angular_momentum: Angular momentum parameter (not used for Gaussian)
            spin: Spin parameter (not used for Gaussian)
            s: Mandelstam variable s (mass squared) or array of s values
            *args: Positional parameter overrides (mean, width)
            **kwargs: Keyword parameter overrides

        Returns:
            Square root of Gaussian PDF
        """
        # Get parameters with overrides
        params = self._get_parameters(*args, **kwargs)

        np = config.backend  # Get backend dynamically

        # Calculate Gaussian PDF: exp(-(s - mean)² / (2 * width²)) / (width * sqrt(2π))
        # Then take square root: sqrt(exp(-(s - mean)² / (2 * width²)) / (width * sqrt(2π)))
        # This simplifies to: exp(-(s - mean)² / (4 * width²)) / sqrt(width * sqrt(2π))

        mean = params["mean"]
        width = params["width"]

        # Calculate the square root of the Gaussian PDF
        # sqrt(1/(width*sqrt(2π))) * exp(-(s-mean)²/(4*width²))
        normalization = 1.0 / np.sqrt(width * np.sqrt(2 * np.pi))
        exponent = -((s**0.5 - mean) ** 2) / (4 * width**2)

        return np.sqrt(normalization * np.exp(exponent))

    def __call__(self, angular_momentum, spin, *args, s=None, **kwargs) -> Union[float, Any]:
        s_val = s if s is not None else (self.s.value if self.s is not None else None)
        if s_val is None:
            raise ValueError("s must be provided either at construction or call time")
        return self.function(angular_momentum, spin, s_val, *args, **kwargs)


class InterpolationBase(Lineshape):
    """
    Base class for interpolation-based lineshapes.

    This class provides the common Pydantic fields and validators for
    interpolation-based lineshapes where the amplitude is determined by
    interpolating between fixed mass points with floating amplitude parameters.
    """

    # Fixed parameters - mass points where interpolation is anchored
    mass_points: FixedParam[list[float]] = Field(description="Fixed mass points for interpolation")

    # Fixed parameter - whether to use complex interpolation
    complex: FixedParam[bool] = Field(
        default_factory=lambda: FixedParam(value=False),
        description="Whether to use complex interpolation (real and imaginary parts)",
    )

    # Optimization parameters - amplitude values at mass points
    amplitudes: list[float] = Field(
        default_factory=list,
        description="Amplitude values at the mass points. Leave empty to use default values. Otherwise, provide the amplitude values in the order of the mass points (n_amplitudes = n_mass_points or n_amplitudes = 2 * n_mass_points for complex interpolation).",
    )

    def _get_parameters(self, *args, **kwargs) -> dict[str, Any]:
        """Get parameters with overrides from call arguments."""
        args, kwargs = self._parse_args_and_kwargs(args, kwargs)
        params = {
            "amplitudes": [],
        }
        for name, default_value in zip(self.parameter_order, self.amplitudes):
            params["amplitudes"].append(kwargs.get(name, default_value))
        return params

    @property
    def parameter_order(self) -> list[str]:
        """Return the order of parameters for positional arguments."""
        if self.complex.value:
            # For complex interpolation, we have real and imaginary parts
            param_names = []
            for i in range(len(self.mass_points.value)):
                param_names.extend([f"amplitude_{i}_real", f"amplitude_{i}_imag"])
            return param_names
        else:
            # For real interpolation, we have just the amplitude values
            return [f"amplitude_{i}" for i in range(len(self.mass_points.value))]

    @model_validator(mode="after")
    def validate_amplitudes_length(self):
        """Validate that amplitudes list has the correct length for mass_points."""
        expected_length = len(self.mass_points.value)

        if self.complex.value:
            # For complex interpolation, we need 2 * number of mass points (real + imag)
            expected_length *= 2

        if len(self.amplitudes) == 0:
            # Initialize with default values
            if self.complex.value:
                # Default to 1.0 for real parts, 0.0 for imaginary parts
                self.amplitudes = []
                for _ in range(len(self.mass_points.value)):
                    self.amplitudes.extend([1.0, 0.0])  # real, imag
            else:
                self.amplitudes = [1.0] * len(self.mass_points.value)

        if len(self.amplitudes) != expected_length:
            raise ValueError(
                f"Amplitudes list length ({len(self.amplitudes)}) must match "
                f"expected length ({expected_length}) for {'complex' if self.complex.value else 'real'} interpolation"
            )
        return self

    def parameters(self) -> dict[str, Any]:
        """
        Get parameters in the order specified by parameter_order with their actual values.

        For interpolation classes, this returns the amplitude values as individual parameters.

        Returns:
            Dictionary with parameter names as keys and their actual values as values,
            ordered according to parameter_order
        """
        return {name: amplitude for name, amplitude in zip(self.parameter_order, self.amplitudes)}

    def interpolate(self, s_values, mass_points, amplitudes):
        """
        Template interpolation function.

        This is a template function that should be overridden by specific
        interpolation classes (LinearInterpolation, QuadraticInterpolation, etc.)
        to implement their specific interpolation algorithms.

        Args:
            s_values: Array of s values (mass squared) where to evaluate the interpolation
            mass_points: Array of mass points where interpolation is anchored
            amplitudes: Array of amplitude values at the mass points

        Returns:
            Interpolated amplitude values at s_values

        Raises:
            NotImplementedError: This template function should be overridden
        """
        raise NotImplementedError("interpolate method must be implemented by specific interpolation classes")

    def __call__(self, angular_momentum, spin, *args, s=None, **kwargs) -> Union[float, Any]:
        """
        Call the interpolation lineshape.

        This method handles the common logic for all interpolation classes
        and delegates the actual interpolation to the interpolate method.

        Args:
            angular_momentum: Angular momentum parameter (not used for interpolation)
            spin: Spin parameter (not used for interpolation)
            *args: Positional parameter overrides (amplitudes)
            s: Mandelstam variable s (mass squared) or array of s values
            **kwargs: Keyword parameter overrides

        Returns:
            Interpolated amplitude values
        """
        s_val = s if s is not None else (self.s.value if self.s is not None else None)
        if s_val is None:
            raise ValueError("s must be provided either at construction or call time")
        return self.function(angular_momentum, spin, s_val, *args, **kwargs)

    def function(self, angular_momentum, spin, s, *args, **kwargs) -> Union[float, Any]:
        """
        Call the interpolation lineshape.

        This method handles the common logic for all interpolation classes
        and delegates the actual interpolation to the interpolate method.

        Args:
            angular_momentum: Angular momentum parameter (not used for interpolation)
            spin: Spin parameter (not used for interpolation)
            *args: Positional parameter overrides (amplitudes)
            s: Mandelstam variable s (mass squared) or array of s values
            **kwargs: Keyword parameter overrides

        Returns:
            Interpolated amplitude values
        """
        # Get parameters with overrides
        params = self._get_parameters(*args, **kwargs)
        amplitudes = params["amplitudes"]

        if self.complex.value:
            # For complex interpolation, split amplitudes into real and imaginary parts
            len(self.mass_points.value)
            real_amplitudes = amplitudes[::2]  # Every other element starting from 0
            imag_amplitudes = amplitudes[1::2]  # Every other element starting from 1

            # Interpolate real and imaginary parts separately
            real_result = self.interpolate(s, self.mass_points.value, real_amplitudes)
            imag_result = self.interpolate(s, self.mass_points.value, imag_amplitudes)

            # Return complex result
            return real_result + 1j * imag_result
        else:
            # For real interpolation, use amplitudes directly
            return self.interpolate(s, self.mass_points.value, amplitudes)


class LinearInterpolation(InterpolationBase):
    """
    Linear interpolation lineshape.

    Performs linear interpolation between fixed mass points with floating
    amplitude parameters.
    """

    def interpolate(self, s_values, mass_points, amplitudes):
        """
        Perform linear interpolation.

        Args:
            s_values: Array of s values (mass squared) where to evaluate the interpolation
            mass_points: Array of mass points where interpolation is anchored
            amplitudes: Array of amplitude values at the mass points

        Returns:
            Linearly interpolated amplitude values
        """
        np = config.backend  # Get backend dynamically

        # Convert to arrays for vectorized operations
        s_array = np.asarray(s_values)
        mass_array = np.array(mass_points)
        amp_array = np.array(amplitudes)

        n_points = len(mass_array)

        if n_points == 0:
            # Empty arrays - return zeros
            return np.zeros_like(s_array, dtype=amp_array.dtype)
        elif n_points == 1:
            # Single point - return constant value
            return np.full_like(s_array, amp_array[0], dtype=amp_array.dtype)
        else:
            # Two or more points - use linear interpolation
            # Vectorized linear interpolation using numpy.interp
            # numpy.interp handles extrapolation by using the nearest values
            return np.interp(s_array, mass_array, amp_array)


class QuadraticInterpolation(InterpolationBase):
    """
    Quadratic interpolation lineshape.

    Performs quadratic interpolation between fixed mass points with floating
    amplitude parameters. Uses Lagrange interpolation for JAX compatibility.
    """

    def interpolate(self, s_values, mass_points, amplitudes):
        """
        Perform quadratic interpolation.

        Args:
            s_values: Array of s values (mass squared) where to evaluate the interpolation
            mass_points: Array of mass points where interpolation is anchored
            amplitudes: Array of amplitude values at the mass points

        Returns:
            Quadratically interpolated amplitude values
        """
        np = config.backend  # Get backend dynamically

        # Convert to arrays for vectorized operations
        s_array = np.asarray(s_values)
        mass_array = np.array(mass_points)
        amp_array = np.array(amplitudes)

        n_points = len(mass_array)

        if n_points < 2:
            # Not enough points for quadratic - fall back to constant
            return np.full_like(s_array, amp_array[0] if n_points == 1 else 0.0, dtype=amp_array.dtype)
        elif n_points == 2:
            # Only two points - use linear interpolation
            return np.interp(s_array, mass_array, amp_array)
        else:
            # Three or more points - use quadratic interpolation
            # For vectorized quadratic interpolation, we'll use a simplified approach
            # that works well for most cases and is JAX-compatible

            # Ensure s_array is at least 1D for vectorized operations
            if s_array.ndim == 0:
                s_array = s_array[np.newaxis]
                scalar_output = True
            else:
                scalar_output = False

            # Create a grid of s values and mass points for vectorized operations
            s_expanded = s_array[:, np.newaxis]  # Shape: (n_s, 1)
            mass_expanded = mass_array[np.newaxis, :]  # Shape: (1, n_mass)

            # Calculate distances from each s to each mass point
            distances = np.abs(s_expanded - mass_expanded)  # Shape: (n_s, n_mass)

            # For each s value, find the three closest mass points
            closest_indices = np.argsort(distances, axis=1)[:, :3]  # Shape: (n_s, 3)

            # Extract the three closest points for each s value
            x_points = np.take_along_axis(mass_expanded, closest_indices, axis=1)  # Shape: (n_s, 3)
            y_points = np.take_along_axis(amp_array[np.newaxis, :], closest_indices, axis=1)  # Shape: (n_s, 3)

            # Vectorized Lagrange quadratic interpolation
            x0, x1, x2 = x_points[:, 0], x_points[:, 1], x_points[:, 2]
            y0, y1, y2 = y_points[:, 0], y_points[:, 1], y_points[:, 2]

            # Lagrange basis polynomials (vectorized)
            L0 = ((s_array - x1) * (s_array - x2)) / ((x0 - x1) * (x0 - x2))
            L1 = ((s_array - x0) * (s_array - x2)) / ((x1 - x0) * (x1 - x2))
            L2 = ((s_array - x0) * (s_array - x1)) / ((x2 - x0) * (x2 - x1))

            result = y0 * L0 + y1 * L1 + y2 * L2

            # Return scalar if input was scalar
            if scalar_output:
                return result[0]
            return result


class CubicInterpolation(InterpolationBase):
    """
    Cubic interpolation lineshape.

    Performs cubic interpolation between fixed mass points with floating
    amplitude parameters. Uses Lagrange interpolation for JAX compatibility.
    """

    def interpolate(self, s_values, mass_points, amplitudes):
        """
        Perform cubic interpolation.

        Args:
            s_values: Array of s values (mass squared) where to evaluate the interpolation
            mass_points: Array of mass points where interpolation is anchored
            amplitudes: Array of amplitude values at the mass points

        Returns:
            Cubically interpolated amplitude values
        """
        np = config.backend  # Get backend dynamically

        # Convert to arrays for vectorized operations
        s_array = np.asarray(s_values)
        mass_array = np.array(mass_points)
        amp_array = np.array(amplitudes)

        n_points = len(mass_array)

        if n_points < 2:
            # Not enough points for cubic - fall back to constant
            return np.full_like(s_array, amp_array[0] if n_points == 1 else 0.0, dtype=amp_array.dtype)
        elif n_points == 2:
            # Only two points - use linear interpolation
            return np.interp(s_array, mass_array, amp_array)
        elif n_points == 3:
            # Three points - use quadratic interpolation
            # Ensure s_array is at least 1D for vectorized operations
            if s_array.ndim == 0:
                s_array = s_array[np.newaxis]
                scalar_output = True
            else:
                scalar_output = False

            s_expanded = s_array[:, np.newaxis]  # Shape: (n_s, 1)
            mass_expanded = mass_array[np.newaxis, :]  # Shape: (1, n_mass)

            distances = np.abs(s_expanded - mass_expanded)  # Shape: (n_s, n_mass)
            closest_indices = np.argsort(distances, axis=1)[:, :3]  # Shape: (n_s, 3)

            x_points = np.take_along_axis(mass_expanded, closest_indices, axis=1)  # Shape: (n_s, 3)
            y_points = np.take_along_axis(amp_array[np.newaxis, :], closest_indices, axis=1)  # Shape: (n_s, 3)

            x0, x1, x2 = x_points[:, 0], x_points[:, 1], x_points[:, 2]
            y0, y1, y2 = y_points[:, 0], y_points[:, 1], y_points[:, 2]

            L0 = ((s_array - x1) * (s_array - x2)) / ((x0 - x1) * (x0 - x2))
            L1 = ((s_array - x0) * (s_array - x2)) / ((x1 - x0) * (x1 - x2))
            L2 = ((s_array - x0) * (s_array - x1)) / ((x2 - x0) * (x2 - x1))

            result = y0 * L0 + y1 * L1 + y2 * L2

            # Return scalar if input was scalar
            if scalar_output:
                return result[0]
            return result
        else:
            # Four or more points - use cubic interpolation
            # Ensure s_array is at least 1D for vectorized operations
            if s_array.ndim == 0:
                s_array = s_array[np.newaxis]
                scalar_output = True
            else:
                scalar_output = False

            s_expanded = s_array[:, np.newaxis]  # Shape: (n_s, 1)
            mass_expanded = mass_array[np.newaxis, :]  # Shape: (1, n_mass)

            distances = np.abs(s_expanded - mass_expanded)  # Shape: (n_s, n_mass)
            closest_indices = np.argsort(distances, axis=1)[:, :4]  # Shape: (n_s, 4)

            x_points = np.take_along_axis(mass_expanded, closest_indices, axis=1)  # Shape: (n_s, 4)
            y_points = np.take_along_axis(amp_array[np.newaxis, :], closest_indices, axis=1)  # Shape: (n_s, 4)

            # Vectorized Lagrange cubic interpolation
            x0, x1, x2, x3 = x_points[:, 0], x_points[:, 1], x_points[:, 2], x_points[:, 3]
            y0, y1, y2, y3 = y_points[:, 0], y_points[:, 1], y_points[:, 2], y_points[:, 3]

            # Lagrange basis polynomials for cubic interpolation (vectorized)
            L0 = ((s_array - x1) * (s_array - x2) * (s_array - x3)) / ((x0 - x1) * (x0 - x2) * (x0 - x3))
            L1 = ((s_array - x0) * (s_array - x2) * (s_array - x3)) / ((x1 - x0) * (x1 - x2) * (x1 - x3))
            L2 = ((s_array - x0) * (s_array - x1) * (s_array - x3)) / ((x2 - x0) * (x2 - x1) * (x2 - x3))
            L3 = ((s_array - x0) * (s_array - x1) * (s_array - x2)) / ((x3 - x0) * (x3 - x1) * (x3 - x2))

            result = y0 * L0 + y1 * L1 + y2 * L2 + y3 * L3

            # Return scalar if input was scalar
            if scalar_output:
                return result[0]
            return result
