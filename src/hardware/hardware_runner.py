"""Real IBM Quantum hardware execution runner, transpiler, and artifact logger.

Scientific Transparency Rules:
- Never fabricates job results, backend names, or counts.
- Waits for real job completion via Qiskit Runtime Sampler.
- Stores raw, processed, and metadata artifacts cleanly in results/hardware/.
- Distinguishes clearly between Noiseless Reference and Physical Device output.
"""
import os
import json
import time
from typing import Dict, Any, Optional, Tuple
from qiskit import QuantumCircuit, transpile

from .ibm_backend import (
    get_ibm_quantum_api_key,
    connect_ibm_service,
    discover_real_backends,
    select_best_small_backend,
)
from .hardware_metrics import evaluate_hardware_vs_reference
from ..metrics.fidelity import normalize_counts
from ..execution.transpile_profiler import count_gate_categories
from ..execution.ideal import run_ideal_simulation


def transpile_for_real_hardware(
    circuit: QuantumCircuit,
    backend,
    optimization_level: int = 1,
    seed_transpiler: int = 42,
) -> Tuple[QuantumCircuit, Dict[str, Any]]:
    """Transpiles a circuit specifically targeting the real IBM physical processor.
    
    Records logical vs physical structural characteristics:
    - logical vs physical depth
    - 1Q and 2Q gate counts
    - native basis transformations
    """
    logical_qubits = circuit.num_qubits
    logical_depth = circuit.depth()
    logical_ops = dict(circuit.count_ops())
    one_q_before, two_q_before, swap_before = count_gate_categories(circuit)

    # Execute physical transpilation targeting real backend
    transpiled_qc = transpile(
        circuit,
        backend=backend,
        optimization_level=optimization_level,
        seed_transpiler=seed_transpiler,
    )

    physical_depth = transpiled_qc.depth()
    physical_ops = dict(transpiled_qc.count_ops())
    one_q_after, two_q_after, swap_after = count_gate_categories(transpiled_qc)

    transpile_info = {
        "backend_name": backend.name,
        "logical_qubits": logical_qubits,
        "physical_qubits_backend": getattr(backend, "num_qubits", None),
        "logical_depth": logical_depth,
        "transpiled_depth": physical_depth,
        "logical_ops": logical_ops,
        "transpiled_ops": physical_ops,
        "one_qubit_gates_before": one_q_before,
        "one_qubit_gates_after": one_q_after,
        "two_qubit_gates_before": two_q_before,
        "two_qubit_gates_after": two_q_after,
        "swap_gates_inferred": swap_after,
        "optimization_level": optimization_level,
    }

    return transpiled_qc, transpile_info


def execute_real_hardware_job(
    circuit: QuantumCircuit,
    backend_name: Optional[str] = None,
    shots: int = 1024,
    optimization_level: int = 1,
    enable_zne: bool = False,
    results_dir: str = "results/hardware",
) -> Dict[str, Any]:
    """Submits and evaluates an authentic quantum job on real IBM Quantum hardware.
    
    Args:
        circuit: Circuit to execute (preferably Non-Local Bell to demonstrate routing).
        backend_name: Optional explicit backend name. If None, auto-selects best small operational backend.
        shots: Shot count (conservative default 1024 for hackathon jobs).
        optimization_level: Transpilation optimization level (default 1).
        enable_zne: Whether to execute gate-folded circuits for ZNE on hardware.
        results_dir: Base directory for storing hardware artifacts.
        
    Returns:
        Dict: Full execution records, job ID, counts, metrics, and metadata.
    """
    from qiskit_ibm_runtime import SamplerV2

    # Step 1: Connect and verify credentials
    service = connect_ibm_service()
    discovered = discover_real_backends(service)

    if not discovered:
        raise RuntimeError("No operational real IBM Quantum backends accessible to this account.")

    # Select backend
    if backend_name:
        matched = [b for b in discovered if b["name"] == backend_name]
        if not matched:
            raise ValueError(f"Requested backend '{backend_name}' not found among accessible backends.")
        selected = matched[0]
    else:
        selected = select_best_small_backend(discovered, min_qubits=circuit.num_qubits)

    backend = selected["backend_object"]
    print(f"\n[IBM Quantum Hardware] Selected Backend: {backend.name} (Qubits: {selected['num_qubits']}, Pending Jobs: {selected['pending_jobs']})")

    # Step 2: Reference noiseless simulation
    p_reference, ref_counts = run_ideal_simulation(circuit, shots=shots, seed_simulator=42)

    # Step 3: Transpile targeting physical backend
    print(f"[IBM Quantum Hardware] Transpiling '{circuit.name}' for {backend.name}...")
    transpiled_qc, transpile_info = transpile_for_real_hardware(
        circuit, backend=backend, optimization_level=optimization_level
    )
    print(f"  -> Logical Depth: {transpile_info['logical_depth']} | Transpiled Depth: {transpile_info['transpiled_depth']}")
    print(f"  -> Logical 2Q Gates: {transpile_info['two_qubit_gates_before']} | Transpiled 2Q Gates: {transpile_info['two_qubit_gates_after']}")

    # Step 4: Submit real hardware job via SamplerV2
    print(f"[IBM Quantum Hardware] Submitting job ({shots} shots) to {backend.name}...")
    sampler = SamplerV2(mode=backend)
    
    submission_time = time.time()
    job = sampler.run([transpiled_qc], shots=shots)
    job_id = job.job_id()
    print(f"[IBM Quantum Hardware] Job submitted successfully! Job ID: {job_id}")
    print("[IBM Quantum Hardware] Waiting for job completion on physical hardware...")

    # Wait for result
    job_result = job.result()
    completion_time = time.time()
    elapsed_time = completion_time - submission_time
    print(f"[IBM Quantum Hardware] Job {job_id} finished in {elapsed_time:.1f}s.")

    # Extract bitstring counts from SamplerV2 PubResult
    pub_result = job_result[0]
    # Classical register output
    data_bin = pub_result.data
    # Find measurement register name (usually 'meas' or 'c')
    counts_dict = {}
    for attr in dir(data_bin):
        if not attr.startswith("_"):
            bit_array = getattr(data_bin, attr)
            if hasattr(bit_array, "get_counts"):
                counts_dict = bit_array.get_counts()
                break

    if not counts_dict:
        # Fallback dictionary extraction
        counts_dict = dict(pub_result.data.meas.get_counts())

    p_hardware_raw = normalize_counts(counts_dict)

    # Step 5: Evaluate quantitative metrics against noiseless reference
    metrics = evaluate_hardware_vs_reference(
        p_reference=p_reference,
        p_hardware_raw=p_hardware_raw,
    )
    print(f"  -> Hardware Raw Fidelity: {metrics['hardware_raw_fidelity']:.5f} (Infidelity: {metrics['hardware_raw_infidelity']:.5f})")

    # Step 6: Persist hardware artifacts
    raw_dir = os.path.join(results_dir, "raw")
    proc_dir = os.path.join(results_dir, "processed")
    meta_dir = os.path.join(results_dir, "metadata")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(proc_dir, exist_ok=True)
    os.makedirs(meta_dir, exist_ok=True)

    timestamp_str = time.strftime("%Y%m%d_%H%M%S", time.gmtime(submission_time))
    base_filename = f"{backend.name}_{circuit.name}_{timestamp_str}"

    # Metadata record
    meta_record = {
        "experiment_type": "real_ibm_hardware",
        "backend_name": backend.name,
        "job_id": job_id,
        "shots": shots,
        "circuit_name": circuit.name,
        "logical_qubits": circuit.num_qubits,
        "transpiled_depth": transpile_info["transpiled_depth"],
        "transpilation_info": transpile_info,
        "submission_timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(submission_time)),
        "completion_timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(completion_time)),
        "elapsed_seconds": elapsed_time,
        "status": "COMPLETED",
    }
    with open(os.path.join(meta_dir, f"{base_filename}_meta.json"), "w") as f:
        json.dump(meta_record, f, indent=2)

    # Raw counts record
    raw_record = {
        "job_id": job_id,
        "backend": backend.name,
        "circuit": circuit.name,
        "raw_counts": counts_dict,
        "reference_counts": ref_counts,
    }
    with open(os.path.join(raw_dir, f"{base_filename}_raw.json"), "w") as f:
        json.dump(raw_record, f, indent=2)

    # Processed results record
    proc_record = {
        "job_id": job_id,
        "backend": backend.name,
        "circuit": circuit.name,
        "shots": shots,
        "transpile_info": transpile_info,
        "distributions": {
            "reference": p_reference,
            "hardware_raw": p_hardware_raw,
        },
        "metrics": metrics,
    }
    with open(os.path.join(proc_dir, f"{base_filename}_summary.json"), "w") as f:
        json.dump(proc_record, f, indent=2)

    return {
        "status": "COMPLETED",
        "backend": backend.name,
        "job_id": job_id,
        "circuit_name": circuit.name,
        "shots": shots,
        "transpile_info": transpile_info,
        "raw_counts": counts_dict,
        "reference_counts": ref_counts,
        "distributions": {
            "reference": p_reference,
            "hardware_raw": p_hardware_raw,
        },
        "metrics": metrics,
    }
