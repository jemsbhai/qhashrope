"""qhashrope prototype: pack-and-verify, classical + quantum.

Pack stage:    MultiSpecQR RGB multiplexing (classical) | superdense coding (quantum)
Verify stage:  hashrope polynomial fingerprints (classical) | Ablayev-Vasiliev-style
               product-state fingerprints + SWAP test (quantum)

Simulator only (Qiskit Aer). No speedup claims: see RESULTS.md limitations.
"""

__all__ = [
    "sequences",
    "classical_pack",
    "quantum_pack",
    "classical_verify",
    "quantum_verify",
    "pipeline",
]
