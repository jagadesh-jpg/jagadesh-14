"""Zero-Noise Extrapolation (ZNE) Error Mitigation Engine.

Implements Unitary Gate Folding (G -> G G^\dagger G) noise scaling
and linear / polynomial Richardson extrapolation to the zero-noise limit (lambda -> 0).
Fully compatible with modern Qiskit 1.x/2.x.
"""
from typing import Dict, List, Tuple, Optional
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import CircuitInstruction, Barrier, Measure


def fold_gates_at_scale(circuit: QuantumCircuit, scale_factor: int) -> QuantumCircuit:
    r"""Scales noise digitally using unitary gate folding: G \to G (G^\dagger G)^k.
    
    For an integer scale factor \lambda \in \{1, 3, 5, ...\}:
    - k = (\lambda - 1) // 2 folds are inserted.
    - If \lambda = 1, circuit is unchanged.
    - If \lambda = 3, each unitary gate G is replaced with G G^\dagger G.
    - If \lambda = 5, each unitary gate G is replaced with G G^\dagger G G^\dagger G.
    
    Barriers and measurements are preserved at the end and never folded.
    
    Args:
        circuit: Input QuantumCircuit (preferably transpiled).
        scale_factor: Odd integer >= 1 (1, 3, 5, etc.).
        
    Returns:
        QuantumCircuit: Noise-amplified circuit mathematically equivalent to the original.
    """
    if scale_factor < 1:
        raise ValueError("scale_factor must be >= 1")
    if scale_factor % 2 == 0:
        raise ValueError(f"scale_factor must be an odd integer (1, 3, 5,...), got {scale_factor}")

    k_folds = (scale_factor - 1) // 2
    if k_folds == 0:
        return circuit.copy()

    folded_circuit = circuit.copy_empty_like()

    # Separate unitary operations from measurements
    unitary_instructions: List[CircuitInstruction] = []
    measurement_instructions: List[CircuitInstruction] = []

    for inst in circuit.data:
        op_name = inst.operation.name
        if op_name in ["measure", "barrier"]:
            measurement_instructions.append(inst)
        else:
            unitary_instructions.append(inst)

    # Reconstruct circuit with gate folding
    for inst in unitary_instructions:
        folded_circuit.append(inst)
        op = inst.operation
        try:
            op_inv = op.inverse()
        except Exception:
            # If inverse not defined, skip folding this gate
            continue

        for _ in range(k_folds):
            folded_circuit.append(CircuitInstruction(op_inv, inst.qubits, inst.clbits))
            folded_circuit.append(CircuitInstruction(op, inst.qubits, inst.clbits))

    # Re-append measurements and barriers
    for inst in measurement_instructions:
        folded_circuit.append(inst)

    return folded_circuit


def extrapolate_polynomial(
    scale_factors: List[float],
    values_by_key: Dict[str, List[float]],
    degree: int = 1,
) -> Dict[str, float]:
    r"""Extrapolates noisy expectation values/probabilities to the zero-noise limit (\lambda \to 0).
    
    Uses polynomial / Richardson extrapolation:
    P(\lambda) = c_0 + c_1 \lambda + c_2 \lambda^2 + ...
    and estimates P(0) = c_0.
    
    Negative extrapolated probabilities are clipped to 0 and re-normalized.
    
    Args:
        scale_factors: List of noise scale factors (e.g. [1.0, 3.0, 5.0]).
        values_by_key: Mapping of outcome bitstring to list of measured probabilities at each scale.
        degree: Polynomial fit degree (1 = linear, 2 = quadratic).
        
    Returns:
        Dict[str, float]: Extrapolated and normalized zero-noise probability distribution.
    """
    x = np.array(scale_factors, dtype=float)
    extrapolated_unnormalized: Dict[str, float] = {}

    # Check available points for fit degree
    fit_degree = min(degree, len(scale_factors) - 1)
    if fit_degree < 1:
        fit_degree = 1

    for key, y_vals in values_by_key.items():
        y = np.array(y_vals, dtype=float)
        try:
            poly = np.polyfit(x, y, deg=fit_degree)
            val_at_zero = float(poly[-1])  # Constant term c_0 = P(\lambda=0)
        except Exception:
            # Fallback to scale=1 if fitting fails
            val_at_zero = float(y[0])

        # Physical boundary clipping
        extrapolated_unnormalized[key] = max(0.0, val_at_zero)

    # Re-normalize into valid probability distribution
    total = sum(extrapolated_unnormalized.values())
    if total <= 1e-12:
        # Uniform fallback if completely degenerate
        n = len(extrapolated_unnormalized)
        return {k: 1.0 / n for k in extrapolated_unnormalized}

    return {k: v / total for k, v in extrapolated_unnormalized.items()}


def apply_zne(
    circuit: QuantumCircuit,
    executor_fn,
    scale_factors: Optional[List[int]] = None,
    extrapolation_degree: int = 1,
) -> Tuple[Dict[str, float], Dict[int, Dict[str, float]]]:
    """Executes the complete Zero-Noise Extrapolation workflow.
    
    Args:
        circuit: Quantum circuit to execute and mitigate.
        executor_fn: Callable taking a QuantumCircuit and returning normalized probability dict {bitstring: prob}.
        scale_factors: List of noise scale factors (default: [1, 3, 5]).
        extrapolation_degree: Degree of extrapolation polynomial (default: 1, linear).
        
    Returns:
        mitigated_dist: Extrapolated probability distribution {bitstring: prob}.
        scale_dists: Measured probability distributions at each noise scale factor.
    """
    if scale_factors is None:
        scale_factors = [1, 3, 5]

    scale_dists: Dict[int, Dict[str, float]] = {}
    all_keys = set()

    # Step 1: Execute at each amplified noise scale
    for scale in scale_factors:
        scaled_qc = fold_gates_at_scale(circuit, scale)
        dist = executor_fn(scaled_qc)
        scale_dists[scale] = dist
        all_keys.update(dist.keys())

    # Step 2: Format data arrays for each outcome bitstring
    values_by_key: Dict[str, List[float]] = {k: [] for k in all_keys}
    for scale in scale_factors:
        for k in all_keys:
            values_by_key[k].append(scale_dists[scale].get(k, 0.0))

    # Step 3: Extrapolate to zero-noise limit lambda = 0
    mitigated_dist = extrapolate_polynomial(
        [float(s) for s in scale_factors],
        values_by_key,
        degree=extrapolation_degree,
    )

    return mitigated_dist, scale_dists
