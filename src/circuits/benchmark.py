"""Deep benchmark circuits: Parameterized QAOA-like alternating operator ansatz and long-range entanglement."""
import numpy as np
from qiskit import QuantumCircuit
from typing import Dict, Any


def create_qaoa_like_circuit(n_qubits: int = 3, p_layers: int = 2, measure: bool = True) -> QuantumCircuit:
    """Creates a deeper structured circuit representing a p-layer QAOA / Trotterized ansatz.
    
    This provides deeper gate structure with alternating single-qubit rotations
    and two-qubit entangling gates.
    """
    qc = QuantumCircuit(n_qubits, name=f"qaoa_like_{n_qubits}q_p{p_layers}")
    
    for q in range(n_qubits):
        qc.h(q)
        
    gamma = 0.392699
    beta = 0.785398
    
    for layer in range(p_layers):
        for i in range(n_qubits - 1):
            qc.cx(i, i + 1)
            qc.rz(2 * gamma * (layer + 1), i + 1)
            qc.cx(i, i + 1)
            
        for q in range(n_qubits):
            qc.rx(2 * beta / (layer + 1), q)
            
    if measure:
        qc.measure_all()
    return qc


def create_long_range_entangled_circuit(n_qubits: int = 3, measure: bool = True) -> QuantumCircuit:
    """Creates a circuit with direct non-nearest-neighbor entangling gates (e.g. CX between qubit 0 and qubit 2).
    
    On a linear nearest-neighbor coupling map [0 - 1 - 2], qubit 0 cannot directly interact with qubit 2.
    Transpilation to a hardware-like target forces the compiler to insert SWAP operations (or 3 CX gates),
    demonstrating realistic routing overhead and depth expansion.
    """
    qc = QuantumCircuit(n_qubits, name="non_local_bell_3q")
    qc.h(0)
    # Entangle non-adjacent qubits 0 and 2 directly across intermediary qubit 1
    qc.cx(0, 2)
    if measure:
        qc.measure_all()
    return qc


def get_benchmark_suite() -> Dict[str, QuantumCircuit]:
    """Returns the benchmark suite across diverse depths and topologies."""
    from .bell import create_bell_circuit
    from .ghz import create_ghz_circuit

    return {
        "bell_state_2q": create_bell_circuit(measure=True),
        "ghz_state_3q": create_ghz_circuit(n_qubits=3, measure=True),
        "non_local_bell_3q": create_long_range_entangled_circuit(n_qubits=3, measure=True),
        "qaoa_ansatz_3q_p2": create_qaoa_like_circuit(n_qubits=3, p_layers=2, measure=True),
    }
