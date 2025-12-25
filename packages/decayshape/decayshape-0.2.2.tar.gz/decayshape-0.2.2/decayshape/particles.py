"""
Particle classes for hadron physics.

Provides classes for particles with mass, spin, and parity quantum numbers.
"""

from typing import Any, Union

from pydantic import BaseModel, Field, model_validator

from .base import FixedParam, JsonSchemaMixin, Numerical
from .config import config


class Particle(BaseModel, JsonSchemaMixin):
    """
    A particle with mass, spin, and parity quantum numbers.

    This class represents a fundamental particle in hadron physics
    with its physical properties.
    """

    mass: Numerical = Field(..., description="Particle mass in MeV/c²")
    spin: float = Field(..., description="Particle spin (0, 0.5, 1, 1.5, 2, ...)")
    parity: int = Field(..., description="Particle parity (+1 or -1)")

    class Config:
        arbitrary_types_allowed = True

    def __repr__(self) -> str:
        """String representation of the particle."""
        return f"Particle(mass={self.mass}, spin={self.spin}, parity={self.parity})"

    def __str__(self) -> str:
        """Human-readable string representation."""
        parity_str = "+" if self.parity > 0 else "-"
        return f"m={self.mass:.3f}, J={self.spin}{parity_str}"


class Channel(BaseModel, JsonSchemaMixin):
    """
    A decay channel with two particles.

    This class represents a decay channel with two final state particles.
    Both particles are fixed parameters that don't change during optimization.
    """

    particle1: FixedParam[Particle] = Field(..., description="First particle in the channel")
    particle2: FixedParam[Particle] = Field(..., description="Second particle in the channel")

    class Config:
        arbitrary_types_allowed = True

    @model_validator(mode="before")
    @classmethod
    def auto_wrap_fixed_params(cls, values):
        """Automatically wrap values in FixedParam for FixedParam fields."""
        if not isinstance(values, dict):
            return values

        # Get the model fields
        model_fields = cls.model_fields

        for field_name, field_info in model_fields.items():
            if field_name in values:
                field_type = field_info.annotation

                # Check if this is a FixedParam field
                if isinstance(field_type, type) and issubclass(field_type, FixedParam):
                    value = values[field_name]

                    # If the value is not already a FixedParam, wrap it
                    if not isinstance(value, FixedParam):
                        if isinstance(value, dict) and "value" in value:
                            value = value["value"]
                        values[field_name] = FixedParam(value=value)

        return values

    @property
    def total_mass(self) -> float:
        """Total mass of the two particles."""
        return self.particle1.value.mass + self.particle2.value.mass

    @property
    def threshold(self) -> float:
        """Threshold energy for this channel."""
        return self.total_mass

    def momentum(self, s: Union[float, Any]) -> Union[float, Any]:
        """
        Calculate the momentum in the center-of-mass frame.

        For s above threshold: real momentum
        For s below threshold: complex momentum (imaginary part)

        Args:
            s: Mandelstam variable s (mass squared)

        Returns:
            Momentum q in the center-of-mass frame (complex for below threshold)
        """
        m1 = self.particle1.value.mass
        m2 = self.particle2.value.mass

        # Calculate the argument of the square root
        # arg = (s - (m1 + m2)^2) * (s - (m1 - m2)^2)
        s_plus = s - (m1 + m2) ** 2 + 0j
        s_minus = s - (m1 - m2) ** 2 + 0j
        arg = s_plus * s_minus

        # Use complex square root to handle negative arguments
        # sqrt(negative) = i * sqrt(|negative|)
        if config.backend.isscalar(arg):
            # Single value case
            q = (s_plus) ** 0.5 * (s_minus) ** 0.5 / (2 * s**0.5)
        else:
            # Array case
            q = (s_plus) ** 0.5 * (s_minus) ** 0.5 / (2 * s**0.5)
        return q

    def phase_space_factor(self, s: Union[float, Any]) -> Union[float, Any]:
        """
        Calculate the phase space factor ρ = 2q/√s.

        Below threshold: ρ = 0 (no phase space available)
        Above threshold: ρ = 2q/√s (normal phase space)

        Args:
            s: Mandelstam variable s (mass squared)

        Returns:
            Phase space factor ρ (zero below threshold)
        """
        threshold_squared = self.threshold**2

        q = self.momentum(s)
        return config.backend.where(s < threshold_squared, 0.0, 2 * q / s**0.5)

    def __repr__(self) -> str:
        """String representation of the channel."""
        return f"Channel({self.particle1.value} + {self.particle2.value})"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.particle1.value} + {self.particle2.value}"


# Common particles for convenience
class CommonParticles:
    """Common particles used in hadron physics."""

    # Mesons
    PI_PLUS = Particle(mass=0.13957, spin=0, parity=-1)
    PI_ZERO = Particle(mass=0.13498, spin=0, parity=-1)
    PI_MINUS = Particle(mass=0.13957, spin=0, parity=-1)

    K_PLUS = Particle(mass=0.49368, spin=0, parity=-1)
    K_ZERO = Particle(mass=0.49761, spin=0, parity=-1)
    K_MINUS = Particle(mass=0.49368, spin=0, parity=-1)
    K_BAR_ZERO = Particle(mass=0.49761, spin=0, parity=-1)

    ETA = Particle(mass=0.54786, spin=0, parity=-1)
    ETA_PRIME = Particle(mass=0.95778, spin=0, parity=-1)

    RHO_PLUS = Particle(mass=0.77526, spin=1, parity=-1)
    RHO_ZERO = Particle(mass=0.77526, spin=1, parity=-1)
    RHO_MINUS = Particle(mass=0.77526, spin=1, parity=-1)

    OMEGA = Particle(mass=0.78265, spin=1, parity=-1)
    PHI = Particle(mass=1.01946, spin=1, parity=-1)

    # Baryons
    PROTON = Particle(mass=0.93827, spin=0.5, parity=1)
    NEUTRON = Particle(mass=0.93957, spin=0.5, parity=1)

    LAMBDA = Particle(mass=1.11568, spin=0.5, parity=1)
    SIGMA_PLUS = Particle(mass=1.18937, spin=0.5, parity=1)
    SIGMA_ZERO = Particle(mass=1.19264, spin=0.5, parity=1)
    SIGMA_MINUS = Particle(mass=1.19745, spin=0.5, parity=1)

    XI_ZERO = Particle(mass=1.31486, spin=0.5, parity=1)
    XI_MINUS = Particle(mass=1.32171, spin=0.5, parity=1)

    # Nuclei
    DEUTERON = Particle(mass=1.87561, spin=1, parity=1)
    TRITON = Particle(mass=2.80892, spin=0.5, parity=1)
    HE3 = Particle(mass=2.80839, spin=0.5, parity=1)
    ALPHA = Particle(mass=3.72738, spin=0, parity=1)
