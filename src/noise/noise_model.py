"""Controlled Synthetic Noise Model generation using Qiskit Aer's native NoiseModel API.

Constructs controlled synthetic depolarizing and readout noise channels for reproducible simulation.
"""
from typing import Optional
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError
from .noise_profiles import NoiseProfile, get_noise_profile


def build_noise_model(
    profile_or_name: Optional[object] = "medium",
    include_readout: bool = True,
    include_gate_noise: bool = True,
) -> NoiseModel:
    """Builds a verified Qiskit Aer NoiseModel based on defined controlled synthetic error parameters.
    
    Args:
        profile_or_name: Either a NoiseProfile instance or string ('low', 'medium', 'high').
        include_readout: Whether to include classical readout errors.
        include_gate_noise: Whether to include 1-qubit and 2-qubit depolarizing gate noise.
        
    Returns:
        NoiseModel: Native Qiskit Aer NoiseModel instance configured with synthetic noise channels.
    """
    if isinstance(profile_or_name, str):
        profile = get_noise_profile(profile_or_name)
    elif isinstance(profile_or_name, NoiseProfile):
        profile = profile_or_name
    else:
        raise TypeError(f"Invalid profile type: {type(profile_or_name)}")

    noise_model = NoiseModel()

    # 1. Quantum Gate Errors (Synthetic Depolarizing channels)
    if include_gate_noise:
        # 1-qubit gate errors
        if profile.p1_gate > 0:
            err_1q = depolarizing_error(profile.p1_gate, 1)
            # Add to common single-qubit gates
            noise_model.add_all_qubit_quantum_error(
                err_1q, ["x", "sx", "rz", "h", "s", "t", "rx", "ry", "id"]
            )

        # 2-qubit gate errors
        if profile.p2_gate > 0:
            err_2q = depolarizing_error(profile.p2_gate, 2)
            # Add to standard entangling gates
            noise_model.add_all_qubit_quantum_error(err_2q, ["cx", "cz", "ecr"])

    # 2. Measurement / Readout Errors
    if include_readout and (profile.p_meas0_prep1 > 0 or profile.p_meas1_prep0 > 0):
        # Readout error matrix: M[measured, prepared]
        # [[P(0|0), P(0|1)],
        #  [P(1|0), P(1|1)]]
        p01 = profile.p_meas0_prep1  # prepared 1, measured 0
        p10 = profile.p_meas1_prep0  # prepared 0, measured 1
        ro_matrix = [
            [1.0 - p10, p01],
            [p10, 1.0 - p01],
        ]
        ro_error = ReadoutError(ro_matrix)
        noise_model.add_all_qubit_readout_error(ro_error)

    return noise_model
