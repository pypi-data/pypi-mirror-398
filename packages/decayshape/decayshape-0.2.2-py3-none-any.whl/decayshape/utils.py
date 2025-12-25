"""
Utility functions for hadron physics lineshapes.

Contains Blatt-Weiskopf form factors and angular momentum barrier factors
commonly used in amplitude analysis.
"""

from typing import Any, Union

from decayshape import config


def blatt_weiskopf_form_factor(q: Union[float, Any], r: float, L: int) -> Union[float, Any]:
    """
    Calculate the Blatt-Weiskopf form factor.

    The Blatt-Weiskopf form factor accounts for the finite size of hadrons
    and depends on the angular momentum L of the decay.

    Args:
        q: Momentum in the decay frame
        r: Hadron radius parameter (in GeV^-1)
        L: Angular momentum of the decay

    Returns:
        Blatt-Weiskopf form factor
    """
    np = config.backend  # Get backend dynamically

    x = q * r
    if L == 0:
        return np.ones_like(q)
    elif L == 1:
        return np.sqrt(1 + x**2)
    elif L == 2:
        return np.sqrt(9 + 3 * x**2 + x**4)
    elif L == 3:
        return np.sqrt(225 + 45 * x**2 + 6 * x**4 + x**6)
    elif L == 4:
        return np.sqrt(11025 + 1575 * x**2 + 135 * x**4 + 10 * x**6 + x**8)
    else:
        raise ValueError(f"Blatt-Weiskopf form factor not implemented for L={L}")


def angular_momentum_barrier_factor(q: Union[float, Any], q0: Union[float, Any], L: int) -> Union[float, Any]:
    """
    Calculate the angular momentum barrier factor.

    The barrier factor accounts for the angular momentum dependence
    of the decay amplitude.

    Args:
        q: Momentum in the decay frame
        q0: Reference momentum (typically at resonance mass)
        L: Angular momentum of the decay

    Returns:
        Angular momentum barrier factor
    """
    np = config.backend  # Get backend dynamically

    if L == 0:
        return np.ones_like(q)
    else:
        return (q / q0) ** L


def phase_space_factor(q_s: Union[float, Any], s: Union[float, Any]) -> Union[float, Any]:
    """
    Calculate the phase space factor.
    """
    return 2 * q_s / s**0.5


def mass_dependent_width(
    q_s: Union[float, Any], s: Union[float, Any], q0: Union[float, Any], m0: float, gamma0: float, L: int, r: float
) -> Union[float, Any]:
    """
    Calculate the mass-dependent width.
    """
    rho = phase_space_factor(q_s, s)
    rho0 = phase_space_factor(q0, s)
    return (
        gamma0
        * rho
        / rho0
        * (
            angular_momentum_barrier_factor(q_s, q0, L)
            * blatt_weiskopf_form_factor(q_s, r, L)
            / blatt_weiskopf_form_factor(q0, r, L)
        )
        ** 2
    )


def relativistic_breit_wigner_denominator(s: Union[float, Any], mass: float, width: float) -> Union[float, Any]:
    """
    Calculate the denominator of a relativistic Breit-Wigner.

    Args:
        s: Mandelstam variable s (mass squared)
        mass: Resonance mass
        width: Resonance width

    Returns:
        Denominator of the Breit-Wigner
    """
    return s - mass**2 + 1j * mass * width


def two_body_breakup_momentum(s: Union[float, Any], m1: float, m2: float) -> Union[float, Any]:
    """
    Calculate the two-body breakup momentum in the center-of-mass frame.

    This is the momentum of each daughter particle in the center-of-mass frame
    of the parent particle decay.

    Args:
        s: Mandelstam variable s (mass squared of the parent)
        m1: Mass of first daughter particle
        m2: Mass of second daughter particle

    Returns:
        Breakup momentum in GeV/c
    """
    np = config.backend  # Get backend dynamically

    # Two-body breakup momentum formula
    # q = sqrt((s - (m1 + m2)^2) * (s - (m1 - m2)^2)) / (2 * sqrt(s))
    return np.sqrt((s - (m1 + m2) ** 2) * (s - (m1 - m2) ** 2)) / (2 * np.sqrt(s))
