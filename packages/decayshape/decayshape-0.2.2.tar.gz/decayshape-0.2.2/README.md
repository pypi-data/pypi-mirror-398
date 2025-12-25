# DecayShape

[![codecov](https://codecov.io/gh/KaiHabermann/DecayShape/branch/main/graph/badge.svg)](https://codecov.io/gh/KaiHabermann/DecayShape)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

A Python package for lineshapes used in hadron physics amplitude or partial wave analysis.

## Features

- **Configurable Backend**: Switch between NumPy and JAX backends for all mathematical operations
- **Standard Lineshapes**: Relativistic Breit-Wigner, Flatté, and K-matrix implementations
- **Utility Functions**: Blatt-Weiskopf form factors and angular momentum barrier factors
- **Extensible Design**: Abstract base class for implementing custom lineshapes

## Installation

```bash
pip install decayshape
```

## Quick Start

```python
import decayshape as ds
import numpy as np

# Create a Relativistic Breit-Wigner with s values
s_values = np.linspace(0.5, 1.0, 100)
bw = ds.RelativisticBreitWigner(s=s_values, pole_mass=0.775, width=0.15)

# Evaluate with default parameters
amplitude = bw()

# Override parameters at call time (for optimization)
amplitude_override = bw(width=0.2, r=1.5)  # keyword arguments
amplitude_pos = bw(0.2, 1.5)  # positional arguments

# Switch to JAX backend
ds.set_backend("jax")
import jax.numpy as jnp

# Now all operations use JAX
s_jax = jnp.linspace(0.5, 1.0, 100)
bw_jax = ds.RelativisticBreitWigner(s=s_jax, pole_mass=0.775, width=0.15)
amplitude_jax = bw_jax(width=0.2)
```

## Available Lineshapes

### Relativistic Breit-Wigner
```python
bw = ds.RelativisticBreitWigner(
    s=s_values,                 # Mandelstam variable s (automatically wrapped as FixedParam)
    pole_mass=0.775,            # Pole mass (optimization parameter)
    width=0.15,                 # Width (optimization parameter)
    r=1.0,                      # Hadron radius (optimization parameter)
    L=0                         # Angular momentum (optimization parameter)
)
```

### Flatté
```python
flatte = ds.Flatte(
    s=s_values,                     # Mandelstam variable s (auto-wrapped)
    pole_mass=0.98,                 # Pole mass
    # Channel masses (auto-wrapped as FixedParam[float])
    channel1_mass1=0.139,           # π mass
    channel1_mass2=0.139,           # π mass
    channel2_mass1=0.494,           # K mass
    channel2_mass2=0.494,           # K mass
    # Width and dynamics per channel
    width1=0.1,
    width2=0.05,
    r1=1.0,
    r2=1.0,
    L1=0,
    L2=0
    # q01 and q02 are optional; if omitted they default to pole_mass/2
)
```

### K-matrix (advanced)
```python
from decayshape import Channel, CommonParticles

# Define channels (auto-wrapped FixedParam for particles)
pipi = Channel(
    particle1=CommonParticles.PI_PLUS,
    particle2=CommonParticles.PI_MINUS,
)
kk = Channel(
    particle1=CommonParticles.K_PLUS,
    particle2=CommonParticles.K_MINUS,
)

kmat = ds.KMatrixAdvanced(
    s=s_values,                     # Mandelstam variable s (auto-wrapped)
    channels=[pipi, kk],            # List[Channel]
    pole_masses=[0.775, 0.98],      # List of pole masses (n_poles)
    production_couplings=[1.0, 0.8],# length = n_poles
    # decay_couplings: length = n_poles * n_channels (row-major)
    decay_couplings=[1.0, 0.5, 0.3, 0.7],
    output_channel=0,               # which channel amplitude to return
    r=1.0,
    L=0
)

# Evaluate
ampl = kmat()
```

## Backend Configuration

The package supports both NumPy and JAX backends:

```python
# Use NumPy (default)
ds.set_backend("numpy")

# Use JAX
ds.set_backend("jax")
```

## Parameter Separation

The lineshapes distinguish between two types of parameters using Pydantic models:

- **Fixed Parameters**: Marked with `FixedParam[type]` and never change during optimization (e.g., `s` values, channel masses)
- **Optimization Parameters**: Regular Pydantic fields that can be overridden at call time (e.g., pole masses, widths, couplings, radii)

This separation makes the lineshapes ideal for parameter optimization where only certain parameters need to be varied.

**Automatic FixedParam Wrapping**: You don't need to manually wrap values in `FixedParam()` - the system automatically detects `FixedParam` fields and wraps the values for you. This means you can simply pass `s=s_values` instead of `s=ds.FixedParam(s_values)`.

## Serialization

All lineshapes support serialization and deserialization using Pydantic:

```python
# Serialize to dictionary
bw_dict = bw.model_dump()

# Serialize to JSON (for simple s values)
bw_json = bw.model_dump_json()

# Deserialize from dictionary
bw_restored = RelativisticBreitWigner.model_validate(bw_dict)

# Deserialize from JSON
bw_restored = RelativisticBreitWigner.model_validate(json.loads(bw_json))
```

## Parameter Optimization

The lineshapes support parameter override at call time, making them ideal for optimization:

```python
# Create a lineshape with s values and parameter separation
bw = ds.RelativisticBreitWigner(s=s_values, pole_mass=0.775, width=0.15, r=1.0, L=1)

# Override optimization parameters using keyword arguments
result1 = bw(width=0.2, r=1.5)

# Override optimization parameters using positional arguments (order: width, r, L, q0)
result2 = bw(0.2, 1.5, 0)

# Mix positional and keyword arguments
result3 = bw(0.2, 1.5, L=0)

# For optimization frameworks
def objective_function(params):
    width, r, L = params
    return bw(width, r, L)

# Get parameter information
print(f"Fixed parameters: {bw.get_fixed_parameters()}")
print(f"Optimization parameters: {bw.get_optimization_parameters()}")
print(f"Parameter order: {bw.parameter_order}")
```

## Utility Functions

```python
# Blatt-Weiskopf form factor
F = ds.blatt_weiskopf_form_factor(q, q0, r=1.0, L=0)

# Angular momentum barrier factor
B = ds.angular_momentum_barrier_factor(q, q0, L=0)
```

## Development

```bash
# Install in development mode
pip install -e .

# Run tests
pytest

# Format code
black decayshape/
isort decayshape/
```

## License

MIT License
