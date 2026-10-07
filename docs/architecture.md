# System Architecture: Noise-Aware Quantum Engineering (Challenge I7)

## Overview
This platform implements an automated, modular, and evidence-driven quantum noise profiling and error-mitigation benchmarking suite for quantum cloud environments.

## Architecture Diagram

```
                 +---------------------------+
                 |  Quantum Benchmark Suite  |
                 | (Bell, GHZ, QAOA Ansatz)  |
                 +-------------+-------------+
                               |
                               v
                 +---------------------------+
                 |  Target Transpilation &   |
                 |   Structural Profiling    |
                 +-------------+-------------+
                               |
        +----------------------+-----------------------+
        |                      |                       |
        v                      v                       v
+---------------+      +----------------+      +---------------+
| Classical CPU |      | Ideal Quantum  |      | Realistic Aer |
| Baseline      |      | Simulator      |      | Noisy Sim     |
| (Statevector) |      | (Noiseless)    |      | (Depol + RO)  |
+---------------+      +----------------+      +-------+-------+
                                                       |
                                                       v
                                               +---------------+
                                               |  ZNE Engine   |
                                               | (Gate Folding |
                                               |  G->G G+ G)   |
                                               +-------+-------+
                                                       |
        +----------------------------------------------+
        |
        v
+--------------------------------------------------------------+
|             Quantitative Metric Evaluation Engine            |
| - Total Variation Distance (TVD)                             |
| - Classical Bhattacharyya / Hellinger Fidelity (F_cl)        |
| - Mitigation Error Reduction Gain (%)                        |
+--------------------------------------------------------------+
        |
        v
+--------------------------------------------------------------+
|                     Artifacts & Reports                      |
| - benchmark_results.json / benchmark_summary.csv             |
| - Comparative Distribution & Scaling Plots                   |
+--------------------------------------------------------------+
```

## Module Directory Breakdown
1. `src/circuits/`: Circuit construction with parameterizable depth and entanglement topology (`bell.py`, `ghz.py`, `benchmark.py`).
2. `src/noise/`: Standardized noise profiles (`noise_profiles.py`) and native Qiskit Aer `NoiseModel` constructor (`noise_model.py`).
3. `src/execution/`: Backend abstraction handling ideal Aer simulation (`ideal.py`), noisy Aer execution (`noisy.py`), transpilation profiling (`transpile_profiler.py`), and real IBM Quantum hardware verification (`hardware.py`).
4. `src/mitigation/`: Zero-Noise Extrapolation using digital unitary gate folding and Richardson extrapolation (`zne.py`).
5. `src/metrics/`: Mathematically rigorous distance and fidelity metrics (`fidelity.py`).
6. `src/benchmarking/`: CPU classical statevector complexity evaluation (`benchmark.py`).
7. `src/experiments/`: End-to-end execution pipeline and publication figure generation (`run_experiments.py`).
