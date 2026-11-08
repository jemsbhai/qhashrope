# Private genomic identity verification

**Problem.** Two sites hold sequence data and need to know whether the records are the same: a clinic confirming a sample matches the one a central lab sequenced, or two biobanks checking whether they hold the same donor. Sending the sequence itself is a privacy exposure and, at genome scale, a large transfer.

**qhashrope fit.** Each side computes a quantum fingerprint of its sequence locally and sends only the fingerprint: O(log n) qubits for an n-base record. A SWAP test answers equality and reveals almost nothing about the sequence itself. This is the quantum counterpart of hashrope-bio, the author's classical genomic toolkit validated on GRCh38 chr22 (5,770/5,770 gene/exon queries) and ClinVar (3,422/3,422 pathogenic SNVs localized).

**Prototype status.** The verification stage is demonstrated on seeded 96 bp segments: identical, 1, 3, and 10 substitution pairs separate cleanly in simulation (SWAP-test P(0) of 1.000, 0.625, 0.573, 0.503). Scaling to full-length sequences and a hardware run are open steps.

**Known limitation.** The current block-hash codeword has no minimum distance, so near-identical sequences sit close to the decision threshold (one false positive under depolarizing noise p=0.02). The Ablayev-Vasiliev error-correcting encoding is the planned fix.

## Measured results (fixed encoding, 2026-11-08)

Demo: `genomic_demo.py`; data: `results.json`. Settings: noiseless
AerSimulator (matrix_product_state), 4096 shots per pair, global threshold
0.75. Fingerprint: 12 position-seeded block symbols (mod 4096) folded to a
12-bit message, extended Golay (24,12,8) encoding, SWAP test.

| Pair class (3 pairs each) | Quantum P(0) estimates | Decision |
|---|---|---|
| identical | 1.0000, 1.0000, 1.0000 | equal |
| 1 substitution | 0.5007, 0.4912, 0.4951 | differ |
| 3 substitutions | 0.5083, 0.5029, 0.4944 | differ |
| 10 substitutions | 0.4980, 0.4954, 0.5034 | differ |

Accuracy: classical hashrope 12/12, quantum fingerprint 12/12. Distinct
pairs sit at the analytic floor 0.5 regardless of substitution count,
because any message difference flips at least 8 of the 24 encoded bits.
