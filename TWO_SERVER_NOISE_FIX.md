# Can the two-server construction fix qhashrope's noisy verification?

Analysis prepared 2026-11-08. This document is the experiment record
behind the "Two-server noise fix, 2026-11-08" section of RESULTS.md and
is part of the repo record.

Sources read for this analysis:

- Paper (full text): `paper/main.tex` in github.com/jemsbhai/herpb -
  "Exact Privacy-Preserving Similarity Search via Two-Server Additive
  Secret Sharing", Syed, Alsulami, Silaghi, IEEE ICTAI 2026 (published
  version: DOI 10.1109/ICTAI70596.2026.00211; first page verified against
  `~/workspace/niw-uploads/publications-batch/Syed - Exact
  Privacy-Preserving Similarity Search - IEEE ICTAI 2026 - First
  Page.pdf`, identical abstract). The repo README describes the earlier
  RPB/MRPB schemes; the secret-sharing protocol of the paper is
  implemented in `src/herpb/schemes/secret_sharing_64.py` and
  `src/herpb/rag/two_server.py`. github.com/jemsbhai/herpbHealth is a
  healthcare-domain application repo for the same protocol ("Privacy-
  preserving RAG for healthcare using two-server additive secret
  sharing... primitives implemented in the companion herpb package").
- Failure record: `RESULTS.md` in this repo, "Encoding fix,
  2026-11-08" (commits ce3e36b / 14a5931).
- Fingerprint code: `qhashrope/quantum_verify.py`,
  `qhashrope/qnoise.py` in this repo.

---

## A. The herpb / ICTAI protocol in brief

**Problem.** Privacy-preserving similarity search for RAG: rank a
corpus of document embeddings by dot product with a query embedding,
without exposing the query to the servers (query-private mode) or the
documents either (mutual-privacy mode).

**Construction.** All arithmetic is exact integer arithmetic in the
native ring Z_{2^64} (hardware uint64).

- Embeddings are fixed-point encoded: E_k(x) = round(x * 2^k). The only
  approximation in the pipeline is this one-time quantization; the
  dot-product error is bounded by d * 2^-k (unit vectors, dimension d)
  and does not grow with computation depth.
- A secret value m is additively shared: sample s_1 uniform in
  Z_{2^64}, set s_2 = m - s_1 mod 2^64. Server l gets s_l.
  Reconstruction is m = s_1 + s_2 mod 2^64 (two's complement for signs).
- Query-private mode: documents sit in plaintext on both servers; the
  client shares the query. Server l computes, for every document j,
  A_j^(l) = sum_i d_{j,i} * s_l^(i) - a plain uint64 dot product of the
  document against its query share. The client adds the two servers'
  partial sums and recovers the exact integer dot product, divides by
  the public constant 2^{2k}, and ranks. Zero inter-server
  communication.
- Mutual-privacy mode: documents are shared too. The one nonlinear
  operation (shared x shared) is done with matrix-vector Beaver
  triples: because the corpus matrix D is static, a dealer precomputes
  a random mask A, the public E = D - A, and per-query triples
  (b^(t), c^(t) = A b^(t)). Online, the servers open only
  f = q - b^(t) (one round, d integers, 3 KB at d = 384), each computes
  its share of Dq locally, and the client reconstructs exactly.

**Exactness.** Server arithmetic is exact in Z_{2^64}; headroom
(d * 2^{2k} ~ 2^41 << 2^63 at d = 384, k = 16) prevents wraparound, so
reconstructed scores equal the plaintext integer dot products exactly
and rankings are preserved exactly (Recall@1 = 1.000 in all reported
configurations). This is the paper's central contrast with CKKS, whose
noise accumulates per operation and corrupts rankings (Recall@1 =
0.883 at poly_modulus_degree 4096).

**Privacy.** Information-theoretic, not computational: each share is
uniform in Z_{2^64} and perfectly masks the value, so each server's
view is statistically independent of the query (and, in mutual mode,
of each document). The load-bearing assumption is that the two servers
do not collude; if they pool views they reconstruct everything. The
paper suggests enforcing non-collusion organizationally (different
providers/jurisdictions).

The architectural pattern to carry over: **replace one fragile global
computation with many small partial computations on shares, performed
independently, whose results the client recombines exactly.**

---

## B. Transfer to qhashrope: does the same move fix the p = 0.02 failure?

### B.0 The failure, restated

The fixed fingerprint encoding folds a string to a 12-bit message,
expands it with the extended binary Golay code (24, 12, 8), and
prepares the 24 codeword bits as a computational-basis product state
|codeword>. Two fingerprints are compared by one SWAP test over both
registers: 49 qubits, 2 Hadamards, 24 CSWAPs, plus the X preparations.
Noiselessly the analytic P(0) is in {1.0, 0.5} and the 0.75 midpoint
threshold is exact. Under the depolarizing model of
`qhashrope/qnoise.py` at p = 0.02, identical pairs contract to
P(0) = 0.72-0.74 and fall below threshold (stage 5: 6/9, all errors on
identical pairs), while distinct pairs stay at 0.4934-0.5110. At
p = 0.01 identical pairs read 0.836-0.839 and pass.

### B.1 The factorization - verified in the code

`analytic_overlap2` in quantum_verify.py returns exactly 1.0 if the two
24-bit codewords are identical and exactly 0.0 otherwise, because each
encoded bit b is prepared as the basis state |b> and differing bits are
orthogonal factors. In general, for two basis-state fingerprints,

    |<a|b>|^2 = prod_j delta(a_j, b_j),

i.e. the overlap factorizes over the 24 encoded-bit positions: it is 1
iff every position agrees and 0 if any position differs. (For the
legacy angle encoding the same factorization held over the 12 block
symbols with factors cos^2(delta_s * pi/16); the Golay expansion moved
the atoms from 12 symbols to 24 bits - the fold mixes the symbols
globally, so the bit, not the block, is the finest decomposition unit
of the fixed encoding.)

Consequence: the single 49-qubit SWAP network is not structurally
necessary. Position j can be tested by its own 3-qubit SWAP test
(ancilla + the two parties' j-th bits): prep is at most one X per side,
then H, one CSWAP, H, measure. The 24 tests are independent circuits
whose classical outcome estimates the client recombines. This is the
herpb pattern restated in quantum hardware terms: many small partial
computations, exact classical recombination, no single deep fragile
computation.

### B.2 (i) Circuit size and noise contraction per unit

Gate counts measured from the actual circuits built by
`qhashrope/quantum_verify.py` (identical codewords, so both registers
have weight 12):

- Monolithic SWAP test: **49 qubits; 24 X + 2 H + 24 CSWAP + 1
  measurement**. The whole entangled state (ancilla + 48 register
  qubits) is carried through all 24 noisy 3-qubit CSWAP gates, and a
  single ancilla measurement must survive all of it. Empirically the
  identical-pair coherence factor contracts to 2 * 0.73 - 1 ~ 0.46 at
  p = 0.02.
- Per-bit SWAP test: **3 qubits; at most 2 X + 2 H + 1 CSWAP + 1
  measurement** (5 noisy gates, depth ~5), no cross-bit entanglement,
  no idle spectator qubits. Across 24 tests the totals are 48 X + 48 H
  + 24 CSWAP: the decomposition does not reduce the raw count of
  expensive gates (the same 24 CSWAPs, and more single-qubit gates in
  aggregate). What it changes is the estimator structure, and that is
  where the noise behaviour differs:
  - Distinct positions are self-stabilizing: their analytic P(0) is
    0.5, and depolarizing noise pulls estimates toward 0.5, so a
    "differ" reading barely moves at any p.
  - Identical positions have analytic P(0) = 1.0 and contract, but
    each one only has to stay on the correct side of its own 0.75
    threshold: a per-bit margin of ~0.2 against shot noise of
    sigma <= 0.0078 at 4096 shots (~25 sigma). A bit decision fails
    only if five gates' worth of noise drags the estimate down by
    ~0.2, versus the monolithic test where the full 49-qubit
    contraction (~0.27 in P(0)) is compared against a 0.25 margin.
  - The Golay distance then absorbs residual bit errors: distinct
    codewords differ in >= 8 positions, so a decision rule of
    "equal iff at most 3 positions are decided differ" (the
    unique-decoding radius of the (24,12,8) code) tolerates up to 3
    fully wrong bit decisions on the equal side and up to 4 on the
    distinct side before it can flip.
  - The naive analog recombination - multiply the per-bit factors
    f_j = 2 p0_j - 1 into a global overlap estimate and threshold at
    0.75 - compounds the per-bit contractions across all 24 factors
    and is NOT expected to inherit this robustness. Section C measures
    all recombinations separately; this distinction is the crux.

### B.3 (ii) The two-server split and what privacy it buys

Mapping, following the paper's roles: the two string holders are the
clients (as in the Ablayev-Vasiliev simultaneous-message model they
already compute their own fingerprints locally); the two non-colluding
servers act as referees, each executing a disjoint subset of the
per-bit SWAP tests (say positions 0-11 and 12-23) on the fingerprint
bits for its positions, and returning the position estimates to the
client, who alone recombines them into the decision.

What this buys, stated carefully and weaker than the paper's
guarantee:

- Neither server ever sees a string; each sees only the fingerprint
  bits for its own positions. A 24-bit Golay codeword carries exactly
  the 12-bit folded message; a 12-position subset can in principle
  contain an information set, so one server might recover the folded
  message m - but m is a many-to-one folded hash of the string
  (collision probability 2^-12 across strings), not the string, and
  the AV fingerprint is already the privacy object of the protocol
  (log-size, reveals equality and little else). Splitting positions
  strictly reduces each server's view relative to a single referee
  holding the whole fingerprint.
- The non-collusion assumption does the same work as in the paper:
  if the servers pool their position estimates they jointly hold the
  full comparison, though still not the strings.
- Honest difference from herpb: there, servers compute over additive
  shares and never hold any plaintext-derived component; here the
  referees hold hash-derived fingerprint bits for their positions.
  The privacy is the AV fingerprint privacy plus a split-view
  reduction, not information-theoretic sharing of the underlying
  data. The transfer is architectural (decompose, distribute,
  recombine), not a literal port of the Z_{2^64} sharing.

### B.4 (iii) The common-mode variant

A weaker, simpler relative: measure a known-identical control pair
through the same circuits under the same noise, and decide relative
to the control instead of against the absolute 0.75 (the pre-fix
pipeline did exactly this at the monolithic level: control measured
0.800 at p = 0.02, threshold set to 0.650). In decomposed form the
control also localizes which positions contract. Costs: it assumes
the noise is stationary between the control and test runs (true in
this simulator by construction; on hardware, only approximately, over
short windows), and it spends margin by construction - the relative
threshold (C + 0.5)/2 sits halfway between the contracted identical
estimate and the floor. Section C reports it as recombination R4,
applied to the product estimator.

### B.5 (iv) What this does not fix

- Per-bit preparation and measurement noise remains: every bit test
  still carries up to 5 noisy gates, and on hardware, readout error
  and T1/T2 act on every one of the 24 runs. The Aer model used here
  has gate depolarizing noise only - no readout error, no idle
  decoherence, no crosstalk. Small circuits should fare better under
  idle/crosstalk terms (fewer spectators, shorter depth), but that is
  an argument, not a measurement; the simulation verdict does not
  transfer to hardware automatically.
- Cost multiplies: 24 circuits per comparison instead of 1, and 24x
  the shots for the same per-factor precision. On queued hardware,
  submission count dominates latency.
- The analog product estimator still compounds contraction across
  factors (measured in section C); decomposition alone, without
  decision-level recombination, is not the fix.
- The 2^-12 fold collision is untouched: two strings whose folded
  12-bit messages coincide are indistinguishable in every variant,
  monolithic or decomposed. The classical hashrope check remains the
  exact backstop.
- The identical-side margin is finite: at p = 0.05 the monolithic
  identical pair read 0.5688-0.5864; the per-bit margins shrink with p
  as well, and there is a p at which bit decisions start failing in
  bulk. The decomposition moves the failure point; it does not remove
  it.

---

## C. Experiment

**Setup.** Standalone script (library untouched) using the existing
fingerprint preparation (`qv.codeword`, `qv.fingerprint_circuit`) and
the existing noise model (`qnoise.depolarizing(0.02)` - the identical
model to RESULTS.md), MPS simulator (`qv.default_sim`), 4096 shots
per circuit. For each pair: (a) a fresh monolithic 49-qubit SWAP-test
estimate as head-to-head; (b) 24 per-bit 3-qubit SWAP tests. Pairs:
3 identical DNA, 3 DNA at 1 substitution, 3 DNA at 10 substitutions
(`sequences.make_pair_set`), aspirin vs its amide analog, benzene vs
cyclohexane, aspirin vs aspirin, plus an independent known-identical
control pair. Recombinations (all fixed in advance):

- **R1 product**: f_j = clip(2 p0_j - 1, 0, 1), global
  P(0) = (1 + prod f_j)/2, equal iff >= 0.75.
- **R2 AND**: a bit is decided "differ" iff p0_j < 0.75; equal iff
  zero bits decided differ.
- **R3 Golay**: equal iff bits decided differ <= 3 (unique-decoding
  radius of the (24,12,8) code).
- **R4 relative**: R1's product estimate, but threshold
  (C + 0.5)/2 = 0.5441 from the control pair's product estimate
  C = 0.5882, measured under the same noise.

**Per-bit readings.** Across all 13 pairs (312 bit tests) there were
**zero bit-decision errors**: every agreeing bit measured
P(0) in [0.9521, 0.9771] and every differing bit in [0.4866, 0.5225],
a clean gap around the 0.75 per-bit threshold. The number of bits
decided "differ" equals the true codeword Hamming distance in every
distinct case (8, 12, 16, 12, 12, 8, 12, 12 - the Golay minimum is 8)
and 0 in every identical case. Mean per-bit contraction on agreeing
bits: p0_j ~ 0.965, i.e. a per-bit factor f_j ~ 0.93; compounded,
0.93^24 ~ 0.18, which is exactly the product overlap measured below.

**Results table** (p = 0.02 throughout; "mono" = fresh monolithic
estimate at the 0.75 threshold):

| Pair | Truth | Mono P(0) | Mono | Product P(0) | R1 | R2 | R3 | R4 | Bits differ |
|---|---|---|---|---|---|---|---|---|---|
| DNA identical 1 | equal | 0.7368 | FAIL | 0.5927 | FAIL | pass | pass | pass | 0 |
| DNA identical 2 | equal | 0.7402 | FAIL | 0.5863 | FAIL | pass | pass | pass | 0 |
| DNA identical 3 | equal | 0.7244 | FAIL | 0.5917 | FAIL | pass | pass | pass | 0 |
| Aspirin identical | equal | 0.7356 | FAIL | 0.5921 | FAIL | pass | pass | pass | 0 |
| Control identical | equal | 0.7246 | FAIL | 0.5882 | FAIL | pass | pass | pass | 0 |
| DNA 1-sub 1 | differ | 0.5142 | pass | 0.5000 | pass | pass | pass | pass | 8 |
| DNA 1-sub 2 | differ | 0.5010 | pass | 0.5000 | pass | pass | pass | pass | 12 |
| DNA 1-sub 3 | differ | 0.5085 | pass | 0.5000 | pass | pass | pass | pass | 16 |
| DNA 10-sub 1 | differ | 0.4912 | pass | 0.5000 | pass | pass | pass | pass | 12 |
| DNA 10-sub 2 | differ | 0.4978 | pass | 0.5000 | pass | pass | pass | pass | 12 |
| DNA 10-sub 3 | differ | 0.5068 | pass | 0.5000 | pass | pass | pass | pass | 8 |
| Aspirin vs amide analog | differ | 0.4980 | pass | 0.5000 | pass | pass | pass | pass | 12 |
| Benzene vs cyclohexane | differ | 0.4973 | pass | 0.5000 | pass | pass | pass | pass | 12 |

**Scores at p = 0.02, 13/13 pairs:** monolithic @ 0.75: **8/13**
(all 5 identical pairs fail, reproducing the RESULTS.md stage-5
failure with fresh runs: 0.7244-0.7402). R1 product @ 0.75: **8/13**
- the same failure signature; decomposition with the analog product
estimator does not fix anything, because the per-bit contraction
compounds in the estimator just as it does in the deep circuit.
R4 relative: **13/13**, but on a thin margin (identical products
0.5863-0.5927 against a 0.5441 threshold; distinct at exactly 0.5000).
R2 AND: **13/13**. R3 Golay radius: **13/13**, with the widest margin
of any rule - identical pairs at 0 decided-differ against a tolerance
of 3, distinct pairs at 8-16 against the same tolerance, i.e. the
decision sits at least 4 bit-errors away from flipping on both sides,
and not one of the 312 bit decisions was wrong.

**Reading of the result.** The fix is not the decomposition alone and
not a better analog estimator: it is decomposition plus decision-level
recombination - per-position binary decisions with a per-position
margin (~0.20 in P(0), ~25 shot-noise sigma) and an error-correcting
code whose distance (8) converts residual bit errors into a tolerated
budget (3). That is precisely the herpb move: in the paper, servers
return exact partial sums and the client recombines them with exact
arithmetic; here the servers return shallow-circuit bit decisions and
the client recombines them with the Golay decoding rule. The fragile
step in both stories is the same - one deep, noise-accumulating
computation (CKKS evaluation there, the 49-qubit SWAP network here) -
and the remedy is the same: never let one analog quantity accumulate
the whole computation's error.

Raw per-bit data: run output preserved with this analysis (script:
two_server_experiment.py; results JSON: 24 per-bit estimates per
pair, monolithic estimates, circuit op counts).

## Verdict

- In simulation, at the exact noise level that breaks the current
  pipeline (depolarizing p = 0.02), the two-server-style
  decomposition with per-bit decisions and Golay-radius recombination
  classifies **13/13 pairs correctly**, where the monolithic circuit
  scores 8/13. The chemistry pairs that motivated the encoding fix
  (benzene/cyclohexane, aspirin/amide) are among the correct 13.
- The analog product recombination does **not** fix it (8/13), and
  the relative/control recombination fixes it only with a thin
  margin (13/13, margin ~0.04). Any write-up should credit the
  decision-level recombination, not "splitting the circuit" in
  general.
- Open for hardware: the Aer model here is gate-depolarizing only.
  The per-bit circuits (3 qubits, depth ~5) should be far less
  exposed to the idle-decoherence and crosstalk terms that dominate
  real devices than a 49-qubit circuit, and R3 tolerates up to 3 bad
  bit runs outright; but readout error now lands on 24 separate runs,
  queue cost is 24 jobs per comparison, and none of that is measured
  here. The 2^-12 fold-collision caveat is unchanged in all variants.
  (Closed the same day: see "Hardware follow-up, 2026-11-08" below.)

---

## Hardware follow-up, 2026-11-08

The open hardware question in the verdict above was answered the same
day. The per-bit protocol (R3, Golay radius-3 recombination) ran on
IBM Quantum hardware, backend ibm_marrakesh (SamplerV2, 4096 shots
per circuit), on three pairs: an identical DNA pair, benzene vs
cyclohexane, and aspirin vs its amide analog (the two chemistry pairs
from section C). All 3 pair decisions were correct, with zero
bit-decision errors in 72 bit tests: the identical pair showed 0
decided-differ bits, and each distinct pair showed exactly its true
Hamming distance of 12. Hardware per-bit P(0) values tracked the
p = 0.02 simulation closely (agreeing bits 0.9456-0.9670, differing
bits 0.4880-0.5334), and unlike the Aer model the device numbers
include readout error, T1/T2 decoherence, and crosstalk. The cost
noted above was the submission shape actually used: 24 circuits per
comparison, 72 circuits for the three pairs. Full per-bit values and
job IDs: HARDWARE_RESULTS.md; account and instance record:
IBM_QUANTUM_RUN.md. The 2^-12 fold-collision caveat is unchanged: it
applies to the hardware runs exactly as it does in simulation.

