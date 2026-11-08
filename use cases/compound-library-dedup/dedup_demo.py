"""Demo for the compound-library-dedup use case.

Two small fictional libraries of canonical SMILES (8 compounds each) with
a planted overlap of exactly 4 compounds. Every cross-library pair is
compared with the quantum fingerprint SWAP test (fixed Golay encoding,
noiseless MPS, 4096 shots, global threshold 0.75); classical hashrope runs
as the exact reference. The demo succeeds iff the quantum match set equals
the planted duplicate set exactly: no extras, no misses.
Writes results.json next to this script.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from qhashrope import classical_verify, quantum_verify  # noqa: E402

SHOTS = 4096

LIBRARY_A = {
    "aspirin": "CC(=O)Oc1ccccc1C(=O)O",
    "ibuprofen": "CC(C)Cc1ccc(C(C)C(=O)O)cc1",
    "caffeine": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
    "paracetamol": "CC(=O)Nc1ccc(O)cc1",
    "benzene": "c1ccccc1",
    "toluene": "Cc1ccccc1",
    "ethanol": "CCO",
    "phenol": "Oc1ccccc1",
}

LIBRARY_B = {
    "pyridine": "c1ccncc1",
    "caffeine": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
    "cyclohexane": "C1CCCCC1",
    "aspirin": "CC(=O)Oc1ccccc1C(=O)O",
    "acetone": "CC(C)=O",
    "benzene": "c1ccccc1",
    "methanol": "CO",
    "ethanol": "CCO",
}

PLANTED = {"aspirin", "benzene", "caffeine", "ethanol"}


def main():
    sim = quantum_verify.default_sim()
    quantum_matches = set()
    classical_matches = set()
    matrix = []
    for name_a, smi_a in LIBRARY_A.items():
        row = {"a": name_a, "matches": []}
        for name_b, smi_b in LIBRARY_B.items():
            q = quantum_verify.verify_pair(smi_a, smi_b, shots=SHOTS, sim=sim)
            c = classical_verify.verify_pair(smi_a, smi_b)
            if q["decision_equal"]:
                quantum_matches.add(name_a)
                row["matches"].append({"b": name_b,
                                       "estimated_p0": q["estimated_p0"]})
            if c["rope_equal"]:
                classical_matches.add(name_a)
        matrix.append(row)
    results = {
        "demo": "compound library deduplication without disclosure",
        "payload_type": "canonical SMILES strings",
        "quantum": {
            "simulator": "AerSimulator, matrix_product_state, noiseless",
            "shots": SHOTS,
            "threshold": quantum_verify.DEFAULT_THRESHOLD,
            "fingerprint": "Golay (24,12,8) encoded fingerprint, SWAP test",
        },
        "library_sizes": {"A": len(LIBRARY_A), "B": len(LIBRARY_B)},
        "cross_pairs_compared": len(LIBRARY_A) * len(LIBRARY_B),
        "planted_duplicates": sorted(PLANTED),
        "quantum_matches": sorted(quantum_matches),
        "classical_matches": sorted(classical_matches),
        "quantum_exact_match_set": quantum_matches == PLANTED,
        "match_matrix": matrix,
    }
    print(f"planted:   {sorted(PLANTED)}")
    print(f"quantum:   {sorted(quantum_matches)}  "
          f"exact={quantum_matches == PLANTED}")
    print(f"classical: {sorted(classical_matches)}  "
          f"exact={classical_matches == PLANTED}")
    out = Path(__file__).with_name("results.json")
    out.write_text(json.dumps(results, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
