"""Circuit transpilation targeting a hardware-like synthetic target with restricted connectivity and native basis gates."""
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Tuple
from qiskit import QuantumCircuit, transpile
from qiskit.transpiler import CouplingMap


@dataclass
class TranspilationRecord:
    """Metadata and structural circuit characteristics before and after transpilation."""
    target_label: str
    optimization_level: int
    qubits_before: int
    qubits_after: int
    depth_before: int
    depth_after: int
    ops_before: Dict[str, int]
    ops_after: Dict[str, int]
    one_qubit_gates_before: int
    one_qubit_gates_after: int
    two_qubit_gates_before: int
    two_qubit_gates_after: int
    swap_gates_inserted: int
    transpiled_circuit: QuantumCircuit

    def to_dict(self) -> Dict[str, Any]:
        """Serializes circuit metrics to dictionary for logging/reporting."""
        return {
            "target_label": self.target_label,
            "optimization_level": self.optimization_level,
            "qubits_before": self.qubits_before,
            "qubits_after": self.qubits_after,
            "depth_before": self.depth_before,
            "depth_after": self.depth_after,
            "ops_before": self.ops_before,
            "ops_after": self.ops_after,
            "one_qubit_gates_before": self.one_qubit_gates_before,
            "one_qubit_gates_after": self.one_qubit_gates_after,
            "two_qubit_gates_before": self.two_qubit_gates_before,
            "two_qubit_gates_after": self.two_qubit_gates_after,
            "swap_gates_inserted": self.swap_gates_inserted,
        }


def count_gate_categories(circuit: QuantumCircuit) -> Tuple[int, int, int]:
    """Counts 1-qubit, 2-qubit, and explicit swap gates in circuit.
    
    Returns:
        (one_q_count, two_q_count, swap_count)
    """
    one_q = 0
    two_q = 0
    swap_count = 0
    non_gate_ops = {"measure", "barrier", "delay", "reset"}

    for inst in circuit.data:
        op_name = inst.operation.name
        if op_name in non_gate_ops:
            continue
        n_qubits = len(inst.qubits)
        if op_name == "swap":
            swap_count += 1
            two_q += 1
        elif n_qubits == 1:
            one_q += 1
        elif n_qubits == 2:
            two_q += 1
    return one_q, two_q, swap_count


def get_hardware_like_synthetic_target(n_qubits: int = 4) -> Tuple[CouplingMap, List[str], str]:
    """Builds a hardware-like synthetic target with restricted linear topology and transmon native basis gates.
    
    Label: 'hardware-like synthetic target'
    Topology: Restricted 1D nearest-neighbor linear coupling map [0 - 1 - 2 - 3 ...].
    Native Basis Gates: ['cx', 'id', 'rz', 'sx', 'x'].
    
    Scientific Honesty:
    This is an explicitly synthetic target model illustrating how physical connectivity
    constraints and basis gate decompositions reshape circuit depth and gate counts.
    It does NOT represent any proprietary or specific IBM processor calibration data.
    """
    edges = []
    for i in range(n_qubits - 1):
        edges.append([i, i + 1])
        edges.append([i + 1, i])
    cmap = CouplingMap(edges)
    basis_gates = ["cx", "id", "rz", "sx", "x"]
    label = "hardware-like synthetic target (linear nearest-neighbor coupling + transmon basis)"
    return cmap, basis_gates, label


def transpile_to_hardware_target(
    circuit: QuantumCircuit,
    optimization_level: int = 1,
    seed_transpiler: int = 42,
) -> TranspilationRecord:
    """Transpiles a circuit against the hardware-like synthetic target and records structural changes.
    
    Args:
        circuit: Input abstract QuantumCircuit.
        optimization_level: Qiskit transpilation optimization level (default 1).
        seed_transpiler: Deterministic seed for reproducible layout and routing.
        
    Returns:
        TranspilationRecord containing detailed structural comparisons.
    """
    qubits_before = circuit.num_qubits
    depth_before = circuit.depth()
    ops_before = dict(circuit.count_ops())
    one_q_before, two_q_before, swap_before = count_gate_categories(circuit)

    # Synthetic target with at least the circuit's qubit count
    target_qubits = max(qubits_before, 4)
    cmap, basis_gates, target_label = get_hardware_like_synthetic_target(target_qubits)

    # Initial layout fixed to consecutive physical qubits [0, 1, 2, ...] to rigorously test routing
    initial_layout = list(range(qubits_before))

    transpiled = transpile(
        circuit,
        coupling_map=cmap,
        basis_gates=basis_gates,
        initial_layout=initial_layout,
        optimization_level=optimization_level,
        seed_transpiler=seed_transpiler,
    )

    qubits_after = transpiled.num_qubits
    depth_after = transpiled.depth()
    ops_after = dict(transpiled.count_ops())
    one_q_after, two_q_after, swap_after = count_gate_categories(transpiled)

    # Count CX overhead attributed to routing/swap if CX increased
    # A single SWAP decomposes into 3 CX gates in the native basis
    cx_diff = ops_after.get("cx", 0) - ops_before.get("cx", 0)
    inferred_swaps = max(0, cx_diff // 3)

    return TranspilationRecord(
        target_label=target_label,
        optimization_level=optimization_level,
        qubits_before=qubits_before,
        qubits_after=qubits_after,
        depth_before=depth_before,
        depth_after=depth_after,
        ops_before=ops_before,
        ops_after=ops_after,
        one_qubit_gates_before=one_q_before,
        one_qubit_gates_after=one_q_after,
        two_qubit_gates_before=two_q_before,
        two_qubit_gates_after=two_q_after,
        swap_gates_inserted=inferred_swaps,
        transpiled_circuit=transpiled,
    )
