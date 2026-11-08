# Use cases

Applications of the qhashrope pack-and-verify prototype, one folder each. Every case uses the same two primitives: superdense-coding packing (2 bits per transmitted qubit over shared Bell pairs) and quantum fingerprint verification (Ablayev-Vasiliev-style fingerprints compared with a SWAP test). As of 2026-11-08 the fingerprint uses the fixed encoding (position-seeded block hashing, Golay (24,12,8) error-correcting expansion, one global decision threshold of 0.75); every folder carries a runnable demo and a `results.json` with measured values from that pipeline. See the "Encoding fix, 2026-11-08" section of the root RESULTS.md.

1. [genomic-identity-verification](genomic-identity-verification/) - Private genomic identity verification: prove two sequence records match without revealing the sequence.
2. [model-dataset-integrity](model-dataset-integrity/) - Model and dataset integrity attestation: prove a deployed artifact is bit-identical to the certified one.
3. [replica-equality](replica-equality/) - Replica equality over constrained links: verify large copies match by exchanging O(log n) qubits.
4. [record-linkage](record-linkage/) - Record linkage without disclosure: two institutions check whether they hold the same record, learning only the answer.
5. [superdense-packing](superdense-packing/) - Entanglement-assisted dense packing: send later data at 2 bits per qubit over entanglement shared in advance.
6. [molecular-identity](molecular-identity/) - Molecular identity verification: confirm a compound record (canonical SMILES/InChI) is identical across sites without distributing the structure library. Includes a measured chemistry demo.
7. [compound-library-dedup](compound-library-dedup/) - Compound library deduplication without disclosure: two organizations find their library overlap by equality only, without pooling proprietary structures.
8. [quantum-chemistry-result-verification](quantum-chemistry-result-verification/) - Quantum chemistry result verification: check that two computations on different machines or in different labs produced identical output records.
