# Use cases

Applications of the qhashrope pack-and-verify prototype, one folder each. Every case uses the same two primitives: superdense-coding packing (2 bits per transmitted qubit over shared Bell pairs) and quantum fingerprint verification (Ablayev-Vasiliev-style product-state fingerprints compared with a SWAP test).

1. [genomic-identity-verification](genomic-identity-verification/) - Private genomic identity verification: prove two sequence records match without revealing the sequence.
2. [model-dataset-integrity](model-dataset-integrity/) - Model and dataset integrity attestation: prove a deployed artifact is bit-identical to the certified one.
3. [replica-equality](replica-equality/) - Replica equality over constrained links: verify large copies match by exchanging O(log n) qubits.
4. [record-linkage](record-linkage/) - Record linkage without disclosure: two institutions check whether they hold the same record, learning only the answer.
5. [superdense-packing](superdense-packing/) - Entanglement-assisted dense packing: send later data at 2 bits per qubit over entanglement shared in advance.
6. [molecular-identity](molecular-identity/) - Molecular identity verification: confirm a compound record (canonical SMILES/InChI) is identical across sites without distributing the structure library. Includes a measured chemistry demo.
7. [compound-library-dedup](compound-library-dedup/) - Compound library deduplication without disclosure: two organizations find their library overlap by equality only, without pooling proprietary structures.
8. [quantum-chemistry-result-verification](quantum-chemistry-result-verification/) - Quantum chemistry result verification: check that two computations on different machines or in different labs produced identical output records.
