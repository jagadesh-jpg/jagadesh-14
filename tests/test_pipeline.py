"""Automated verification tests for noise modeling, ZNE, transpilation, and metrics."""
import pytest
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from src.circuits import get_benchmark_suite
from src.circuits.bell import create_bell_circuit
from src.circuits.ghz import create_ghz_circuit
from src.noise import build_noise_model, get_noise_profile
from src.mitigation.zne import fold_gates_at_scale, apply_zne
from src.metrics.fidelity import (
    total_variation_distance,
    hellinger_fidelity,
    calculate_relative_error_reduction,
    compute_all_metrics,
)
from src.execution.transpile_profiler import transpile_to_hardware_target
from src.benchmarking.benchmark import compute_classical_exact_distribution, compute_statevector_memory_bytes


def test_zne_gate_folding_preserves_noiseless_state():
    """Validates that for lambda=1 and lambda=3, gate folding preserves ideal state distribution exactly."""
    qc = create_bell_circuit(measure=True)
    folded_1 = fold_gates_at_scale(qc, scale_factor=1)
    folded_3 = fold_gates_at_scale(qc, scale_factor=3)

    sim = AerSimulator()
    res_orig = sim.run(qc, shots=4000, seed_simulator=42).result().get_counts()
    res_f1 = sim.run(folded_1, shots=4000, seed_simulator=42).result().get_counts()
    res_f3 = sim.run(folded_3, shots=4000, seed_simulator=42).result().get_counts()

    # Under noiseless simulation with fixed seed, counts should be identical
    assert res_orig == res_f1 == res_f3


def test_transpilation_synthetic_target_routing_overhead():
    """Validates that non-adjacent operations require SWAP insertion and depth expansion."""
    from src.circuits.benchmark import create_long_range_entangled_circuit
    qc = create_long_range_entangled_circuit(n_qubits=3, measure=True)
    rec = transpile_to_hardware_target(qc, optimization_level=1, seed_transpiler=42)

    assert rec.depth_after > rec.depth_before
    assert rec.two_qubit_gates_after > rec.two_qubit_gates_before
    assert rec.swap_gates_inserted >= 1


def test_metric_mathematical_consistency():
    """Validates TVD, Hellinger fidelity, and relative error reduction bounds."""
    p_ideal = {"00": 0.5, "11": 0.5}
    p_noisy = {"00": 0.45, "11": 0.45, "01": 0.05, "10": 0.05}
    p_mit = {"00": 0.48, "11": 0.48, "01": 0.02, "10": 0.02}

    metrics = compute_all_metrics(p_ideal, p_noisy, p_mit)
    assert 0.0 <= metrics["fidelity_noisy"] <= 1.0
    assert 0.0 <= metrics["fidelity_mitigated"] <= 1.0
    assert metrics["fidelity_mitigated"] > metrics["fidelity_noisy"]
    assert metrics["relative_error_reduction_pct"] > 0.0
    assert metrics["infidelity_noisy"] == pytest.approx(1.0 - metrics["fidelity_noisy"])


def test_classical_reference_memory_scaling():
    """Validates classical statevector memory scaling formula: 2^N * 16 bytes."""
    assert compute_statevector_memory_bytes(3) == 128
    assert compute_statevector_memory_bytes(10) == 1024 * 16
    assert compute_statevector_memory_bytes(20) == 1048576 * 16


def test_full_precision_artifact_consistency():
    """Validates that for all stored benchmark results, the relative error reduction
    calculated directly from full-precision (raw_infidelity - mit_infidelity)/raw_infidelity * 100
    strictly reproduces the stored relative_error_reduction_pct.
    """
    import json
    import os

    json_path = os.path.join("results", "processed", "benchmark_results.json")
    assert os.path.exists(json_path), "benchmark_results.json does not exist"

    with open(json_path, "r") as f:
        results = json.load(f)

    assert len(results) > 0, "No benchmark results stored"

    for entry in results:
        m = entry["metrics"]
        raw_fid = m["fidelity_noisy"]
        mit_fid = m["fidelity_mitigated"]
        raw_inf = m["infidelity_noisy"]
        mit_inf = m["infidelity_mitigated"]
        stored_gain = m["relative_error_reduction_pct"]

        # Check raw and mitigated infidelity
        calc_raw_inf = 1.0 - raw_fid
        calc_mit_inf = 1.0 - mit_fid
        assert raw_inf == pytest.approx(calc_raw_inf, abs=1e-15)
        assert mit_inf == pytest.approx(calc_mit_inf, abs=1e-15)

        # Calculate relative error reduction from full precision
        calc_gain = ((calc_raw_inf - calc_mit_inf) / calc_raw_inf) * 100.0
        assert stored_gain == pytest.approx(calc_gain, abs=1e-12)

