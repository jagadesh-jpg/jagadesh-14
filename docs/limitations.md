# Experimental Limitations & Scientific Honesty

In strict adherence to the competition rules and scientific rigor, this document details the boundaries, known failure modes, and physical limitations of our approach.

## 1. Physical Noise vs Mitigation
- **Mitigation does NOT eliminate physical noise**: Error mitigation post-processes measurement statistics to infer noiseless expectation values. It does **not** protect quantum coherences during execution or increase physical coherence times ($T_1, T_2$).
- True fault tolerance requires Quantum Error Correction (QEC) with physical qubit overhead, not statistical extrapolation.

## 2. Zero-Noise Extrapolation (ZNE) Breakdown at Extreme Noise
- **Extreme Decoherence Failure Mode**: As demonstrated in our extreme-noise stress test ($p_2 = 20\%, \text{Readout} = 15\%$ on GHZ state), severe decoherence causes the state to decay into a maximally mixed state ($F_{cl} \approx 0.497$).
- Under these conditions:
  - Raw Fidelity: $0.4973$
  - Mitigated Fidelity: $0.5337$
  - Relative Error Reduction: only $+7.24\%$ (collapsing from $+18\%$ under standard noise).
- **Physical Reason**: Gate folding increases circuit depth by $3\times$ and $5\times$. When the base error is high, the folded circuits completely depolarize, destroying the linear error relationship assumed by Richardson extrapolation.

## 3. Sampling Stability Across Shot Counts
- In our shot-stability audit (1,000, 4,000, and 10,000 shots), the measured relative error reduction remained stable within $\pm 0.4\%$ on 4,000+ shots.
- **Scientific Interpretation**: The improvement remains stable across increased shot counts, reducing the likelihood that the observed gain is primarily a sampling fluctuation.

## 4. Classical Reference Analysis & No Quantum Advantage
- **No Quantum Advantage Claim**: For small test problem sizes ($N \le 20$ qubits), classical statevector linear algebra executes in $< 0.01$ seconds on a standard CPU and computes the exact amplitudes without shot noise.
- **Memory Scaling**:
  - Storage for complex128 statevector amplitudes scales as $\text{Memory} = 2^N \times 16 \text{ bytes}$.
  - At $N = 3$: 128 bytes.
  - At $N = 30$: 16 GB.
  - At $N = 40$: 16 TB.
  - At $N = 50$: 16 PB.
- Quantum hardware scales physically in linear qubits $O(N)$ for state preparation, but suffers from physical device noise and shot variance.

## 5. Real IBM Quantum Hardware Validation Layer & Limitations
- **Separation of Regimes**: Controlled synthetic-noise experiments were used to isolate and benchmark the mitigation workflow. Real IBM Quantum hardware execution was then implemented as an independent hardware validation layer.
- **Physical Hardware Constraints**:
  1. **Queue Latency**: Free-tier public IBM Quantum backends have dynamic queues ranging from minutes to hours.
  2. **Calibration Drift**: Physical coherence times ($T_1, T_2$), gate fidelities, and readout matrices drift over hours, meaning hardware runs reflect single-point-in-time calibration snapshots.
  3. **Backend-Specific Transpilation**: Circuits must be mapped to physical heavy-hex topologies, requiring routing and SWAP insertions.
  4. **ZNE Hardware Scaling**: On physical hardware with native pulse channels, digital gate folding $G \to G G^\dagger G$ increases physical circuit duration, making folded circuits vulnerable to $T_1/T_2$ relaxation.
  5. **Status Transparency**: In the absence of an active API key in `.env`, physical hardware execution is transparently recorded as **NOT EXECUTED**. Fabricated hardware results are strictly prohibited.

