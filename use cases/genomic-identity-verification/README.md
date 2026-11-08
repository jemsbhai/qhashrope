# Private genomic identity verification

**Problem.** Two sites hold sequence data and need to know whether the records are the same: a clinic confirming a sample matches the one a central lab sequenced, or two biobanks checking whether they hold the same donor. Sending the sequence itself is a privacy exposure and, at genome scale, a large transfer.

**qhashrope fit.** Each side computes a quantum fingerprint of its sequence locally and sends only the fingerprint: O(log n) qubits for an n-base record. A SWAP test answers equality and reveals almost nothing about the sequence itself. This is the quantum counterpart of hashrope-bio, the author's classical genomic toolkit validated on GRCh38 chr22 (5,770/5,770 gene/exon queries) and ClinVar (3,422/3,422 pathogenic SNVs localized).

**Prototype status.** The verification stage is demonstrated on seeded 96 bp segments: identical, 1, 3, and 10 substitution pairs separate cleanly in simulation (SWAP-test P(0) of 1.000, 0.625, 0.573, 0.503). Scaling to full-length sequences and a hardware run are open steps.

**Known limitation.** The current block-hash codeword has no minimum distance, so near-identical sequences sit close to the decision threshold (one false positive under depolarizing noise p=0.02). The Ablayev-Vasiliev error-correcting encoding is the planned fix.
