# qhashrope prototype — results

A combined pack-and-verify prototype joining the user's two published
classical systems with their quantum counterparts:

| Stage | Classical (published systems) | Quantum counterpart |
|---|---|---|
| Pack | MultiSpecQR: 3 payloads multiplexed into one RGB image | Superdense coding: 2 bits per transmitted qubit over shared Bell pairs |
| Verify | hashrope polynomial fingerprints (exact rope equality) | Ablayev-Vasiliev-style product-state fingerprints + SWAP test |

Built and run 2026-11-07. **Simulator only for this original run.** IBM
Quantum hardware runs followed on 2026-11-08; see the dated sections at the
end of this file ("Encoding fix", "Two-server noise fix", "Hardware run")
and HARDWARE_RESULTS.md.

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
one block by three symbol steps, so the fingerprints genuinely overlap at
cos²(3π/16) in that coordinate. The block-hash codeword has no guaranteed
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
  top of the depolarizing model used here). (Superseded in part on
  2026-11-08: the two-server per-bit protocol, developed after this build,
  has since run on ibm_marrakesh with 3 of 3 pair decisions correct and 0
  bit-decision errors; see the "Hardware run, 2026-11-08" section at the
  end of this file.)
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

**Update, 2026-11-08.** The hardware step was executed, in a different
shape than the plan above: by then the fingerprint encoding had been
replaced (Golay (24,12,8), below) and the monolithic SWAP form had been
shown to be the form noise breaks, so what ran on ibm_marrakesh was the
two-server per-bit protocol (24 three-qubit circuits per pair), not the
two monolithic circuit families and not a stage-5 calibration (the fixed
encoding needs none: the 0.75 threshold is set by construction). Result:
3 of 3 pair decisions correct, 0 bit-decision errors in 72 bit tests. An
exploratory monolithic 49-qubit job was also submitted; its status is
recorded in HARDWARE_RESULTS.md. Full record: HARDWARE_RESULTS.md and
IBM_QUANTUM_RUN.md.

## Encoding fix, 2026-11-08

Later on 2026-11-08, a chemistry demo (SMILES payloads, `use
cases/molecular-identity/`) exposed two failures of the original
fingerprint encoding, both measured, neither visible in the DNA tests
above:

1. **Codeword collision.** Benzene (`c1ccccc1`) and cyclohexane
   (`C1CCCCC1`) produced byte-identical 12-symbol codewords and scored
   P(0) = 1.0000, a false "equal" no threshold can fix. Both strings are 8
   characters, so most of the 12 blocks are empty or hold one character,
   and the unseeded per-block polynomial hashes coincided mod 16 on every
   block.
2. **No minimum distance.** Aspirin vs its one-character amide analog
   scored P(0) = 0.9839 against an analytic 0.9810, a false "equal" at
   the 0.85 threshold. The pair differed in exactly one codeword symbol,
   by one step (14 to 13); with angle encoding `Ry(s * pi / 8)`, a
   one-step symbol change leaves the fingerprint overlap at cos^2(pi/16)
   in that coordinate.

### The fix

The fingerprint in `qhashrope/quantum_verify.py` was redesigned in three
parts (the original encoding remains available behind a `legacy=True`
flag, and the validation runs below use the new encoding throughout):

- **Position-seeded block hashing, larger alphabet.** Each block's
  hashrope fingerprint is mixed (splitmix64 finalizer) with its block
  index and reduced mod 4096 instead of mod 16. Block content is hashed
  together with its position, so sparse blocks of short strings no longer
  coincide systematically. The map stays fully deterministic: identical
  strings give identical fingerprints.
- **Error-correcting expansion (Ablayev-Vasiliev).** The 12 symbols are
  folded into one 12-bit message `m = sum_j (2j+1) * s_j + 25 * len
  (mod 4096)`; every weight is odd, so any single-symbol change provably
  changes `m`, as does any length change. The message is then encoded
  with the extended binary Golay code (24,12,8) and each encoded bit is
  prepared as an orthogonal qubit state (|0> or |1>) instead of an angle
  step. Bound relied on: any two distinct messages have encoded Hamming
  distance at least 8 (verified exhaustively over all 4096 codewords:
  minimum nonzero weight 8), and their fingerprint states are supported
  on disjoint computational-basis strings, so the overlap is exactly 0.
  Identical strings keep overlap exactly 1.
- **One global threshold, fixed in advance.** With overlap in {0, 1} by
  construction, the SWAP-test probability P(0) = (1 + |<f|g>|^2) / 2
  takes only the analytic values 1.0 (equal) and 0.5 (distinct). The
  decision threshold is the midpoint, **0.75**, used for every pair in
  every run and demo below. At 4096 shots the sampling deviation is
  ~0.0078, so the threshold sits ~32 sampling deviations from both
  analytic values. No per-pair calibration remains anywhere in the
  pipeline (the old noise-stage self-calibration was removed for the
  same reason).

### New headline results (fixed encoding, same protocols as above)

- Test suite: 8/8 pass, including new exhaustive checks of the Golay
  minimum distance and of position seeding, and analytic separation of
  all five chemistry pairs. One existing test was changed: the
  maximally-different-pair test asserted the old encoding's angle
  geometry and now asserts the fixed encoding's behavior (orthogonal
  states, P(0) at the 0.5 floor).
- Stage 2, superdense pack, noiseless: message accuracy 1.00 (unchanged
  stage, re-run).
- Stage 3, classical verify: 18/18.
- Stage 4, quantum verify, noiseless: 18/18. Identical pairs measure
  P(0) = 1.0000; distinct-pair class means are 0.4963 (1 substitution),
  0.5085 (3), 0.5007 (10) - all at the analytic floor 0.5, independent of
  mutation count, as the distance-8 bound requires. Largest
  |estimate - analytic| over the 18 pairs: 0.0166.
- Stage 5, noisy end-to-end (depolarizing p = 0.02 on every gate,
  threshold 0.75, no calibration): **the quantum stage scores 6/9 and
  fails this stage.** All 6 distinct pairs are classified correctly
  (0.4934-0.5110); all 3 identical pairs are false negatives, measuring
  0.7344, 0.7400, and 0.7356 against the 0.75 threshold. The classical
  stage scores 9/9. The identical-pair estimate under the same noise,
  kept as a diagnostic only, is 0.7200. Cause: the encoded circuit is
  49 qubits with roughly twice the noisy gates of the legacy 25-qubit
  circuit, so at p = 0.02 the identical-pair signal contracts to
  ~0.72-0.74, below the 0.75 midpoint. The encoding is exact
  noiselessly; what was traded away is noise margin, and no threshold
  or noise-model adjustment was made to mask that.
- Stage 6, noise robustness: superdense message accuracy 1.00 at
  p = 0.01 and p = 0.05 (unchanged); identical-pair SWAP P(0) measures
  0.8389 and 0.8357 at p = 0.01 (above threshold) and 0.5688 and 0.5864
  at p = 0.05 (below threshold).
- Chemistry pairs (the original failures): 5/5 correct at threshold
  0.75. Aspirin vs itself 1.0000; aspirin vs amide analog 0.4944; benzene
  vs toluene 0.4849; benzene vs pyridine 0.4900; benzene vs cyclohexane
  0.4980. Every distinct pair has encoded Hamming distance 12 and sits
  at the analytic floor.
- Use-case demos (each folder under `use cases/` has the script and a
  `results.json` with full per-pair output): genomic identity 12/12
  quantum and 12/12 classical; model/dataset integrity 3/3 (a 3-byte
  change measures 0.5073); replica equality 3/3 (one-byte changes at the
  start and at the end of a 3,420-byte record measure 0.5093 and
  0.4902); record linkage 3/3 (a one-character DOB change measures
  0.4919); superdense packing message accuracy 1.00 at p = 0, 0.01,
  0.05; compound-library dedup recovers exactly the 4 planted duplicates
  out of 64 cross pairs, no extras, no misses; quantum-chemistry result
  verification 3/3 (a third-decimal coordinate change measures 0.5068).

The noisy identical-pair contraction is consistent, not an outlier
effect: repeated measurements of identical pairs at p = 0.02 across
separate runs gave 0.7200, 0.7280, 0.7283, 0.7312, 0.7339, 0.7344,
0.7356, 0.7397, 0.7400, and 0.7466, while distinct pairs stayed at
0.48-0.52 throughout. Net statement: under this noise model the fixed
encoding is exact noiselessly and fully robust for distinct pairs, but
its identical-pair margin at p = 0.02 does not reach the 0.75 midpoint
threshold. Closing that gap is a noise-hardening problem (fewer noisy
gates in the encoded circuit, or error mitigation), not a threshold
problem, and it is left as future work rather than tuned around.

What did not change: the fingerprint is still 24 qubits and the
communication advantage argument is untouched (in fact the encoded
fingerprint now has an exact overlap dichotomy rather than a graded
one). The residual fingerprint caveat is the fold: two different strings
whose folded 12-bit messages collide (probability 2^-12 for a random
distinct pair) stay indistinguishable to the quantum stage, exactly as
with any short fingerprint; the classical hashrope stage remains the
exact check.

## Two-server noise fix, 2026-11-08

The stage-5 failure recorded in the section above (fixed encoding,
monolithic 49-qubit SWAP test: at depolarizing p = 0.02 the
identical-pair signal contracts to 0.72-0.74 and falls below the 0.75
threshold) stands as measured. This section records a follow-up
experiment, run the same day, that closes that specific gap in
simulation. Full analysis, script, and raw per-bit data:
`TWO_SERVER_NOISE_FIX.md`, `two_server_experiment.py`,
`two_server_results.json`.

### The fix

The architectural pattern is imported from the author's ICTAI 2026
paper, "Exact Privacy-Preserving Similarity Search via Two-Server
Additive Secret Sharing" (DOI 10.1109/ICTAI70596.2026.00211): replace
one fragile global computation with many small partial computations on
shares, performed independently, whose results the client recombines
exactly. It applies here because the Golay-encoded fingerprint is a
computational-basis product state, so its overlap factorises exactly
over the 24 encoded bit positions: the single 49-qubit SWAP network
(24 X + 2 H + 24 CSWAP) is replaced by 24 independent 3-qubit SWAP
tests (ancilla plus the two parties' j-th bits; at most 5 noisy gates
each). Each test returns a per-bit binary decision (positions agree iff
per-bit P(0) >= 0.75), and the client decides "equal" iff at most 3
positions are decided differ, the unique-decoding radius of the
(24,12,8) Golay code. In the two-server mapping, two non-colluding
referees each execute a disjoint subset of the bit tests and return the
estimates; only the client recombines them.

### Measured head-to-head at p = 0.02

Same noise model (`qhashrope.qnoise`), MPS simulator, 4096 shots per
circuit, 13 pairs: 3 identical DNA, 3 DNA at 1 substitution, 3 DNA at
10 substitutions, aspirin vs aspirin, aspirin vs its amide analog,
benzene vs cyclohexane, and an independent known-identical control.

- **Monolithic circuit at the 0.75 threshold: 8/13.** All 5 identical
  pairs fail, measuring 0.7244-0.7402; all 8 distinct pairs pass
  (0.4912-0.5142). The stage-5 failure reproduces with fresh runs.
- **Per-bit decisions with Golay radius-3 recombination: 13/13.**
  Across all 312 bit tests there were zero bit-decision errors:
  agreeing bits measured P(0) in [0.9521, 0.9771] and differing bits in
  [0.4866, 0.5225], a clean gap around the 0.75 per-bit threshold.
  Identical pairs show 0 decided-differ bits; distinct pairs show
  8-16, equal to their true codeword Hamming distances in every case
  (the Golay minimum distance is 8). The decision sits at least 4
  bit-errors away from flipping on both sides.
- **Analog product recombination: 8/13, and explicitly not the fix.**
  Multiplying the per-bit factors into a global overlap estimate and
  thresholding at 0.75 fails with the same signature as the monolithic
  circuit: identical pairs land at 0.5863-0.5927, because the ~0.93
  per-bit contraction compounds across all 24 factors (0.93^24 ~ 0.18).
  Decomposition alone fixes nothing; decomposition plus decision-level
  recombination under the Golay decoding rule is the fix. (A relative
  control-pair rule also reached 13/13, but on a thin margin of ~0.04.)

**Re-verified 2026-11-10** from a clean copy of this repository at HEAD
a5c8b30 (`two_server_experiment.py`, Qiskit 2.6.2, Aer 0.18.2, same
noise model, 4096 shots per circuit): monolithic 8/13 with the five
identical pairs at 0.7268-0.7385, product recombination 8/13, per-bit
Golay radius-3 recombination 13/13, zero bit-decision errors in 312
bit tests, and decided-differ counts equal to the true codeword
Hamming distances in every case. Every decision field matches
`two_server_results.json` exactly; only the analog product values
move, at the third decimal, as expected from shot noise.

### Caveats

- **Cost: 24 circuits per comparison instead of 1**, and 24x the shots
  for the same per-factor precision. On queued hardware, submission
  count dominates latency.
- **Simulator limits.** The Aer noise model used here is
  gate-depolarizing only: no readout error, no idle decoherence
  (T1/T2), no crosstalk. The per-bit circuits (3 qubits, depth ~5)
  should be far less exposed to those terms than a 49-qubit circuit,
  and the radius-3 rule tolerates up to 3 fully wrong bit decisions
  outright, but the hardware advantage is argued, not measured. The
  IBM Quantum hardware run remains open, and the simulator verdict
  does not transfer to hardware automatically. (Update, 2026-11-08:
  the hardware run has since been executed and agreed with the
  simulator verdict; see the next section.)
- **The 2^-12 fold collision is untouched.** Two strings whose folded
  12-bit messages coincide remain indistinguishable to the quantum
  stage in every variant, monolithic or decomposed. The classical
  hashrope stage remains the exact check.

## Hardware run, 2026-11-08

The two-server per-bit protocol was run on IBM Quantum hardware (**ibm_marrakesh**, SamplerV2, 4096 shots per circuit): 3 of 3 pair decisions correct under the Golay radius-3 rule, 0 bit decision errors in 72 per-bit tests. The three pairs were an identical DNA pair (decided equal, 0 bits differ), benzene vs cyclohexane (12 of 12 differing bits decided differ), and aspirin vs its amide analog (12 of 12). Hardware per-bit P(0) tracked the p=0.02 simulation closely: agreeing bits measured 0.9456-0.9670 and differing bits 0.4880-0.5334, with the device's readout error, decoherence, and crosstalk included in those numbers, none of which the Aer model has. The exploratory monolithic 49-qubit job (dbo8uudt7fqc73ako33g) also completed: on the identical pair A it measured P(0) = 0.4814, essentially at the 0.5 analytic floor, and decided differ, which is incorrect. The monolithic form fails on hardware as it does in the p=0.02 simulation, and more completely; the per-bit form on the same device was 3 of 3. Full per-bit values, job IDs (dbo8ukc4148s73924tfg, dbo8ukgou4as73b5ml6g, dbo8ul5t7fqc73ako2pg) and the monolithic job are in `HARDWARE_RESULTS.md` (`hardware_results.json`, `hardware_jobs.json`); the account and instance record is in `IBM_QUANTUM_RUN.md`.
