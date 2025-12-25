"""
Utility functions for generating JSON schemas of lineshapes.

This module provides helper functions for the frontend to understand
the structure and parameters of all available lineshapes.
"""

import json
from typing import Any, Optional

import numpy as np

from .kmatrix_advanced import KMatrixAdvanced
from .lineshapes import Flatte, GounarisSakurai, RelativisticBreitWigner
from .particles import Channel, CommonParticles


def get_all_lineshape_schemas() -> dict[str, dict[str, Any]]:
    """
    Generate JSON schemas for all available lineshape types.

    Returns:
        Dictionary mapping lineshape names to their JSON schemas
    """
    schemas = {}

    # Dummy s values (will be ignored in schemas)
    np.array([0.5, 0.6, 0.7])

    # RelativisticBreitWigner
    try:
        schemas["RelativisticBreitWigner"] = RelativisticBreitWigner.to_json_schema()
    except Exception as e:
        schemas["RelativisticBreitWigner"] = {"error": str(e)}

    # Flatte
    try:
        schemas["Flatte"] = Flatte.to_json_schema()
    except Exception as e:
        schemas["Flatte"] = {"error": str(e)}

    # GounarisSakurai
    try:
        schemas["GounarisSakurai"] = GounarisSakurai.to_json_schema()
    except Exception as e:
        schemas["GounarisSakurai"] = {"error": str(e)}

    # KMatrixAdvanced
    try:
        schemas["KMatrixAdvanced"] = KMatrixAdvanced.to_json_schema()
    except Exception as e:
        schemas["KMatrixAdvanced"] = {"error": str(e)}

    return schemas


def get_lineshape_schema(lineshape_name: str, **kwargs) -> dict[str, Any]:
    """
    Generate JSON schema for a specific lineshape type.

    Args:
        lineshape_name: Name of the lineshape class
        **kwargs: Additional parameters for lineshape construction

    Returns:
        JSON schema dictionary for the specified lineshape

    Raises:
        ValueError: If lineshape_name is not recognized
    """
    # Dummy s values (will be ignored in schema)
    s_vals = np.array([0.5, 0.6, 0.7])

    if lineshape_name == "RelativisticBreitWigner":
        defaults = {"pole_mass": 0.775, "width": 0.15}
        defaults.update(kwargs)
        lineshape = RelativisticBreitWigner(s=s_vals, **defaults)

    elif lineshape_name == "Flatte":
        defaults = {
            "pole_mass": 0.98,
            "channel1_mass1": 0.139,
            "channel1_mass2": 0.139,
            "channel2_mass1": 0.494,
            "channel2_mass2": 0.494,
            "width1": 1.0,
            "width2": 0.5,
            "r1": 1.0,
            "r2": 1.0,
            "L1": 0,
            "L2": 0,
        }
        defaults.update(kwargs)
        lineshape = Flatte(s=s_vals, **defaults)

    elif lineshape_name == "GounarisSakurai":
        defaults = {"pole_mass": 0.775, "width": 0.15}
        defaults.update(kwargs)
        lineshape = GounarisSakurai(s=s_vals, **defaults)

    elif lineshape_name == "KMatrixAdvanced":
        # Create default channels if not provided
        if "channels" not in kwargs:
            pipi_channel = Channel(particle1=CommonParticles.PI_PLUS, particle2=CommonParticles.PI_MINUS)
            kk_channel = Channel(particle1=CommonParticles.K_PLUS, particle2=CommonParticles.K_MINUS)
            kwargs["channels"] = [pipi_channel, kk_channel]

        defaults = {
            "pole_masses": [0.775, 0.98],
            "production_couplings": [1.0, 0.8],
            "decay_couplings": [1.0, 0.5, 0.3, 0.7],
            "output_channel": 0,
        }
        defaults.update(kwargs)
        lineshape = KMatrixAdvanced(s=s_vals, **defaults)

    else:
        raise ValueError(f"Unknown lineshape type: {lineshape_name}")

    return lineshape.to_json_schema()


def get_available_lineshapes() -> list[str]:
    """
    Get list of all available lineshape types.

    Returns:
        List of lineshape class names
    """
    return ["RelativisticBreitWigner", "Flatte", "GounarisSakurai", "KMatrixAdvanced"]


def export_schemas_to_file(filename: str, indent: Optional[int] = 2) -> None:
    """
    Export all lineshape schemas to a JSON file.

    Args:
        filename: Output filename
        indent: JSON indentation (None for compact)
    """
    schemas = get_all_lineshape_schemas()

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(schemas, f, indent=indent, ensure_ascii=False)


def get_common_particles_info() -> dict[str, Any]:
    """
    Get information about common particles for frontend use.

    Returns:
        Dictionary with particle information
    """
    particles_info = {}

    # Get all common particles
    common_particles = [
        ("PI_PLUS", CommonParticles.PI_PLUS),
        ("PI_MINUS", CommonParticles.PI_MINUS),
        ("K_PLUS", CommonParticles.K_PLUS),
        ("K_MINUS", CommonParticles.K_MINUS),
        ("PROTON", CommonParticles.PROTON),
        ("NEUTRON", CommonParticles.NEUTRON),
    ]

    for name, particle in common_particles:
        particles_info[name] = {
            "name": name,  # Use the constant name as the particle name
            "mass": particle.mass,
            "spin": particle.spin,
            "parity": particle.parity,
            # Note: charge is not defined in the current Particle class
        }

    return particles_info
