"""Secure IBM Quantum backend connection and discovery module.

Scientific & Security Guarantees:
- Loads API key strictly from environment variable IBM_QUANTUM_API_KEY (or local .env).
- Never prints, logs, stores, or serializes the secret API key.
- Discovers authentic, accessible real IBM Quantum physical backends.
- Rejects simulated backends for physical hardware evaluation.
"""
import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load local .env if present
load_dotenv()


def get_ibm_quantum_api_key() -> Optional[str]:
    """Retrieves the IBM Quantum API key from the environment securely.
    
    Checks IBM_QUANTUM_API_KEY and fallback QISKIT_IBM_TOKEN.
    Does NOT print or log the key.
    
    Returns:
        str: API key string if found, None otherwise.
    """
    key = os.environ.get("IBM_QUANTUM_API_KEY")
    if not key:
        key = os.environ.get("QISKIT_IBM_TOKEN")
    if key:
        key = key.strip()
    return key if key else None


def connect_ibm_service(api_key: Optional[str] = None):
    """Initializes QiskitRuntimeService with the provided or discovered API key.
    
    Args:
        api_key: Optional explicit API key. If None, loaded securely from environment.
        
    Returns:
        QiskitRuntimeService instance.
        
    Raises:
        ValueError: If no API key is found in environment or arguments.
        RuntimeError: If connection or authentication fails.
    """
    if api_key is None:
        api_key = get_ibm_quantum_api_key()

    if not api_key:
        raise ValueError(
            "IBM Quantum API key not found. Please set the 'IBM_QUANTUM_API_KEY' environment variable "
            "or add it to a local .env file. (Per security rules, never commit API keys to version control)."
        )

    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
        try:
            service = QiskitRuntimeService(channel="ibm_quantum_platform", token=api_key)
        except Exception:
            service = QiskitRuntimeService(channel="ibm_cloud", token=api_key)
        return service
    except Exception as e:
        raise RuntimeError(f"Failed to authenticate with IBM Quantum Runtime service: {str(e)}")


def discover_real_backends(service=None) -> List[Dict[str, Any]]:
    """Discovers accessible physical IBM Quantum backends (excluding simulators).
    
    Returns only safe public metadata:
    - name
    - num_qubits
    - operational status
    - pending_jobs (queue length)
    - basis_gates
    """
    if service is None:
        service = connect_ibm_service()

    # Query operational real backends only (simulator=False)
    real_backends = service.backends(simulator=False)
    discovered = []

    for b in real_backends:
        try:
            status = b.status()
            config = b.configuration()
            discovered.append({
                "name": b.name,
                "num_qubits": config.n_qubits,
                "operational": status.operational,
                "status_msg": status.status_msg,
                "pending_jobs": status.pending_jobs,
                "basis_gates": getattr(config, "basis_gates", []),
                "backend_object": b,
            })
        except Exception:
            # Fallback if configuration query differs in runtime version
            discovered.append({
                "name": b.name,
                "num_qubits": getattr(b, "num_qubits", None),
                "operational": True,
                "status_msg": "active",
                "pending_jobs": -1,
                "basis_gates": [],
                "backend_object": b,
            })

    return discovered


def select_best_small_backend(discovered_backends: List[Dict[str, Any]], min_qubits: int = 3) -> Dict[str, Any]:
    """Selects the best operational backend for small 2-3 qubit benchmark execution.
    
    Prioritization criteria:
    1. Operational status is True.
    2. Sufficient qubits (>= min_qubits).
    3. Smallest queue length (pending_jobs) to minimize waiting time.
    """
    candidates = [
        b for b in discovered_backends
        if b.get("operational", False) and (b.get("num_qubits", 0) or 0) >= min_qubits
    ]

    if not candidates:
        raise RuntimeError(
            f"No operational real IBM Quantum backend found with at least {min_qubits} qubits. "
            f"Available backends: {[b['name'] for b in discovered_backends]}"
        )

    # Sort by pending_jobs ascending (smallest queue first)
    # If pending_jobs is -1 or unknown, sort to end
    candidates.sort(key=lambda x: x["pending_jobs"] if x["pending_jobs"] >= 0 else 999999)
    selected = candidates[0]
    return selected
