"""GHZ state (|GHZ_n>) multi-qubit entanglement circuit."""
from qiskit import QuantumCircuit


def create_ghz_circuit(n_qubits: int = 3, measure: bool = True) -> QuantumCircuit:
    """Creates an n-qubit Greenberger-Horne-Zeilinger (GHZ) state:
    |GHZ> = (|0...0> + |1...1>) / sqrt(2).
    
    Args:
        n_qubits: Number of qubits (default 3).
        measure: If True, adds measurement operations to classical registers.
        
    Returns:
        QuantumCircuit: The GHZ state circuit.
    """
    if n_qubits < 2:
        raise ValueError("GHZ circuit requires at least 2 qubits.")
    
    qc = QuantumCircuit(n_qubits, name=f"ghz_{n_qubits}q")
    qc.h(0)
    for i in range(n_qubits - 1):
        qc.cx(i, i + 1)
        
    if measure:
        qc.measure_all()
    return qc
