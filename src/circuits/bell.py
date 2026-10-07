"""Bell state (|Phi+>) test circuit."""
from qiskit import QuantumCircuit


def create_bell_circuit(measure: bool = True) -> QuantumCircuit:
    """Creates a 2-qubit Bell state |Phi+> = (|00> + |11>) / sqrt(2).
    
    Args:
        measure: If True, adds measurement operations to classical registers.
        
    Returns:
        QuantumCircuit: The 2-qubit Bell state circuit.
    """
    qc = QuantumCircuit(2, name="bell_phi_plus")
    qc.h(0)
    qc.cx(0, 1)
    if measure:
        qc.measure_all()
    return qc
