# qhashrope prototype — results

A combined pack-and-verify prototype joining the user's two published
classical systems with their quantum counterparts:

| Stage | Classical (published systems) | Quantum counterpart |
|---|---|---|
| Pack | MultiSpecQR: 3 payloads multiplexed into one RGB image | Superdense coding: 2 bits per transmitted qubit over shared Bell pairs |
| Verify | hashrope polynomial fingerprints (exact rope equality) | Ablayev-Vasiliev-style product-state fingerprints + SWAP test |

Built and run 2026-11-07. **Simulator only.** IBM Quantum hardware runs are
the remaining step and need the user's personal account token (not used here).

## Environment

- Python 3.12.3, Qiskit 2.6.2, qiskit-aer 0.18.2, multispecqr 0.2.1,
  hashrope (PyPI) — all inside `~/workspace/.qiskit-venv`
  (multispecqr and hashrope were pip-installed into that venv; both are the
  user's published packages, used unmodified).
- Simulator: AerSimulator, `matrix_product_state` method for the SWAP-test
  circuits (see "Simulator choice" below); default method elsewhere.
- Machine: x86_64 Linux VM. Full suite runtime ~78 s.

## Commands

```
~/workspace/.qiskit-venv/bin/python tests/test_prototype.py   # 5 assertions
~/workspace/.qiskit-venv/bin/python run_prototype.py          # stages 1-6 -> results.json
```

Raw outputs: `logs/tests.log`, `logs/run.log`, `results.json`,
`packed_rgb.png` (the stage-1 multiplexed image).

## Architecture

- `qhashrope/sequences.py` — seeded 96 bp DNA-like segments; pair classes
  identical / 1 / 3 / 10 point substitutions.
- `qhashrope/classical_pack.py` — MultiSpecQR `encode_rgb` / `decode_rgb`.
- `qhashrope/quantum_pack.py` — superdense coding, 4 pairs = 8 payload bits
  per trial. Decode handles Qiskit's counts-key bit order (per pair, the
  Bob-qubit bit is the flip bit, the Alice-qubit bit is the phase bit;
  verified deterministically in the tests).
- `qhashrope/classical_verify.py` — hashrope `PolynomialHash` (2^61−1,
  base 131), `rope_from_bytes`, `rope_equal`, `rope_hash`.
- `qhashrope/quantum_verify.py` — fingerprint construction: segment split
  into 12 blocks; codeword symbol of a block = its hashrope fingerprint
  mod 16; symbol s encoded as Ry(s·π/8) on one qubit (12-qubit product
  state). Overlap factorises: |⟨ψ|φ⟩|² = Π cos²(Δs·π/16), decaying with
  codeword Hamming distance. Full SWAP test (ancilla + 12 cswap, 25 qubits)
  estimates P(0) = (1 + |⟨ψ|φ⟩|²)/2; decision threshold 0.85 noiseless.
  Every estimate is cross-checked against the closed-form analytic value.
- `qhashrope/pipeline.py` — end-to-end (pack, mutate, verify), with
  noise-aware threshold calibration (below).
- `qhashrope/qnoise.py` — depolarizing Aer noise models.

## Tests (all pass)

- Superdense coding: all 4 messages decode exactly, 256/256 shots each.
- MultiSpecQR: 3-payload round-trip lossless.
- hashrope: identical ropes equal; 1-substitution ropes differ (hash + equality).
- SWAP test, identical fingerprints: P(0) = 1.0000 (theory 1.0).
- SWAP test, maximally different codewords: P(0) = 0.495–0.500 across runs
  (theory 0.5).

## Stage results

### Stage 1 — classical pack (MultiSpecQR RGB)
3 payloads (`QHASHROPE-DEMO`, `PACK:MSQR+SDC`, `VERIFY:SWAP-TEST`) packed
into one 33×33 RGB image and decoded back: **3/3 exact, lossless**.

### Stage 2 — quantum pack (superdense coding, noiseless)
20 trials × 8 payload bits: **message accuracy 1.00, bit accuracy 1.00**.

### Stages 3+4 — verify, 18 segment pairs (4096 shots per SWAP test)
Classical hashrope verify: **18/18 correct** (exact, as expected).
Quantum fingerprint verify, threshold 0.85: **18/18 correct** in the final
run; mean estimated P(0) by class — identical 1.000, 1 mutation 0.625,
3 mutations 0.573, 10 mutations 0.503. Max |estimated − analytic| P(0)
across pairs: 0.018 (≈2σ of shot noise at 4096 shots).
Caveat observed across runs: one 1-mutation pair has analytic P(0) = 0.8457,
within shot noise of the 0.85 threshold; it classified correctly in the final
run and incorrectly in an earlier run (17/18). Cause: its codewords differ in
one block by one symbol step, so the fingerprints genuinely overlap at
cos²(π/16) in that coordinate. The block-hash codeword has no guaranteed
minimum distance; the Ablayev-Vasiliev construction assumes an error-
correcting code with relative distance δ. Dropping a real ECC (e.g.
Reed–Solomon over the symbols) in front of the angle encoding is the known
fix and the first upgrade for the hackathon notebook.

### Stage 5 — end-to-end (depolarizing noise p = 0.02 on quantum verify)
9 trials (3 identical, 2× each of 1/3/10 mutations).
Classical verify: TP 3, TN 6, FP 0, FN 0 — accuracy 1.00.
Quantum verify: **TP 3, TN 5, FP 1, FN 0 — accuracy 0.89**.
The one false positive is a 1-mutation trial (analytic P(0) 0.75, measured
0.655 under noise vs calibrated threshold 0.650) — borderline by construction.
Failure found and fixed during the build: with the fixed noiseless threshold
0.85, all 3 identical trials were rejected (FN 3, accuracy 0.67), because
depolarizing noise pulls identical-pair P(0) from 1.0 down to ≈0.80 at
p = 0.02. Fix: calibrate the threshold per noise condition — measure a
known-identical pair under the same noise model (measured 0.800) and set the
threshold midway to 0.5 (→ 0.650). This is the direct analogue of
MultiSpecQR's colour-calibration step.

### Stage 6 — noise sweep (depolarizing, all gates)
| p | Superdense message acc. (8 trials) | Superdense bit acc. | SWAP identical-pair P(0) |
|---|---|---|---|
| 0.0 | 1.00 | 1.00 | 1.000 |
| 0.01 | 1.00 | 1.00 | 0.886 |
| 0.05 | 1.00 | 1.00 | 0.634 |

Superdense coding (shallow 2-qubit circuits, majority outcome over 1024
shots) is robust at these levels; the 25-qubit SWAP-test circuit degrades
steadily, which is exactly why the verify stage needs calibration.

## Simulator choice (performance note)
Statevector simulation of one 25-qubit SWAP-test run took 12.8 s regardless
of shot count on this machine; the MPS method took 0.14 s at 4096 shots.
Fingerprint states are product states and the SWAP circuit entangles them
weakly, so MPS is essentially exact here; it was validated against both the
closed-form analytic overlap (max deviation 0.018 over 18 pairs, consistent
with shot noise) and an earlier statevector run of the same circuits
(agreement within shot noise). All reported P(0) values are MPS estimates
cross-checked against the analytic values in `results.json`.

## Failures encountered during the build (all resolved, none skipped silently)
1. Aer rejected a 2-qubit depolarizing error on the 3-qubit `cswap`
   instruction (`NoiseError`). Fixed by attaching a 3-qubit depolarizing
   error to `cswap` in `qnoise.py`.
2. Fixed-threshold end-to-end verify failed under noise (accuracy 0.67);
   fixed by calibration, documented in Stage 5 above.
3. The borderline 1-mutation pair (analytic P(0) 0.8457 vs threshold 0.85)
   is a genuine protocol limitation, not a bug; documented in Stages 3+4
   with the ECC fix path.

## Honest limitations
- **Simulator only.** No IBM Quantum hardware was accessed; no token was
  available to this build. Hardware P(0) values will sit below the MPS
  numbers (real devices add readout error, crosstalk, and T1/T2 decay on
  top of the depolarizing model used here).
- **No speedup is claimed anywhere.** The quantum fingerprint equality test
  is a communication-complexity statement (simultaneous-message model):
  fingerprints of ~log n qubits suffice for equality testing between two
  parties who each hold a string. On one machine, preparing and comparing
  the states costs more than the classical hashrope fingerprint comparison,
  which is exact and effectively free at this scale.
- **Holevo cap respected.** Superdense coding's 2 bits per transmitted
  qubit requires a pre-shared entangled pair; it does not beat the
  one-bit-per-qubit readout limit for unentangled carriers, and nothing in
  the pack stage claims MultiSpecQR-style 3×/9× readable-payload density.
- **Scale.** 96 bp segments, 12-qubit fingerprints, 8-bit superdense
  payloads: a mechanism demonstration with measured numbers, sized for a
  hackathon notebook, not a benchmark against production tools.
- The classical hashrope check is exact (61-bit hash, full rope equality);
  it is the ground-truth anchor for the quantum verify stage, not a
  competitor the quantum stage beats.

## What remains for the hardware step
1. Add the user's IBM Quantum token (his account), pick a backend, and
   submit the two circuit families (superdense payloads, SWAP tests for the
   same 18 pairs) — submit early, free-tier queue time is the schedule risk.
2. Re-run the stage-5 calibration on the real backend (identical-pair P(0)
   on hardware sets the threshold) before classifying any pair.
3. Optional: readout-error mitigation on the ancilla measurement; ECC
   (Reed–Solomon) codeword upgrade for the fingerprint stage.
