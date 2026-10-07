"""Quantitative metrics for quantum state fidelity and probability distribution distances.

Terminology Standards:
- Fidelity (F_cl): Bhattacharyya / Classical fidelity in [0, 1].
- Infidelity / Error (epsilon): 1 - Fidelity in [0, 1].
- Relative Error Reduction (Gain %): Percentage by which mitigation reduces the error/infidelity:
      Gain = ((Error_noisy - Error_mitigated) / Error_noisy) * 100%
  Note: This is NEVER called a "fidelity increase %".
"""
from typing import Dict
import numpy as np


def normalize_counts(counts: Dict[str, int]) -> Dict[str, float]:
    """Converts raw shot counts to a normalized empirical probability distribution."""
    total_shots = sum(counts.values())
    if total_shots == 0:
        return {}
    return {k: v / total_shots for k, v in counts.items()}


def get_aligned_distributions(p_dist: Dict[str, float], q_dist: Dict[str, float]):
    """Aligns two discrete probability distributions over their common support."""
    all_keys = sorted(list(set(p_dist.keys()) | set(q_dist.keys())))
    p_vec = np.array([p_dist.get(k, 0.0) for k in all_keys], dtype=float)
    q_vec = np.array([q_dist.get(k, 0.0) for k in all_keys], dtype=float)
    return all_keys, p_vec, q_vec


def total_variation_distance(p_dist: Dict[str, float], q_dist: Dict[str, float]) -> float:
    r"""Total Variation Distance (TVD) between two probability distributions:
    TVD(P, Q) = 0.5 * \sum_x |P(x) - Q(x)| \in [0, 1].
    """
    _, p, q = get_aligned_distributions(p_dist, q_dist)
    return float(0.5 * np.sum(np.abs(p - q)))


def hellinger_fidelity(p_dist: Dict[str, float], q_dist: Dict[str, float]) -> float:
    r"""Bhattacharyya / Classical Fidelity between two distributions:
    F_{cl}(P, Q) = (\sum_x \sqrt{P(x) Q(x)})^2 \in [0, 1].
    """
    _, p, q = get_aligned_distributions(p_dist, q_dist)
    bhattacharyya_coeff = np.sum(np.sqrt(np.clip(p * q, 0.0, None)))
    return float(bhattacharyya_coeff ** 2)


def hellinger_distance(p_dist: Dict[str, float], q_dist: Dict[str, float]) -> float:
    r"""Hellinger Distance between two probability distributions:
    H(P, Q) = \sqrt{0.5 * \sum_x (\sqrt{P(x)} - \sqrt{Q(x)})^2} \in [0, 1].
    """
    _, p, q = get_aligned_distributions(p_dist, q_dist)
    diff = np.sqrt(p) - np.sqrt(q)
    return float(np.sqrt(0.5 * np.sum(diff ** 2)))


def calculate_relative_error_reduction(error_noisy: float, error_mitigated: float) -> float:
    r"""Calculates relative error reduction (percentage reduction in error/infidelity):
    Relative Error Reduction = ((Error_noisy - Error_mitigated) / Error_noisy) * 100%
    """
    if error_noisy <= 1e-12:
        return 0.0
    return float(((error_noisy - error_mitigated) / error_noisy) * 100.0)


def compute_all_metrics(
    p_ideal: Dict[str, float],
    p_noisy: Dict[str, float],
    p_mitigated: Dict[str, float],
) -> Dict[str, float]:
    """Calculates comprehensive quantitative metrics with explicit distinction between
    fidelity, infidelity/error, and relative error reduction.
    """
    # 1. Total Variation Distance (Error distance)
    tvd_noisy = total_variation_distance(p_ideal, p_noisy)
    tvd_mitigated = total_variation_distance(p_ideal, p_mitigated)
    tvd_relative_error_reduction_pct = calculate_relative_error_reduction(tvd_noisy, tvd_mitigated)

    # 2. Classical Bhattacharyya Fidelity
    fid_noisy = hellinger_fidelity(p_ideal, p_noisy)
    fid_mitigated = hellinger_fidelity(p_ideal, p_mitigated)
    fidelity_delta = fid_mitigated - fid_noisy

    # 3. Infidelity (State error = 1 - Fidelity)
    infidelity_noisy = 1.0 - fid_noisy
    infidelity_mitigated = 1.0 - fid_mitigated
    infidelity_relative_error_reduction_pct = calculate_relative_error_reduction(
        infidelity_noisy, infidelity_mitigated
    )

    # 4. Hellinger Distance
    hellinger_noisy = hellinger_distance(p_ideal, p_noisy)
    hellinger_mitigated = hellinger_distance(p_ideal, p_mitigated)
    hellinger_relative_error_reduction_pct = calculate_relative_error_reduction(
        hellinger_noisy, hellinger_mitigated
    )

    return {
        # TVD metrics
        "tvd_noisy": tvd_noisy,
        "tvd_mitigated": tvd_mitigated,
        "tvd_relative_error_reduction_pct": tvd_relative_error_reduction_pct,
        # Fidelity metrics
        "fidelity_ideal": 1.0,
        "fidelity_noisy": fid_noisy,
        "fidelity_mitigated": fid_mitigated,
        "fidelity_delta": fidelity_delta,
        # Infidelity / Error metrics
        "infidelity_noisy": infidelity_noisy,
        "infidelity_mitigated": infidelity_mitigated,
        "relative_error_reduction_pct": infidelity_relative_error_reduction_pct,
        # Hellinger distance metrics
        "hellinger_dist_noisy": hellinger_noisy,
        "hellinger_dist_mitigated": hellinger_mitigated,
        "hellinger_relative_error_reduction_pct": hellinger_relative_error_reduction_pct,
    }
