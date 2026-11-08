# Outbreak strain matching

**Problem.** During an outbreak, surveillance labs in different institutions and countries need to know whether an isolate one of them has sequenced is the strain the others are tracking. The sequence data behind that question is sensitive on several axes at once: patient-linked sampling metadata, national reporting politics, and simple priority (nobody wants to pool raw data before their own analysis is out). What the network needs operationally is a match answer per isolate, early, without a central pool of everyone's sequences.

**qhashrope fit.** The isolate is reduced to its strain record: pathogen, lineage or clade assignment, and the defining variant signature. Each lab fingerprints its isolate record locally; the coordinating side holds the outbreak strain record; a SWAP test answers whether this isolate is that strain. Equality only: no sequence, no signature, no metadata crosses, which is what makes the check offerable between parties that will not pool data.

**Prototype status.** Measured in this folder: `outbreak_demo.py` ran both verifiers on three isolate-record pairs (noiseless MPS simulator, 4096 shots per pair, global threshold 0.75; full output in `results.json`). Classical hashrope 3/3, quantum fingerprint 3/3, including a single variant position differing in the signature, which correctly reads as a different strain under exact equality. The identical pair was also run under depolarizing noise p = 0.02 in both circuit forms; see below.

**Known limitation.** Outbreak matching in practice is phylogenetic, not exact: a genuine outbreak isolate accumulates mutations as transmission proceeds, so "same outbreak" means "close on the tree", and an exact-equality test flags descendants of the tracked strain as non-matches. The record-level signature used here (lineage plus defining sites) is the coarse level at which equality is the right question; anything finer needs a distance protocol, not a fingerprint equality test. The record also inherits the usual caveat: it verifies the typed record, and a mislabeled or misassigned isolate record passes or fails on its paperwork.

## Measured results (fixed encoding, 2026-11-08)

Demo: `outbreak_demo.py`; data: `results.json`. Settings: noiseless
AerSimulator (matrix_product_state), 4096 shots per pair, global threshold
0.75, Golay-encoded fingerprint.

| Case | Quantum P(0) | Decision |
|---|---|---|
| isolate identical to the known outbreak strain | 1.0000 | equal |
| one variant position differing (HA K160T to K160N) | 0.5063 | differ |
| an unrelated strain record (H1N1) | 0.5076 | differ |

Classical hashrope agrees on all three pairs (3/3); quantum 3/3. The
single variant change flips 16 of 24 encoded positions, the largest
codeword distance in this folder, because the edit lands in a densely
weighted part of the message fold; distance under the code is a
property of the encoding, not of biological importance, and the
decision only uses which side of the floor the pair sits on.

Two-server variant, identical pair, depolarizing noise p = 0.02:
monolithic P(0) = 0.7102, called differ (wrong); per-bit P(0) values in
[0.9548, 0.9734], 0 bits decided differ, Golay radius-3 decision equal
(correct). Same pattern as the root measurement: the monolithic
circuit loses identical pairs at this noise level, and the per-bit
decision recombination keeps them.
