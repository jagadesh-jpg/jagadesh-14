"""Command-line runner for Real IBM Quantum Hardware validation.

Usage:
    python -m src.hardware.run_hardware [--shots SHOTS] [--backend BACKEND_NAME]
"""
import sys
import argparse
from src.hardware.ibm_backend import (
    get_ibm_quantum_api_key,
    connect_ibm_service,
    discover_real_backends,
    select_best_small_backend,
)
from src.hardware.hardware_runner import execute_real_hardware_job
from src.circuits.benchmark import create_long_range_entangled_circuit


def main():
    parser = argparse.ArgumentParser(description="Real IBM Quantum Hardware Validation Runner")
    parser.add_argument("--shots", type=int, default=1024, help="Measurement shots (default: 1024)")
    parser.add_argument("--backend", type=str, default=None, help="Target IBM physical backend name")
    parser.add_argument("--check-only", action="store_true", help="Only check credentials and discover backends without submitting a job")
    args = parser.parse_args()

    print("=" * 75)
    print("IBM QUANTUM REAL HARDWARE VALIDATION LAYER")
    print("=" * 75)

    api_key = get_ibm_quantum_api_key()
    if not api_key:
        print("\n[STOP CONDITION TRIGGERED: MISSING CREDENTIALS]")
        print("No IBM Quantum API key was detected in 'IBM_QUANTUM_API_KEY' or '.env'.")
        print("\nTo enable authentic hardware execution:")
        print("  1. Create a local '.env' file in this directory with:")
        print("     IBM_QUANTUM_API_KEY=your_actual_ibm_api_key_here")
        print("  2. (Note: '.env' is automatically gitignored and will never be committed).")
        print("  3. Run this command again: python -m src.hardware.run_hardware")
        print("\nPer hackathon rules and scientific honesty, hardware execution is marked:")
        print("STATUS: NOT EXECUTED (Awaiting user credentials)")
        print("=" * 75)
        sys.exit(0)

    try:
        service = connect_ibm_service(api_key=api_key)
        backends = discover_real_backends(service)
        print(f"\n[Connection Successful] Discovered {len(backends)} accessible physical backend(s):")
        for b in backends:
            print(f"  * {b['name']} (Qubits: {b['num_qubits']}, Operational: {b['operational']}, Queue: {b['pending_jobs']})")

        if args.check_only:
            # Select target circuit: Non-Local Bell (3Q)
            qc = create_long_range_entangled_circuit(n_qubits=3, measure=True)
            selected = select_best_small_backend(backends, min_qubits=qc.num_qubits)
            target_backend = selected["backend_object"]
            print(f"\n[Check-Only Mode] Recommended Backend: {target_backend.name}")
            print(f"  * Physical Qubits: {selected['num_qubits']}")
            print(f"  * Operational: {selected['operational']}")
            print(f"  * Pending Queue: {selected['pending_jobs']}")
            print(f"\n[Check-Only Mode] Performing LOCAL transpilation test against {target_backend.name} (NO JOB WILL BE SUBMITTED)...")

            from src.hardware.hardware_runner import transpile_for_real_hardware
            transpiled_qc, transpile_info = transpile_for_real_hardware(
                circuit=qc,
                backend=target_backend,
                optimization_level=1,
            )
            print("  * Local Transpilation: SUCCESS")
            print(f"  * Circuit: {qc.name}")
            print(f"  * Logical Depth: {transpile_info['logical_depth']} -> Real Backend Transpiled Depth: {transpile_info['transpiled_depth']}")
            print(f"  * Logical 1Q Gates: {transpile_info['one_qubit_gates_before']} -> Transpiled 1Q Gates: {transpile_info['one_qubit_gates_after']}")
            print(f"  * Logical 2Q Gates: {transpile_info['two_qubit_gates_before']} -> Transpiled 2Q Gates: {transpile_info['two_qubit_gates_after']}")
            print(f"  * Inferred SWAP Gates: {transpile_info['swap_gates_inferred']}")
            print(f"  * Transpiled Operations: {transpile_info['transpiled_ops']}")
            print("\nCheck-only verification complete. NO QUANTUM JOB WAS SUBMITTED.")
            print("Job ID: NONE — CHECK-ONLY MODE")
            print("=" * 75)
            sys.exit(0)

        # Select target circuit: Non-Local Bell (3Q)
        qc = create_long_range_entangled_circuit(n_qubits=3, measure=True)
        print(f"\nExecuting circuit: '{qc.name}' (demonstrating physical topology routing)")

        result = execute_real_hardware_job(
            circuit=qc,
            backend_name=args.backend,
            shots=args.shots,
            results_dir="results/hardware",
        )

        m = result["metrics"]
        print("\n" + "=" * 75)
        print("HARDWARE JOB COMPLETED SUCCESSFULLY")
        print(f"Backend:           {result['backend']}")
        print(f"Job ID:            {result['job_id']}")
        print(f"Hardware Fidelity: {m['hardware_raw_fidelity']:.5f}")
        print(f"Infidelity:        {m['hardware_raw_infidelity']:.5f}")
        print(f"TVD Distance:      {m['hardware_raw_tvd']:.5f}")
        print("Artifacts saved in: results/hardware/")
        print("=" * 75)

    except Exception as e:
        print(f"\n[Hardware Execution Error]: {str(e)}")
        print("STATUS: FAILED / NOT EXECUTED")
        sys.exit(1)


if __name__ == "__main__":
    main()
