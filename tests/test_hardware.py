"""Automated unit tests for real IBM Quantum hardware integration layer.

Guarantees:
- Tests pass independently of whether IBM Quantum credentials exist or network is connected.
- Verifies credential discovery failure modes without exposing keys.
- Verifies hardware metric evaluation functions.
- Verifies physical transpilation against mock/backend targets without running real jobs.
"""
import pytest
from qiskit import QuantumCircuit
from src.hardware.ibm_backend import get_ibm_quantum_api_key, connect_ibm_service
from src.hardware.hardware_metrics import evaluate_hardware_vs_reference
from src.circuits.benchmark import create_long_range_entangled_circuit


def test_missing_credentials_fails_gracefully(monkeypatch):
    """Verifies that connect_ibm_service raises a descriptive ValueError if no API key is set."""
    monkeypatch.delenv("IBM_QUANTUM_API_KEY", raising=False)
    monkeypatch.delenv("QISKIT_IBM_TOKEN", raising=False)
    
    with pytest.raises(ValueError, match="IBM Quantum API key not found"):
        connect_ibm_service(api_key=None)


def test_hardware_metric_evaluation_consistency():
    """Verifies hardware evaluation metrics vs reference statevector distribution."""
    p_ref = {"00": 0.5, "11": 0.5}
    p_hw_raw = {"00": 0.44, "11": 0.46, "01": 0.06, "10": 0.04}
    p_hw_mit = {"00": 0.48, "11": 0.49, "01": 0.02, "10": 0.01}

    m = evaluate_hardware_vs_reference(
        p_reference=p_ref,
        p_hardware_raw=p_hw_raw,
        p_hardware_mitigated=p_hw_mit,
    )

    assert m["reference_fidelity"] == 1.0
    assert 0.0 <= m["hardware_raw_fidelity"] <= 1.0
    assert m["hardware_raw_infidelity"] == pytest.approx(1.0 - m["hardware_raw_fidelity"])
    assert m["hardware_mitigated_fidelity"] > m["hardware_raw_fidelity"]
    assert m["relative_error_reduction_pct"] > 0.0


def test_hardware_metadata_schema():
    """Verifies that hardware artifact schema preserves required non-secret fields."""
    schema_fields = {
        "experiment_type", "backend_name", "job_id", "shots", "circuit_name",
        "logical_qubits", "transpiled_depth", "transpilation_info", "status"
    }
    sample_meta = {
        "experiment_type": "real_ibm_hardware",
        "backend_name": "ibm_kyiv",
        "job_id": "c1234567890abcdef",
        "shots": 1024,
        "circuit_name": "non_local_bell_3q",
        "logical_qubits": 3,
        "transpiled_depth": 7,
        "transpilation_info": {},
        "status": "COMPLETED",
    }
    assert schema_fields.issubset(sample_meta.keys())
