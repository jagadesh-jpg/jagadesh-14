"""Noisy simulation execution using defined noise models and AerSimulator."""
from typing import Dict, Tuple, Optional
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel
from ..metrics.fidelity import normalize_counts
from ..noise.noise_model import build_noise_model


def get_noisy_simulator(noise_model: NoiseModel) -> AerSimulator:
    """Instantiates a Qiskit AerSimulator backed by the provided NoiseModel."""
    return AerSimulator(noise_model=noise_model)


def run_noisy_simulation(
    circuit: QuantumCircuit,
    noise_model: Optional[NoiseModel] = None,
    noise_profile_name: str = "medium",
    shots: int = 4096,
    seed_simulator: int = 42,
) -> Tuple[Dict[str, float], Dict[str, int]]:
    """Executes a quantum circuit under realistic noise simulation.
    
    Args:
        circuit: Transpiled quantum circuit with measurements.
        noise_model: Optional pre-constructed NoiseModel. If None, builds from profile name.
        noise_profile_name: Name of profile ('low', 'medium', 'high') if noise_model is None.
        shots: Number of measurement shots.
        seed_simulator: Random seed for reproducible sampling.
        
    Returns:
        prob_dist: Normalized empirical probability distribution.
        raw_counts: Raw shot counts dictionary.
    """
    if noise_model is None:
        noise_model = build_noise_model(noise_profile_name)

    sim = AerSimulator(noise_model=noise_model)
    job = sim.run(circuit, shots=shots, seed_simulator=seed_simulator)
    result = job.result()
    counts = result.get_counts()
    prob_dist = normalize_counts(counts)
    return prob_dist, counts
