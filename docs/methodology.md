# Scientific Methodology: Noise Engineering & Zero-Noise Extrapolation

## 1. Controlled Synthetic Noise Modeling
To test quantum software under realistic conditions without inventing or falsely claiming specific physical processor calibration data, we employ native Qiskit Aer error channels configured as **Controlled Synthetic Noise Profiles**:
- **1-Qubit Gate Error Channel**: Synthetic depolarizing error applied to native single-qubit basis gates:
  $$\mathcal{E}_1(\rho) = (1 - p_1) \rho + \frac{p_1}{3} \sum_{U \in \{X, Y, Z\}} U \rho U^\dagger$$
- **2-Qubit Gate Error Channel**: Synthetic depolarizing error applied to entangling gates ($CX$):
  $$\mathcal{E}_2(\rho) = (1 - p_2) \rho + \frac{p_2}{15} \sum_{U \in \{I, X, Y, Z\}^{\otimes 2} \setminus \{II\}} U \rho U^\dagger$$
- **Readout / Assignment Error Matrix**: Synthetic asymmetric bit-flip measurement channel:
  $$M = \begin{bmatrix} P(0|0) & P(0|1) \\ P(1|0) & P(1|1) \end{bmatrix}$$

Synthetic profiles evaluated:
| Profile | 1Q Error ($p_1$) | 2Q Error ($p_2$) | Readout Error ($P(1|0), P(0|1)$) | Regime Description |
|---|---|---|---|---|
| **Low** | $0.0005$ | $0.0050$ | $0.010$ ($1.0\%$) | Representative of next-generation high-coherence superconducting regime |
| **Medium** | $0.0015$ | $0.0150$ | $0.025$ ($2.5\%$) | Representative of typical NISQ transmon device regime |
| **High** | $0.0040$ | $0.0400$ | $0.050$ ($5.0\%$) | Representative of heavy decoherence and cross-talk regime |

---

## 2. Hardware-Like Synthetic Target Transpilation
Modern quantum software engineering must account for hardware-level compilation overheads. We transpile all circuits against a **hardware-like synthetic target**:
- **Coupling Map**: Restricted 1D nearest-neighbor linear coupling topology ($[0 - 1 - 2 - 3]$).
- **Native Basis Gates**: Transmon basis set $\mathcal{B} = \{CX, ID, R_z, SX, X\}$.
- **Structural Routing Impact**:
  - Non-adjacent operations (such as $CX(0, 2)$ in `non_local_bell_3q`) cannot execute directly and require SWAP insertion ($1 \text{ SWAP} \equiv 3 \text{ CX}$), expanding depth from 3 to 5 and 2Q gates from 1 to 4.
  - Decompositions into $SX$ and $R_z$ expand depth on alternating operator ansatzes (e.g. QAOA depth expands from 16 to 26).

---

## 3. Zero-Noise Extrapolation (ZNE) Mitigation
Zero-Noise Extrapolation scales physical noise artificially to infer the hypothetical noiseless limit ($\lambda \to 0$).

### Digital Gate Folding
For odd scale factors $\lambda \in \{1, 3, 5\}$:
Each elementary unitary operation $G$ is amplified according to:
$$G \to G (G^\dagger G)^k, \quad \text{where } k = \frac{\lambda - 1}{2}$$
Since $G^\dagger G = I$, the circuit remains unitarily equivalent under noiseless evolution. Measurement operations and barriers are preserved at the circuit termination and never folded.

### Richardson Polynomial Extrapolation
Given sampled probability distributions $P_\lambda(x)$ at scales $\lambda \in \{1, 3, 5\}$:
We fit a linear polynomial:
$$P_\lambda(x) = c_0(x) + c_1(x) \lambda$$
The extrapolated zero-noise probability is obtained as:
$$P_{mit}(x) = \max(0, c_0(x)), \quad \text{followed by } \tilde{P}_{mit}(x) = \frac{P_{mit}(x)}{\sum_y P_{mit}(y)}$$

---

## 4. Rigorous Metric Definitions

### Classical Bhattacharyya Fidelity ($F_{cl}$)
$$F_{cl}(P, Q) = \left( \sum_{x \in \mathcal{X}} \sqrt{P(x) Q(x)} \right)^2 \in [0, 1]$$

### Infidelity / Error ($\epsilon$)
$$\epsilon = 1 - F_{cl}(P_{ideal}, P)$$

### Relative Error Reduction (%)
$$\text{Relative Error Reduction} = \frac{\epsilon_{noisy} - \epsilon_{mit}}{\epsilon_{noisy}} \times 100\%$$
*(Note: This measures the percentage reduction in infidelity. It is never described as a "fidelity increase %".)*

### Total Variation Distance (TVD)
$$\text{TVD}(P, Q) = \frac{1}{2} \sum_{x \in \mathcal{X}} |P(x) - Q(x)| \in [0, 1]$$
