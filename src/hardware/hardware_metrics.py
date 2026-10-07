"""Quantitative metrics for real IBM Quantum hardware comparison against noiseless reference."""
from typing import Dict, Any
import numpy as np

from ..metrics.fidelity import (
    normalize_counts,
    hellinger_fidelity,
    total_variation_distance,
    hellinger_distance,
    calculate_relative_error_reduction,
)


def evaluate_hardware_vs_reference(
    p_reference: Dict[str, float],
    p_hardware_raw: Dict[str, float],
    p_hardware_mitigated: Dict[str, float] = None,
) -> Dict[str, Any]:
    """Calculates fidelity and error metrics comparing physical hardware results to the noiseless reference distribution.
    
    Terminology & Scientific Distinction:
    - REFERENCE: Noiseless statevector simulation (Fidelity = 1.0).
    - HARDWARE RAW: Physical IBM Quantum hardware execution.
    - HARDWARE MITIGATED (optional): Real hardware execution post-processed with error mitigation.
    
    Args:
        p_reference: Empirical or exact probability distribution of noiseless reference.
        p_hardware_raw: Measured empirical probability distribution from physical device.
        p_hardware_mitigated: Optional mitigated empirical distribution.
        
    Returns:
        Dict of quantitative fidelity, infidelity, and distance metrics.
    """
    fid_raw = hellinger_fidelity(p_reference, p_hardware_raw)
    infid_raw = 1.0 - fid_raw
    tvd_raw = total_variation_distance(p_reference, p_hardware_raw)
    hellinger_dist_raw = hellinger_distance(p_reference, p_hardware_raw)

    metrics = {
        "reference_fidelity": 1.0,
        "hardware_raw_fidelity": fid_raw,
        "hardware_raw_infidelity": infid_raw,
        "hardware_raw_tvd": tvd_raw,
        "hardware_raw_hellinger_dist": hellinger_dist_raw,
    }

    if p_hardware_mitigated is not None:
        fid_mit = hellinger_fidelity(p_reference, p_hardware_mitigated)
        infid_mit = 1.0 - fid_mit
        tvd_mit = total_variation_distance(p_reference, p_hardware_mitigated)
        hellinger_dist_mit = hellinger_distance(p_reference, p_hardware_mitigated)
        rel_error_red = calculate_relative_error_reduction(infid_raw, infid_mit)

        metrics.update({
            "hardware_mitigated_fidelity": fid_mit,
            "hardware_mitigated_infidelity": infid_mit,
            "hardware_mitigated_tvd": tvd_mit,
            "hardware_mitigated_hellinger_dist": hellinger_dist_mit,
            "relative_error_reduction_pct": rel_error_red,
            "fidelity_delta": fid_mit - fid_raw,
        })

    return metrics
