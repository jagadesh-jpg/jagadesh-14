"""Noise profiles dataclass and controlled synthetic noise parameters.

Scientific Honesty Disclaimer:
These profiles are CONTROLLED SYNTHETIC NOISE PROFILES designed for reproducible
quantum software engineering benchmarks. While the orders of magnitude (1e-4 - 1e-2)
are representative of transmon superconducting quantum processors, they are strictly
synthetic and NOT directly parsed from physical IBM Quantum hardware calibration data.
"""
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class NoiseProfile:
    """Noise parameters characterizing controlled synthetic quantum processor errors.
    
    Attributes:
        name: Profile label ('low', 'medium', 'high').
        p1_gate: Single-qubit depolarizing error rate.
        p2_gate: Two-qubit depolarizing error rate.
        p_meas0_prep1: Readout error probability P(measure 1 | state 0).
        p_meas1_prep0: Readout error probability P(measure 0 | state 1).
        description: Synthetic regime description.
    """
    name: str
    p1_gate: float
    p2_gate: float
    p_meas0_prep1: float
    p_meas1_prep0: float
    description: str


# Documented controlled synthetic noise presets
NOISE_PROFILES: Dict[str, NoiseProfile] = {
    "low": NoiseProfile(
        name="low",
        p1_gate=0.0005,
        p2_gate=0.005,
        p_meas0_prep1=0.01,
        p_meas1_prep0=0.01,
        description="Controlled Synthetic Profile [Low]: Representative of high-coherence superconducting regime",
    ),
    "medium": NoiseProfile(
        name="medium",
        p1_gate=0.0015,
        p2_gate=0.015,
        p_meas0_prep1=0.025,
        p_meas1_prep0=0.025,
        description="Controlled Synthetic Profile [Medium]: Representative of typical NISQ transmon device regime",
    ),
    "high": NoiseProfile(
        name="high",
        p1_gate=0.004,
        p2_gate=0.04,
        p_meas0_prep1=0.05,
        p_meas1_prep0=0.05,
        description="Controlled Synthetic Profile [High]: Representative of heavy decoherence and cross-talk regime",
    ),
}


def get_noise_profile(name: str) -> NoiseProfile:
    """Retrieve predefined synthetic noise profile by name."""
    if name not in NOISE_PROFILES:
        raise KeyError(f"Unknown noise profile '{name}'. Choose from: {list(NOISE_PROFILES.keys())}")
    return NOISE_PROFILES[name]
