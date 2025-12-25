"""
Configuration system for DecayShape package.

Provides backend switching between numpy and JAX for all mathematical operations.
"""


import jax.numpy as jnp
import numpy as np


class Config:
    """Configuration class for managing backend selection."""

    def __init__(self, backend: str = "numpy"):
        """
        Initialize configuration with specified backend.

        Args:
            backend: Either "numpy" or "jax"
        """
        self._backend_name = backend
        self._set_backend(backend)

    def _set_backend(self, backend: str) -> None:
        """Set the backend module."""
        if backend == "numpy":
            self.backend = np
        elif backend == "jax":
            self.backend = jnp
        else:
            raise ValueError(f"Backend must be 'numpy' or 'jax', got {backend}")
        self._backend_name = backend

    @property
    def backend_name(self) -> str:
        """Get the current backend name."""
        return self._backend_name

    def set_backend(self, backend: str) -> None:
        """Change the backend."""
        self._set_backend(backend)

    def __repr__(self) -> str:
        return f"Config(backend='{self._backend_name}')"


# Global configuration instance
config = Config("numpy")


def set_backend(backend: str) -> None:
    """
    Set the global backend for all mathematical operations.

    Args:
        backend: Either "numpy" or "jax"
    """
    config.set_backend(backend)
