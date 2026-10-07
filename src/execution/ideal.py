"""Ideal (noiseless) statevector and shot-based quantum circuit execution."""
from typing import Dict, Tuple
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from ..metrics.fidelity import normalize_counts


def run_ideal_simulation(
    circuit: QuantumCircuit,
    shots: int = 4096,
    seed_simulator: int = 42,
) -> Tuple[Dict[str, float], Dict[str, int]]:
    """Executes a quantum circuit on an ideal (noiseless) AerSimulator.
    
    Args:
        circuit: Transpiled quantum circuit with measurements.
        shots: Number of measurement shots.
        seed_simulator: Random seed for reproducible sampling.
        
    Returns:
        prob_dist: Normalized empirical probability distribution.
        raw_counts: Raw shot counts dictionary.
    """
    ideal_backend = AerSimulator()
    job = ideal_backend.run(circuit, shots=shots, seed_simulator=seed_simulator)
    result = job.result()
    counts = result.get_counts()
    prob_dist = normalize_counts(counts)
    return prob_dist, counts
