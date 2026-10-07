# Noise-Aware Quantum Engineering

### Qiskit Fall Fest 2026 GITAM × IBM Quantum Hackathon — Industry Challenge I7
**Participant Role:** Quantum Software Engineer  
**Repository:** [jagadesh-14](https://github.com/jagadesh-jpg/jagadesh-14.git)

[![Qiskit Version](https://img.shields.io/badge/Qiskit-2.5.2-6929C4.svg)](https://qiskit.org/)
[![Qiskit Aer](https://img.shields.io/badge/Qiskit_Aer-0.17.2-0062FF.svg)](https://github.com/Qiskit/qiskit-aer)
[![IBM Quantum Runtime](https://img.shields.io/badge/IBM_Quantum_Runtime-0.50.0-0062FF.svg)](https://quantum.ibm.com/)
[![Tests](https://img.shields.io/badge/Tests-8%2F8%20Passed-10B981.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 1. Problem

### Official Industry Challenge I7 Statement:
> *"Quantum cloud team needs reliable results on noisy hardware.*  
> *Build: Noisy simulator, transpile, mitigate; report fidelity gain.*  
> *Role: Quantum software engineer."*

NISQ quantum processors suffer from decoherence, gate infidelities, and measurement readout assignment errors. Cloud quantum teams face the challenge of executing non-trivial quantum circuits on noisy physical processors while extracting meaningful expectation values without the prohibitive physical qubit overhead of full Quantum Error Correction (QEC).

---

## 2. Solution Pipeline

This repository implements an evidence-driven, reproducible quantum noise engineering pipeline:

```
  +----------------------+
  | Quantum Test Circuit | (Bell, GHZ, Non-Local Bell, QAOA Ansatz)
  +----------+-----------+
             |
             v
  +----------------------+
  | Target Transpilation | (Hardware-like basis decomposition & routing analysis)
  +----------+-----------+
             |
      +------+---------------------------------------+
      |                                              |
      v                                              v
+------------+                               +---------------+
| Ideal Ref  | (Noiseless Statevector)       | Controlled    | (Depolarizing + Readout
| Simulation |                               | Noise Sim     |  Low/Medium/High)
+-----+------+                               +-------+-------+
      |                                              |
      |                                              v
      |                                      +---------------+
      |                                      | ZNE Engine    | (Gate Folding G -> G G+ G
      |                                      | Extrapolator  |  lambda in {1, 3, 5})
      |                                      +-------+-------+
      |                                              |
      +----------------------+-----------------------+
                             |
                             v
              +------------------------------+
              | Quantitative Metrics Engine  | (Fidelity, Infidelity, Relative
              |                              |  Error Reduction %, TVD)
              +--------------+---------------+
                             |
                             v
              +------------------------------+
              | Real IBM Hardware Validation | (Execution on ibm_kingston 156Q)
              +------------------------------+
```

---

## 3. Architecture

Modular engineering structure:

```
jagadesh-14/
│
├── README.md                   # Complete scientific documentation & report
├── requirements.txt            # Locked verified dependencies
├── .gitignore                  # Security-hardened gitignore protecting secrets
├── LICENSE                     # MIT Open Source License
│
├── src/
│   ├── circuits/               # Bell, GHZ, Non-Local Bell, and QAOA ansatz generators
│   │   ├── bell.py
│   │   ├── ghz.py
│   │   └── benchmark.py
│   ├── noise/                  # Controlled synthetic noise models and profiles
│   │   ├── noise_profiles.py
│   │   └── noise_model.py
│   ├── execution/              # Transpilation profiler, noiseless & noisy simulators
│   │   ├── transpile_profiler.py
│   │   ├── ideal.py
│   │   ├── noisy.py
│   │   └── hardware.py
│   ├── mitigation/             # Zero-Noise Extrapolation (ZNE) gate folding engine
│   │   └── zne.py
│   ├── metrics/                # Rigorous fidelity, infidelity, and error metrics
│   │   └── fidelity.py
│   ├── benchmarking/           # Classical reference & memory scaling analysis
│   │   └── benchmark.py
│   ├── experiments/            # Automated test runner and visualization engine
│   │   └── run_experiments.py
│   └── hardware/               # Real IBM Quantum hardware integration layer
│       ├── ibm_backend.py      # Secure authentication & backend discovery
│       ├── hardware_runner.py  # Physical SamplerV2 runner & artifact recorder
│       ├── hardware_metrics.py # Physical vs reference metric evaluator
│       └── run_hardware.py     # Command-line hardware validation utility
│
├── tests/                      # Automated unit test suite (8/8 tests passing)
│   ├── test_pipeline.py
│   └── test_hardware.py
│
├── results/
│   ├── processed/              # Machine-readable summary CSV & JSON benchmarks
│   ├── figures/                # Publication-grade comparative plots
│   └── hardware/               # Authentic IBM Quantum physical hardware records
│       ├── raw/                # Measured physical shot counts
│       ├── processed/          # Summary metrics
│       └── metadata/           # Timestamps, job IDs, and compilation metadata
│
├── notebooks/
│   └── I7_experiment.ipynb     # Interactive Jupyter notebook walkthrough
│
└── docs/
    ├── architecture.md         # Pipeline architectural breakdown
    ├── methodology.md          # Scientific formulations and error channels
    └── limitations.md          # Failure modes and honesty guidelines
```

---

## 4. Scientific Methodology

### Controlled Synthetic Noise Profiles
All synthetic experiments are strictly isolated under **Controlled Synthetic Noise Profiles** (representative transmon error channels):
- **1-Qubit Gate Error**: Depolarizing channel $\mathcal{E}_1(\rho) = (1 - p_1) \rho + \frac{p_1}{3} \sum_{U} U \rho U^\dagger$.
- **2-Qubit Gate Error**: Depolarizing channel $\mathcal{E}_2(\rho) = (1 - p_2) \rho + \frac{p_2}{15} \sum_{U} U \rho U^\dagger$.
- **Readout / Assignment Error Matrix**: Asymmetric stochastic bit-flip channel.

| Profile | 1Q Error ($p_1$) | 2Q Error ($p_2$) | Readout Flip ($P(1|0), P(0|1)$) | Description |
|---|---|---|---|---|
| **Low** | $0.0005$ | $0.0050$ | $0.010$ ($1.0\%$) | High-coherence superconducting regime |
| **Medium** | $0.0015$ | $0.0150$ | $0.025$ ($2.5\%$) | Typical NISQ transmon regime |
| **High** | $0.0040$ | $0.0400$ | $0.050$ ($5.0\%$) | Heavy decoherence and cross-talk regime |

### Target Transpilation
Circuits are compiled against a **hardware-like synthetic target** (1D linear nearest-neighbor coupling $[0 - 1 - 2 - 3]$, native basis $\{CX, ID, R_z, SX, X\}$). Non-local operations (such as $CX(0, 2)$ in `non_local_bell_3q`) force SWAP insertion ($1 \text{ SWAP} \equiv 3 CX$), expanding depth from $3 \to 5$ and 2Q gates from $1 \to 4$.

### Zero-Noise Extrapolation (ZNE) Mitigation
- **Unitary Gate Folding**: Scales noise digitally via $G \to G (G^\dagger G)^k$ for odd scale factors $\lambda \in \{1, 3, 5\}$ while strictly preserving measurement terminations.
- **Richardson Extrapolation**: Fits $P_\lambda(x) = c_0(x) + c_1(x) \lambda$ to infer the zero-noise limit $P_{mit}(x) = \max(0, c_0(x))$, followed by $L_1$ normalization.

### Metric Definitions
- **Classical Bhattacharyya / Hellinger Fidelity**: $F_{cl}(P, Q) = \left( \sum_x \sqrt{P(x) Q(x)} \right)^2 \in [0, 1]$.
- **Infidelity / Error**: $\epsilon = 1 - F_{cl}$.
- **Relative Error Reduction**:
  $$\text{Relative Error Reduction} = \frac{\epsilon_{raw} - \epsilon_{mit}}{\epsilon_{raw}} \times 100\%$$
  *(Note: This represents the percentage of infidelity removed by mitigation. It is never called a "fidelity increase".)*
- **Total Variation Distance (TVD)**: $\text{TVD}(P, Q) = \frac{1}{2}\sum_x |P(x) - Q(x)| \in [0, 1]$.

---

## 5. Verified Benchmark Results

*Extracted directly from live executions (`results/processed/benchmark_summary.csv`):*

| Circuit | Target Depth | 2Q Gates (CX) | Noise Profile | Raw Fidelity | Mitigated Fidelity | Raw Infidelity ($\epsilon_{raw}$) | Mitigated Infidelity ($\epsilon_{mit}$) | Relative Error Reduction (%) |
|---|---|---|---|---|---|---|---|---|
| **Bell State ($2Q$)** | $3 \to 5$ | $1 \to 1$ | Low | 0.9775 | **0.9793** | 0.0225 | 0.0207 | **+7.88%** |
| **Bell State ($2Q$)** | $3 \to 5$ | $1 \to 1$ | Medium | 0.9431 | **0.9496** | 0.0569 | 0.0504 | **+11.48%** |
| **Bell State ($2Q$)** | $3 \to 5$ | $1 \to 1$ | High | 0.8872 | **0.9010** | 0.1128 | 0.0990 | **+12.27%** |
| **GHZ State ($3Q$)** | $4 \to 6$ | $2 \to 2$ | Low | 0.9644 | **0.9689** | 0.0356 | 0.0311 | **+12.67%** |
| **GHZ State ($3Q$)** | $4 \to 6$ | $2 \to 2$ | Medium | 0.9136 | **0.9291** | 0.0864 | 0.0709 | **+17.91%** |
| **GHZ State ($3Q$)** | $4 \to 6$ | $2 \to 2$ | High | 0.8159 | **0.8494** | 0.1841 | 0.1506 | **+18.18%** |
| **Non-Local Bell ($3Q$)** | $3 \to 5$ | $1 \to 4$ (1 SWAP) | Low | 0.9583 | **0.9695** | 0.0418 | 0.0305 | **+27.05%** |
| **Non-Local Bell ($3Q$)** | $3 \to 5$ | $1 \to 4$ (1 SWAP) | Medium | 0.8928 | **0.9239** | 0.1072 | 0.0761 | **+29.01%** |
| **Non-Local Bell ($3Q$)** | $3 \to 5$ | $1 \to 4$ (1 SWAP) | High | 0.7717 | **0.8214** | 0.2283 | 0.1786 | **+21.75%** |
| **QAOA Ansatz ($3Q$)** | $16 \to 26$ | $8 \to 8$ | Low | 0.9959 | **0.9978** | 0.0041 | 0.0022 | **+45.85%** |
| **QAOA Ansatz ($3Q$)** | $16 \to 26$ | $8 \to 8$ | Medium | 0.9809 | **0.9906** | 0.0191 | 0.0094 | **+50.73%** |
| **QAOA Ansatz ($3Q$)** | $16 \to 26$ | $8 \to 8$ | High | 0.9370 | **0.9564** | 0.0630 | 0.0436 | **+30.84%** |
| **GHZ Stress Test** | $4 \to 6$ | $2 \to 2$ | Extreme ($p_2=0.20$) | 0.4973 | **0.5337** | 0.5027 | 0.4663 | **+7.24%** *(Breakdown)* |

> **Note on Numerical Precision:**
> Relative error reduction percentages ($\text{Gain} = \frac{\epsilon_{raw} - \epsilon_{mit}}{\epsilon_{raw}} \times 100\%$) are calculated internally from full-precision 64-bit floating-point values stored in `benchmark_results.json` and `benchmark_summary.csv`. The table displays rounded values (4 decimal places) for visual readability.

---

## 6. Real IBM Quantum Hardware Validation Layer

An authentic, single physical execution was conducted on an IBM Quantum transmon processor to provide physical hardware evidence:

| Parameter | Value |
|---|---|
| **Physical Quantum Backend** | **`ibm_kingston`** (IBM Quantum Eagle / Heron architecture) |
| **Physical Qubit Count** | 156 Physical Qubits |
| **Authentic Job ID** | [`db37iaqqfgmc73d09rm0`](file:///results/hardware/metadata/ibm_kingston_non_local_bell_3q_20261007_165400_meta.json) |
| **Execution Status** | `COMPLETED` (Physical queue + execution time: 616.4 seconds) |
| **Circuit Evaluated** | `non_local_bell_3q` (3 logical qubits, $H$, non-local $CX(0, 2)$) |
| **Logical Circuit Complexity** | Depth: 3 \| 1Q Gates: 1 ($H$) \| 2Q Gates: 1 ($CX$) |
| **Physical Transpiled Complexity** | Depth: 8 \| 1Q Gates: 9 ($6 R_z, 3 SX$) \| 2Q Gates: 1 ($CZ$) \| SWAPs: 0 |
| **Measurement Shots** | 1024 Shots |
| **Physical Hardware Measured Counts** | `{'000': 511, '101': 485, '100': 21, '001': 5, '010': 1, '110': 1}` |
| **Noiseless Reference Distribution** | `{'101': 0.52148, '000': 0.47852}` |
| **Physical Hardware Classical Fidelity ($F_{cl}$)** | **`0.97150`** (Infidelity: **`0.02850`**) |
| **Total Variation Distance (TVD)** | **`0.04785`** |
| **Hellinger Distance** | **`0.11981`** |
| **Hardware ZNE Status** | **Hardware ZNE was not performed in this validation run.** |
| **Artifacts Preserved** | `results/hardware/raw/`, `results/hardware/processed/`, `results/hardware/metadata/` |

> **Important Distinction:** The fidelity $F_{cl} = 0.97150$ represents the raw physical measurement quality on `ibm_kingston`; it is **not** described as a ZNE improvement. Controlled synthetic noise experiments benchmarked the mitigation algorithm; real hardware execution provided independent physical evidence.

---

## 7. Classical Reference & Computational Scaling

Noiseless statevector simulation provides the mathematical reference distribution for the controlled experiments.

### Exponential Classical Memory Scaling:
$$\text{Memory} = 2^N \times 16 \text{ bytes (for double-precision complex128 amplitudes)}$$

- **$N = 3$ qubits** (current benchmark circuits): $8 \times 16 = \mathbf{128\text{ bytes}}$ (executed in $< 0.001\text{ s}$).
- **$N = 20$ qubits**: $1{,}048{,}576 \times 16 = \mathbf{16\text{ MB}}$.
- **$N = 30$ qubits**: $2^{30} \times 16 = \mathbf{16\text{ GB}}$.
- **$N = 40$ qubits**: $2^{40} \times 16 = \mathbf{16\text{ TB}}$.
- **$N = 50$ qubits**: $2^{50} \times 16 = \mathbf{16\text{ PB}}$ *(Classical Memory Wall)*.

> **Zero Quantum Advantage Claim:** For small benchmark circuits ($N \le 3$), classical CPU simulation is mathematically exact and vastly faster than quantum sampling. Quantum hardware scales in physical qubits $O(N)$ for state preparation, but suffers from physical device noise and shot variance.

---

## 8. Limitations & Scientific Honesty

In strict accordance with competition rules:
1. **Small Benchmark Circuits**: Experiments were conducted on 2-qubit and 3-qubit circuits to ensure fast, deterministic reproducibility.
2. **Synthetic vs Hardware Noise**: Simulation benchmarks utilized controlled synthetic depolarizing and readout channels; they are not claimed to be exact hardware calibration models.
3. **Single Hardware Snapshot**: The `ibm_kingston` run represents a single physical point-in-time calibration snapshot; real hardware coherence times ($T_1, T_2$) drift continuously.
4. **Hardware ZNE Omission**: ZNE was not evaluated on hardware to avoid excessive queue consumption; hardware ZNE remains a future extension.
5. **Mitigation Does Not Remove Physical Noise**: ZNE statistically infers the zero-noise expectation value; it does **not** physically eliminate hardware decoherence or increase coherence times.
6. **Breakdown at Extreme Noise**: As documented in the extreme stress test ($p_2 = 20\%$), when circuits decay into a maximally mixed state ($F \approx 0.497$), ZNE relative error reduction collapses to $+7.24\%$ because folded circuits lose linear error scaling.
7. **No Quantum Advantage**: No claim of quantum advantage is made.

---

## 9. Reproducibility & Installation

### Environment Requirements
- Python 3.11.x
- Qiskit 2.5.2
- Qiskit Aer 0.17.2
- Qiskit IBM Runtime 0.50.0

```bash
# Clone repository
git clone https://github.com/jagadesh-jpg/jagadesh-14.git
cd jagadesh-14

# Install dependencies
pip install -r requirements.txt
```

### Commands to Run

```bash
# 1. Run the complete synthetic noise benchmark & generate figures
python -m src.experiments.run_experiments

# 2. Run the real IBM Quantum hardware validation layer
# (Requires IBM_QUANTUM_API_KEY in environment or .env file)
python -m src.hardware.run_hardware --shots 1024

# 3. Check IBM Quantum backend access without submitting jobs
python -m src.hardware.run_hardware --check-only

# 4. Run automated test suite
python -m pytest tests/
```

---

## 10. Automated Tests

The repository includes a comprehensive pytest suite verifying pipeline components:
- `test_zne_gate_folding_preserves_noiseless_state`: Validates ideal unitary preservation.
- `test_transpilation_synthetic_target_routing_overhead`: Validates SWAP routing overhead.
- `test_metric_mathematical_consistency`: Validates mathematical metric bounds.
- `test_classical_reference_memory_scaling`: Validates exponential memory formula.
- `test_full_precision_artifact_consistency`: Validates all stored CSV/JSON records against ground truth equations.
- `test_missing_credentials_fails_gracefully`: Validates safe credential rejection.
- `test_hardware_metric_evaluation_consistency`: Validates hardware metric evaluations.
- `test_hardware_metadata_schema`: Validates non-secret metadata serialization.

**Test Status:** `8 passed in ~5s` (100% pass rate).
