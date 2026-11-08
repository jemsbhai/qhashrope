# Quantum chemistry result verification

**Problem.** Computational chemistry results get recomputed constantly: an optimized geometry or checkpoint produced on one cluster is rerun on another machine, in another lab, or by a collaborator validating a published result. The outputs are large records (geometries, wavefunction checkpoints, property blocks), and "did we get the same answer?" is usually answered by eyeballing a few printed energies, which misses silent divergence in the parts nobody printed.

**qhashrope fit.** Treat the result record as what it is for verification purposes: a byte string. Fingerprint the canonicalized output on each side and compare with a SWAP test; the O(log n) qubit fingerprint stands in for a record of any size, and the classical hashrope fingerprint of the same record is the exact check beside it. This is the replica-equality case specialized to scientific computing, with one domain-specific twist: it verifies that two quantum computations agree, using a quantum communication primitive to do it.

**Prototype status.** The verification pipeline is demonstrated in simulation on string payloads, including a chemistry run on canonical SMILES in the molecular-identity folder (classical stage exact on all pairs; quantum stage correct on 3 of 5, with a measured codeword collision that bounds what the current encoding can be trusted to distinguish). No quantum-chemistry output files have been run through it yet; the record-canonicalization step that real checkpoint and log formats need does not exist in this prototype.

**Known limitation.** Byte equality is stricter than scientific equivalence. Two runs of the same calculation routinely differ in byte-level details that mean nothing (iteration counts, ordering of printed terms, floating-point last digits across architectures), so a raw fingerprint check flags agreement-level results as different; and genuinely different results that happen to share a codeword would pass. A usable version needs a canonicalization layer that reduces a result record to its scientifically meaningful content before fingerprinting, which is a chemistry judgment, not a hashing detail. The exact-equality core demonstrated here is the foundation that layer would sit on.

## Measured results (fixed encoding, 2026-11-08)

Demo: `qchem_demo.py`; data: `results.json`. Settings: noiseless
AerSimulator (matrix_product_state), 4096 shots per pair, global threshold
0.75, Golay-encoded fingerprint.

| Case | Quantum P(0) | Decision |
|---|---|---|
| same result record from two machines | 1.0000 | equal |
| one coordinate changed in the third decimal | 0.5068 | differ |
| a different geometry (methane record) | 0.5083 | differ |

Classical hashrope agrees on all three pairs (3/3); quantum 3/3. The
third-decimal change is a single character in one block; under the fixed
encoding that suffices to move the pair to the analytic floor 0.5 (under
the pre-fix encoding, the analogous one-character change in the aspirin
pair scored 0.9839; see molecular-identity).
