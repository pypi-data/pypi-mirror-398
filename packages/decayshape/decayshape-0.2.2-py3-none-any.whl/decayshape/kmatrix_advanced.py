"""
Advanced K-matrix implementation using poles and channels.

This module provides a more sophisticated K-matrix implementation
that uses the particle/pole/channel structure for complex multi-channel
resonance analysis.
"""

from typing import Any, Optional, Union

from pydantic import Field, model_validator

from decayshape import config

from .base import FixedParam, Lineshape
from .particles import Channel
from .utils import angular_momentum_barrier_factor, blatt_weiskopf_form_factor


class KMatrixAdvanced(Lineshape):
    """
    Advanced K-matrix lineshape using poles and channels.

    This implementation allows for multiple poles and channels,
    making it suitable for complex coupled-channel analysis.
    """

    # Fixed parameters (channels and particles)
    channels: FixedParam[list[Channel]] = Field(..., description="List of decay channels")
    output_channel: FixedParam[int] = Field(
        default=FixedParam[int](value=0), description="Which channel of the F-vector to return (0-indexed)"
    )

    # Optimization parameters (poles and couplings)
    pole_masses: list[float] = Field(..., description="List of pole masses")
    production_couplings: list[float] = Field(
        default_factory=list, description="Production couplings from initial state to each pole (length = n_poles)"
    )
    decay_couplings: list[float] = Field(
        default_factory=list, description="Decay couplings from each pole to each channel (length = n_poles × n_channels)"
    )
    r: float = Field(default=1.0, description="Hadron radius parameter")

    background: Optional[list[float]] = Field(default=None, description="Background terms. Length = n_poles x n_channels")
    production_background: Optional[list[float]] = Field(
        default=None, description="Production background terms. Length = n_channels"
    )
    q0: Optional[float] = Field(default=None, description="Reference momentum")

    class Config:
        arbitrary_types_allowed = True

    @model_validator(mode="after")
    def validate_and_fill_couplings(self):
        """Validate coupling lengths and fill with defaults if empty."""
        n_poles = len(self.pole_masses)
        n_channels = len(self.channels.value)

        # Validate output_channel
        if self.output_channel.value < 0 or self.output_channel.value >= n_channels:
            raise ValueError(f"output_channel must be between 0 and {n_channels-1}, got {self.output_channel.value}")

        # Fill production couplings with defaults if empty
        if not self.production_couplings:
            self.production_couplings = [1.0] * n_poles
        elif len(self.production_couplings) != n_poles:
            raise ValueError(f"production_couplings must have length {n_poles}, got {len(self.production_couplings)}")

        # Fill decay couplings with defaults if empty
        if not self.decay_couplings:
            self.decay_couplings = [1.0] * (n_poles * n_channels)
        elif len(self.decay_couplings) != n_poles * n_channels:
            raise ValueError(f"decay_couplings must have length {n_poles * n_channels}, got {len(self.decay_couplings)}")

        if self.background is not None:
            if len(self.background) != n_poles * n_channels:
                raise ValueError(f"background must have length {n_poles * n_channels}, got {len(self.background)}")

        if self.production_background is not None:
            if len(self.production_background) != n_channels:
                raise ValueError(f"production_background must have length {n_channels}, got {len(self.production_background)}")

        return self

    @property
    def parameter_order(self) -> list[str]:
        """Return the order of parameters for positional arguments."""
        n_poles = len(self.pole_masses)
        n_channels = len(self.channels.value)

        # Build flat parameter order
        params = []

        # Add pole masses
        for i in range(n_poles):
            params.append(f"pole_mass_{i}")

        # Add production couplings
        for i in range(n_poles):
            params.append(f"production_coupling_{i}")

        # Add decay couplings (pole_index * n_channels + channel_index)
        for pole_idx in range(n_poles):
            for channel_idx in range(n_channels):
                params.append(f"decay_coupling_{pole_idx}_{channel_idx}")

        # Add background terms
        if self.background is not None:
            for pole_idx in range(n_poles):
                for channel_idx in range(n_channels):
                    params.append(f"background_{pole_idx}_{channel_idx}")

        # Add production background terms
        if self.production_background is not None:
            for channel_idx in range(n_channels):
                params.append(f"production_background_{channel_idx}")

        # Add other parameters
        params.extend(["r"])
        if self.q0 is not None:
            params.append("q0")

        return params

    def _get_parameters(self, *args, **kwargs) -> dict[str, Any]:
        """
        Get parameters with overrides, handling flat parameter structure.
        """
        # Start with optimization parameters
        params = self.get_optimization_parameters().copy()
        # Apply positional arguments
        args, kwargs = self._parse_args_and_kwargs(args, kwargs)
        # Convert flat parameters back to lists for internal use
        n_poles = len(self.pole_masses)
        n_channels = len(self.channels.value)

        # Handle pole masses
        pole_masses = []
        for i in range(n_poles):
            param_name = f"pole_mass_{i}"
            if param_name in kwargs:
                pole_masses.append(kwargs[param_name])
            else:
                pole_masses.append(self.pole_masses[i])
        params["pole_masses"] = pole_masses

        # Handle production couplings
        production_couplings = []
        for i in range(n_poles):
            param_name = f"production_coupling_{i}"
            if param_name in kwargs:
                production_couplings.append(kwargs[param_name])
            else:
                production_couplings.append(self.production_couplings[i])
        params["production_couplings"] = production_couplings

        # Handle decay couplings
        decay_couplings = []
        for pole_idx in range(n_poles):
            for channel_idx in range(n_channels):
                param_name = f"decay_coupling_{pole_idx}_{channel_idx}"
                flat_idx = pole_idx * n_channels + channel_idx
                if param_name in kwargs:
                    decay_couplings.append(kwargs[param_name])
                else:
                    decay_couplings.append(self.decay_couplings[flat_idx])
        params["decay_couplings"] = decay_couplings

        # Handle background terms
        if self.background is not None:
            background = []
            for pole_idx in range(n_poles):
                for channel_idx in range(n_channels):
                    flat_idx = pole_idx * n_channels + channel_idx
                    param_name = f"background_{pole_idx}_{channel_idx}"
                    if param_name in kwargs:
                        background.append(kwargs[param_name])
                    else:
                        background.append(self.background[flat_idx])
            params["background"] = background

        # Handle production background terms
        if self.production_background is not None:
            production_background = []
            for channel_idx in range(n_channels):
                param_name = f"production_background_{channel_idx}"
                if param_name in kwargs:
                    production_background.append(kwargs[param_name])
                else:
                    production_background.append(self.production_background[channel_idx])
            params["production_background"] = production_background

        # Handle other parameters
        for param_name in ["r", "q0"]:
            if param_name in kwargs:
                params[param_name] = kwargs[param_name]

        return params

    def parameters(self) -> dict[str, Any]:
        """
        Get parameters in the order specified by parameter_order with their actual values.

        For KMatrixAdvanced, this converts the internal data structures (pole_masses,
        production_couplings, decay_couplings) to the flat parameter names used in
        parameter_order.

        Returns:
            Dictionary with flat parameter names as keys and their actual values as values,
            ordered according to parameter_order
        """
        param_dict = {}
        n_poles = len(self.pole_masses)
        n_channels = len(self.channels.value)

        # Add pole masses
        for i in range(n_poles):
            param_dict[f"pole_mass_{i}"] = self.pole_masses[i]

        # Add production couplings
        for i in range(n_poles):
            param_dict[f"production_coupling_{i}"] = self.production_couplings[i]

        # Add decay couplings
        for pole_idx in range(n_poles):
            for channel_idx in range(n_channels):
                flat_idx = pole_idx * n_channels + channel_idx
                param_dict[f"decay_coupling_{pole_idx}_{channel_idx}"] = self.decay_couplings[flat_idx]

        # Add background terms
        if self.background is not None:
            for pole_idx in range(n_poles):
                for channel_idx in range(n_channels):
                    flat_idx = pole_idx * n_channels + channel_idx
                    param_dict[f"background_{pole_idx}_{channel_idx}"] = self.background[flat_idx]

        # Add production background terms
        if self.production_background is not None:
            for channel_idx in range(n_channels):
                param_dict[f"production_background_{channel_idx}"] = self.production_background[channel_idx]

        # Add other parameters
        param_dict["r"] = self.r
        param_dict["q0"] = self.q0

        return param_dict

    def function(self, angular_momentum, spin, s, *args, **kwargs) -> Union[float, Any]:
        """
        Evaluate the advanced K-matrix lineshape.

        Args:
            angular_momentum: Angular momentum parameter (doubled values: 0, 2, 4, ...)
            spin: Spin parameter (doubled values: 1, 3, 5, ...)
            s: Mandelstam variable s (mass squared) or array of s values
            *args: Positional parameter overrides
            **kwargs: Keyword parameter overrides

        Implements the K-matrix formalism as described in AmpForm documentation:
        1. Build full T-matrix for all channels
        2. Build P-vector from production couplings
        3. Build F-vector from T-matrix and P-vector
        4. Return first entry of F-vector
        """
        # Get parameters with overrides
        params = self._get_parameters(*args, **kwargs)

        n_poles = len(params["pole_masses"])
        n_channels = len(self.channels.value)

        # Step 1: Build the full T-matrix
        K_matrix = self._build_k_matrix(params, s, n_poles, n_channels)

        # Step 2: Build the P-vector
        P_vector = self._build_p_vector(params, s, n_poles, n_channels)

        # Step 3: Build the F-vector
        A = self._build_amplitude(K_matrix, P_vector, s, n_channels)

        # Step 4: Return the specified channel of the F-vector
        output_idx = self.output_channel.value

        # Compute angular momentum barrier factor
        q = self.channels.value[output_idx].momentum(s)
        L = angular_momentum // 2

        if params["q0"] is None:
            params["q0"] = self.channels.value[output_idx].momentum(
                config.backend.mean(config.backend.array(params["pole_masses"])) ** 2
            )

        B = angular_momentum_barrier_factor(q, params["q0"], L) * blatt_weiskopf_form_factor(q, params["r"], L)

        if n_channels == 1:
            # Single channel: F_vector is already 1D
            return A * B
        else:
            # Multi-channel: F_vector is 2D, return specified channel
            return A[output_idx, :] * B

    def __call__(self, angular_momentum, spin, *args, s=None, **kwargs) -> Union[float, Any]:
        s_val = s if s is not None else (self.s.value if self.s is not None else None)
        if s_val is None:
            raise ValueError("s must be provided either at construction or call time")
        return self.function(angular_momentum, spin, s_val, *args, **kwargs)

    def _build_k_matrix(
        self, params: dict[str, Any], s: Union[float, Any], n_poles: int, n_channels: int
    ) -> Union[float, Any]:
        """
        Build the K Matrix

        K_ij = sum_R (g_Ri * g_Rj) / (m_R^2 - s)
        """
        np = config.backend  # Get backend dynamically
        s_len = config.backend.shape(s)
        if len(s_len) == 0:
            s_len = 1
        else:
            (s_len,) = s_len

        # Build K-matrix: K_ij = sum_R (g_Ri * g_Rj) / (m_R^2 - s)
        # Vectorized approach: compute all pole contributions at once
        K = np.zeros((s_len, n_channels, n_channels), dtype=complex)

        # Convert decay couplings to array for vectorized operations
        g_matrix = np.array(params["decay_couplings"]).reshape(n_poles, n_channels)
        background = params.get("background", None)
        if background is not None:
            background = np.array(background).reshape(n_poles, n_channels)
        else:
            background = np.zeros((n_poles, n_channels), dtype=complex)

        pole_masses = np.array(params["pole_masses"])

        # Vectorized computation over all poles and s values
        for R in range(n_poles):
            m_R = pole_masses[R]
            denominator = m_R**2 - s
            # Handle the case where s equals a pole mass (add small epsilon)
            epsilon = 1e-15
            denominator = np.where(np.abs(denominator) < epsilon, epsilon, denominator)

            # Get decay couplings for this pole
            g_R = g_matrix[R]  # Shape: (n_channels,)
            background_R = background[R]
            g_R_matrix = g_R[:, None] * g_R[None, :]  # Shape: (n_channels, n_channels)

            # target shape: (s_len, n_channels, n_channels)
            K += g_R_matrix / denominator[:, None, None] + background_R
        return K

    def _build_p_vector(
        self, params: dict[str, Any], s: Union[float, Any], n_poles: int, n_channels: int
    ) -> Union[float, Any]:
        """
        Build the P-vector from production couplings.

        P_i = sum_R (beta_R * g_Ri) / (m_R^2 - s)
        where beta_R are the production couplings and g_Ri are the decay couplings.
        """
        np = config.backend  # Get backend dynamically
        len(s)

        # Convert to arrays for vectorized operations
        g_matrix = np.array(params["decay_couplings"]).reshape(n_poles, n_channels)  # (n_poles, n_channels)
        beta_array = np.array(params["production_couplings"])  # (n_poles,)
        pole_masses = np.array(params["pole_masses"])  # (n_poles,)

        denominators = pole_masses[:, None] ** 2 - s[None, :]  # (n_poles, s_len)

        # Handle the case where s equals a pole mass (add small epsilon)
        epsilon = 1e-15
        denominators = np.where(np.abs(denominators) < epsilon, epsilon, denominators)

        contributions = (
            beta_array[:, None, None] * g_matrix[:, :, None] / denominators[:, None, :]
        )  # (n_poles, n_channels, s_len)
        # Sum over all poles to get final P-vector
        P_vector = np.sum(contributions, axis=0)  # (n_channels, s_len)

        # Add production background terms if present
        production_background = params.get("production_background", None)
        if production_background is not None:
            production_background_array = np.array(production_background)  # (n_channels,)
            P_vector = P_vector + production_background_array[:, None]  # (n_channels, s_len)

        return P_vector

    def _build_amplitude(self, K, P, s, n_channels):
        """
        The P-Vector amplitude is given by

        A_a = sum_c ((1 - iK rho )^-1)_ac P_c
        """

        np = config.backend

        # Calculate phase space factors for each channel (vectorized)
        rho_list = []
        for channel in self.channels.value:
            val = channel.phase_space_factor(s)
            rho_list.append(val)
        rho = np.stack(rho_list, axis=0)

        # shape: (s_len, n_channels, n_channels)
        rho_diag_matrix = np.eye(n_channels)[None, :, :] * rho.T[:, :, None]

        # A_a = K_ac P^c
        if n_channels == 1:
            # Single channel: T = K / (1 - i*K*rho)
            A = P[0] / (1 - 1j * K[0, 0] * rho[0])
        else:
            # Multi-channel case: T = K * (I - i*K*rho)^(-1)
            # Fully vectorized calculation for all s values at once
            unity = np.eye(n_channels)

            denominator_matrices = unity[None, :, :] - (1j * K @ rho_diag_matrix)
            T = np.linalg.inv(denominator_matrices)
            A = sum(T[:, :, i] * P_val[:, None] for i, P_val in enumerate(P))

        return A.T

    def get_channel_info(self) -> dict[str, Any]:
        """Get information about all channels."""
        info = {}
        for i, channel in enumerate(self.channels.value):
            info[f"channel_{i}"] = {
                "particles": [channel.particle1.value, channel.particle2.value],
                "threshold": channel.threshold,
                "total_mass": channel.total_mass,
            }
        return info

    def get_pole_info(self) -> dict[str, Any]:
        """Get information about all poles."""
        info = {}
        n_channels = len(self.channels.value)
        for i, pole_mass in enumerate(self.pole_masses):
            info[f"pole_{i}"] = {
                "mass": pole_mass,
                "production_coupling": self.production_couplings[i],
                "decay_couplings": self.decay_couplings[i * n_channels : (i + 1) * n_channels],
            }
        return info
