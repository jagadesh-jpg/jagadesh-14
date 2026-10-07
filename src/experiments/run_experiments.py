"""Core Experiment Runner and Visualization Generator.

Executes the end-to-end evidence-driven quantum noise engineering benchmark:
1. Target backend transpilation and profiling against a 'hardware-like synthetic target'
   (restricted linear nearest-neighbor topology + native transmon basis gates [cx, id, rz, sx, x]).
2. Ideal noiseless execution on transpiled circuit.
3. Realistic noisy simulation across Controlled Synthetic Noise Profiles (Low, Medium, High).
4. Zero-Noise Extrapolation (ZNE) error mitigation via digital unitary gate folding.
5. Extreme-noise stress test evaluating mitigation breakdown boundaries.
6. Quantitative fidelity, infidelity, and relative error reduction calculation.
7. Classical reference memory scaling and runtime analysis.
8. Generates publication-ready figures and JSON/CSV summary records.
"""
import os
import json
import csv
import time
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import numpy as np

from src.circuits import get_benchmark_suite
from src.noise import get_noise_profile, build_noise_model, NOISE_PROFILES
from src.execution import (
    transpile_to_hardware_target,
    run_ideal_simulation,
    run_noisy_simulation,
    get_noisy_simulator,
)
from src.mitigation import apply_zne
from src.metrics import compute_all_metrics, normalize_counts
from src.benchmarking import compute_classical_exact_distribution


def run_single_experiment(
    circuit_name: str,
    circuit,
    noise_level: str = "medium",
    shots: int = 4096,
    optimization_level: int = 1,
    seed: int = 42,
) -> Dict[str, Any]:
    """Runs a complete benchmark experiment for a single circuit and synthetic noise profile."""
    print(f"  -> Testing '{circuit_name}' under '{noise_level}' noise...")
    
    # 1. Classical exact reference baseline and scaling analysis
    classical_data = compute_classical_exact_distribution(circuit)

    # 2. Transpile targeting 'hardware-like synthetic target'
    transpile_rec = transpile_to_hardware_target(
        circuit,
        optimization_level=optimization_level,
        seed_transpiler=seed,
    )
    transpiled_qc = transpile_rec.transpiled_circuit

    # 3. Build controlled synthetic noise model
    noise_model = build_noise_model(noise_level)

    # 4. Ideal (noiseless) reference simulation
    p_ideal, counts_ideal = run_ideal_simulation(
        transpiled_qc, shots=shots, seed_simulator=seed
    )

    # 5. Raw noisy simulation
    p_noisy, counts_noisy = run_noisy_simulation(
        transpiled_qc,
        noise_model=noise_model,
        shots=shots,
        seed_simulator=seed,
    )

    # 6. Zero-Noise Extrapolation (ZNE) Mitigation
    def noisy_executor(folded_qc):
        p_fold, _ = run_noisy_simulation(
            folded_qc,
            noise_model=noise_model,
            shots=shots,
            seed_simulator=seed,
        )
        return p_fold

    mitigated_dist, scale_dists = apply_zne(
        transpiled_qc,
        executor_fn=noisy_executor,
        scale_factors=[1, 3, 5],
        extrapolation_degree=1,
    )

    # 7. Quantitative metrics
    metrics = compute_all_metrics(p_ideal, p_noisy, mitigated_dist)

    return {
        "circuit_name": circuit_name,
        "noise_level": noise_level,
        "shots": shots,
        "transpilation": transpile_rec.to_dict(),
        "classical_reference": {
            "compute_time_sec": classical_data["classical_compute_time_sec"],
            "hilbert_dim": classical_data["hilbert_dimension"],
            "memory_bytes": classical_data["statevector_memory_bytes"],
            "scaling_analysis": classical_data["scaling_analysis"],
        },
        "distributions": {
            "ideal": p_ideal,
            "noisy": p_noisy,
            "mitigated": mitigated_dist,
            "scale_dists": {str(k): v for k, v in scale_dists.items()},
        },
        "raw_counts": {
            "ideal": counts_ideal,
            "noisy": counts_noisy,
        },
        "metrics": metrics,
    }


def run_extreme_stress_test(seed: int = 42) -> Dict[str, Any]:
    """Evaluates GHZ state under extreme synthetic decoherence (p2=20%, RO=15%) to honestly document ZNE breakdown."""
    from qiskit_aer.noise import depolarizing_error, ReadoutError, NoiseModel
    from src.circuits.ghz import create_ghz_circuit

    print("\n  -> Executing Extreme-Noise Stress Test on GHZ State (p2=20%, RO=15%)...")
    qc = create_ghz_circuit(n_qubits=3, measure=True)
    
    # Transpile to hardware-like synthetic target
    transpile_rec = transpile_to_hardware_target(qc, optimization_level=1, seed_transpiler=seed)
    transpiled_qc = transpile_rec.transpiled_circuit

    # Construct extreme noise model
    nm_extreme = NoiseModel()
    nm_extreme.add_all_qubit_quantum_error(depolarizing_error(0.08, 1), ["x", "sx", "rz", "h", "s", "t", "rx", "ry", "id"])
    nm_extreme.add_all_qubit_quantum_error(depolarizing_error(0.20, 2), ["cx"])
    nm_extreme.add_all_qubit_readout_error(ReadoutError([[0.85, 0.15], [0.15, 0.85]]))

    shots = 4096
    p_ideal, _ = run_ideal_simulation(transpiled_qc, shots=shots, seed_simulator=seed)
    p_noisy, _ = run_noisy_simulation(transpiled_qc, noise_model=nm_extreme, shots=shots, seed_simulator=seed)

    def extreme_executor(c):
        p, _ = run_noisy_simulation(c, noise_model=nm_extreme, shots=shots, seed_simulator=seed)
        return p

    p_mit, scale_dists = apply_zne(transpiled_qc, executor_fn=extreme_executor, scale_factors=[1, 3, 5], extrapolation_degree=1)
    metrics = compute_all_metrics(p_ideal, p_noisy, p_mit)

    return {
        "circuit_name": "ghz_state_3q",
        "noise_level": "extreme_stress_test",
        "shots": shots,
        "transpilation": transpile_rec.to_dict(),
        "classical_reference": compute_classical_exact_distribution(qc),
        "distributions": {
            "ideal": p_ideal,
            "noisy": p_noisy,
            "mitigated": p_mit,
            "scale_dists": {str(k): v for k, v in scale_dists.items()},
        },
        "raw_counts": {},
        "metrics": metrics,
    }


def generate_plots(results: List[Dict[str, Any]], output_dir: str):
    """Generates scientific figures with standard ASCII labels to prevent font warnings."""
    os.makedirs(output_dir, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    # -------------------------------------------------------------
    # Plot 1: Probability Distribution Comparison (Ideal vs Noisy vs Mitigated)
    # -------------------------------------------------------------
    for exp in results:
        if exp["noise_level"] == "medium":
            c_name = exp["circuit_name"]
            p_ideal = exp["distributions"]["ideal"]
            p_noisy = exp["distributions"]["noisy"]
            p_mit = exp["distributions"]["mitigated"]

            all_keys = sorted(list(set(p_ideal.keys()) | set(p_noisy.keys()) | set(p_mit.keys())))
            x = np.arange(len(all_keys))
            width = 0.25

            fig, ax = plt.subplots(figsize=(9, 5))
            ax.bar(x - width, [p_ideal.get(k, 0.0) for k in all_keys], width, label="Ideal Reference (Noiseless)", color="#10B981")
            ax.bar(x, [p_noisy.get(k, 0.0) for k in all_keys], width, label="Raw Noisy (Synthetic Aer)", color="#EF4444")
            ax.bar(x + width, [p_mit.get(k, 0.0) for k in all_keys], width, label="Mitigated (ZNE)", color="#3B82F6")

            ax.set_ylabel("Probability", fontsize=11, fontweight="bold")
            # Use ASCII notation |k> instead of unicode brackets to prevent font warnings
            ax.set_title(
                f"State Distribution Comparison: {c_name} (Medium Synthetic Noise)\n"
                f"Fidelity: Noisy={exp['metrics']['fidelity_noisy']:.4f} -> Mitigated={exp['metrics']['fidelity_mitigated']:.4f} "
                f"(Relative Error Reduction: {exp['metrics']['relative_error_reduction_pct']:+.2f}%)",
                fontsize=11, fontweight="bold"
            )
            ax.set_xticks(x)
            ax.set_xticklabels([f"|{k}>" for k in all_keys], fontsize=9)
            ax.legend(frameon=True)
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            
            save_path = os.path.join(output_dir, f"dist_comparison_{c_name}.png")
            plt.savefig(save_path, dpi=300)
            plt.close()

    # -------------------------------------------------------------
    # Plot 2: Fidelity Across Noise Regimes
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 5.5))
    # Filter to standard noise regimes (exclude extreme stress test from bar chart)
    std_results = [r for r in results if r["noise_level"] in ["low", "medium", "high"]]
    circuits = sorted(list(set(r["circuit_name"] for r in std_results)))
    
    x = np.arange(len(circuits))
    width = 0.25

    med_exps = {r["circuit_name"]: r for r in std_results if r["noise_level"] == "medium"}
    fid_noisy = [med_exps[c]["metrics"]["fidelity_noisy"] for c in circuits]
    fid_mit = [med_exps[c]["metrics"]["fidelity_mitigated"] for c in circuits]

    rects1 = ax.bar(x - width/2, fid_noisy, width, label="Raw Noisy Fidelity", color="#EF4444")
    rects2 = ax.bar(x + width/2, fid_mit, width, label="ZNE Mitigated Fidelity", color="#3B82F6")

    for rect in rects1:
        h = rect.get_height()
        ax.annotate(f"{h:.3f}", xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3),
                    textcoords="offset points", ha='center', va='bottom', fontsize=9)
    for rect in rects2:
        h = rect.get_height()
        ax.annotate(f"{h:.3f}", xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3),
                    textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight="bold")

    ax.set_ylabel("Classical Fidelity (F_cl)", fontsize=11, fontweight="bold")
    ax.set_title("Classical Fidelity Comparison Under Controlled Synthetic Noise (Medium)", fontsize=12, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(circuits, fontsize=10)
    ax.set_ylim(0.0, 1.15)
    ax.axhline(1.0, color='gray', linestyle=':', label='Ideal (F=1.0)')
    ax.legend(frameon=True, loc="lower right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fidelity_mitigation_benchmark.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # Plot 3: Relative Error Reduction (%) across Circuits and Noise Levels
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 5.5))
    noise_regimes = ["low", "medium", "high"]
    bar_width = 0.25
    x = np.arange(len(circuits))

    for i, noise_lvl in enumerate(noise_regimes):
        gains = [
            next(r["metrics"]["relative_error_reduction_pct"] for r in std_results if r["circuit_name"] == c and r["noise_level"] == noise_lvl)
            for c in circuits
        ]
        rects = ax.bar(x + (i - 1) * bar_width, gains, bar_width, label=f"Profile: {noise_lvl.capitalize()}")
        for rect in rects:
            h = rect.get_height()
            pos = 3 if h >= 0 else -10
            ax.annotate(f"{h:.1f}%", xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, pos),
                        textcoords="offset points", ha='center', va='bottom', fontsize=8)

    ax.set_ylabel("Relative Error Reduction (%)", fontsize=11, fontweight="bold")
    ax.set_title("Relative Error Reduction Across Controlled Synthetic Noise Profiles\nGain = ((Error_noisy - Error_mitigated) / Error_noisy) * 100%", fontsize=11, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(circuits, fontsize=10)
    ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
    ax.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "mitigation_gain_by_noise_regime.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # Plot 4: Transpilation Structural Profile (Depth and CX Gate Impact)
    # -------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    sample_exps = [next(r for r in std_results if r["circuit_name"] == c) for c in circuits]

    depth_before = [e["transpilation"]["depth_before"] for e in sample_exps]
    depth_after = [e["transpilation"]["depth_after"] for e in sample_exps]
    two_q_before = [e["transpilation"]["two_qubit_gates_before"] for e in sample_exps]
    two_q_after = [e["transpilation"]["two_qubit_gates_after"] for e in sample_exps]

    ind = np.arange(len(circuits))
    w = 0.35

    ax1.bar(ind - w/2, depth_before, w, label="Original Abstract Depth", color="#6366F1")
    ax1.bar(ind + w/2, depth_after, w, label="Target Transpiled Depth", color="#EC4899")
    ax1.set_ylabel("Circuit Depth", fontsize=10, fontweight="bold")
    ax1.set_title("Depth Expansion under Hardware-like Target", fontsize=11, fontweight="bold")
    ax1.set_xticks(ind)
    ax1.set_xticklabels(circuits, fontsize=9, rotation=15)
    ax1.legend()

    ax2.bar(ind - w/2, two_q_before, w, label="Original 2Q Gates (CX)", color="#6366F1")
    ax2.bar(ind + w/2, two_q_after, w, label="Target 2Q Gates (CX)", color="#EC4899")
    ax2.set_ylabel("2-Qubit Gate Count", fontsize=10, fontweight="bold")
    ax2.set_title("2-Qubit Operations (Including SWAP Overheads)", fontsize=11, fontweight="bold")
    ax2.set_xticks(ind)
    ax2.set_xticklabels(circuits, fontsize=9, rotation=15)
    ax2.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "transpilation_structural_profile.png"), dpi=300)
    plt.close()


def run_full_suite() -> List[Dict[str, Any]]:
    """Executes the full benchmark experiment suite including synthetic target transpilation and stress testing."""
    print("=" * 75)
    print("QISKIT FALL FEST 2026: INDUSTRY CHALLENGE I7 NOISE BENCHMARK SUITE")
    print("=" * 75)

    circuits = get_benchmark_suite()
    noise_regimes = ["low", "medium", "high"]
    shots = 4096
    results = []

    for c_name, qc in circuits.items():
        print(f"\nBenchmarking Circuit: {c_name} (Qubits: {qc.num_qubits}, Base Depth: {qc.depth()})")
        for noise_lvl in noise_regimes:
            res = run_single_experiment(
                circuit_name=c_name,
                circuit=qc,
                noise_level=noise_lvl,
                shots=shots,
                optimization_level=1,
            )
            results.append(res)
            m = res["metrics"]
            t = res["transpilation"]
            print(
                f"    [Depth: {t['depth_before']}->{t['depth_after']}, 2Q: {t['two_qubit_gates_before']}->{t['two_qubit_gates_after']}] "
                f"Raw Fid: {m['fidelity_noisy']:.4f} | Mit Fid: {m['fidelity_mitigated']:.4f} | "
                f"Rel Err Reduction: {m['relative_error_reduction_pct']:+.2f}%"
            )

    # Execute extreme noise stress test (honest limitation preservation)
    stress_res = run_extreme_stress_test()
    results.append(stress_res)
    sm = stress_res["metrics"]
    print(
        f"    [STRESS TEST BREAKDOWN] Raw Fid: {sm['fidelity_noisy']:.4f} | "
        f"Mit Fid: {sm['fidelity_mitigated']:.4f} | Rel Err Reduction: {sm['relative_error_reduction_pct']:+.2f}%"
    )

    # Save results
    raw_dir = os.path.join("results", "raw")
    proc_dir = os.path.join("results", "processed")
    fig_dir = os.path.join("results", "figures")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(proc_dir, exist_ok=True)
    os.makedirs(fig_dir, exist_ok=True)

    json_path = os.path.join(proc_dir, "benchmark_results.json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[Saved JSON]: {json_path}")

    csv_path = os.path.join(proc_dir, "benchmark_summary.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "circuit_name", "noise_level", "qubits_before", "qubits_after",
            "depth_before", "depth_after", "one_q_before", "one_q_after",
            "two_q_before", "two_q_after", "swap_inserted", "shots",
            "fidelity_ideal", "fidelity_noisy", "fidelity_mitigated",
            "infidelity_noisy", "infidelity_mitigated", "relative_error_reduction_pct",
            "tvd_noisy", "tvd_mitigated", "classical_time_sec", "statevector_memory_bytes"
        ])
        for r in results:
            t = r["transpilation"]
            m = r["metrics"]
            c = r["classical_reference"]
            writer.writerow([
                r["circuit_name"], r["noise_level"], t["qubits_before"], t["qubits_after"],
                t["depth_before"], t["depth_after"], t["one_qubit_gates_before"], t["one_qubit_gates_after"],
                t["two_qubit_gates_before"], t["two_qubit_gates_after"], t["swap_gates_inserted"],
                r["shots"],
                f"{m['fidelity_ideal']:.1f}",
                repr(m['fidelity_noisy']),
                repr(m['fidelity_mitigated']),
                repr(m['infidelity_noisy']),
                repr(m['infidelity_mitigated']),
                repr(m['relative_error_reduction_pct']),
                repr(m['tvd_noisy']),
                repr(m['tvd_mitigated']),
                f"{c.get('compute_time_sec', c.get('classical_compute_time_sec', 0.0)):.8f}",
                c.get("memory_bytes", c.get("statevector_memory_bytes", 0))
            ])
    print(f"[Saved CSV]: {csv_path}")

    # Generate figures
    generate_plots(results, fig_dir)
    print(f"[Saved Figures in]: {fig_dir}")
    print("=" * 75)
    print("BENCHMARK SUITE COMPLETED SUCCESSFULLY.")
    print("=" * 75)
    return results


if __name__ == "__main__":
    run_full_suite()
