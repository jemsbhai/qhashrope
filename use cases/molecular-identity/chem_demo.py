"""Chemistry demo for the molecular-identity use case.

Runs the EXISTING qhashrope verifiers on canonical SMILES string pairs:
  - classical: hashrope exact equality (qhashrope.classical_verify)
  - quantum:   product-state fingerprints + SWAP test
               (qhashrope.quantum_verify), noiseless MPS simulator,
               4096 shots, default threshold 0.85.

Payloads are plain byte strings (the fingerprint pipeline works on any
string); here they are canonical SMILES for small, well-known compounds.

Writes results.json next to this script and prints a summary table.

Run with the project venv:
    ~/workspace/.qiskit-venv/bin/python "use cases/molecular-identity/chem_demo.py"
"""

import json
import sys
from pathlib import Path

# The qhashrope package lives at the repo root, two levels up.
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from qhashrope import classical_verify, quantum_verify  # noqa: E402

SHOTS = 4096

# (case name, reference SMILES, candidate SMILES)
PAIRS = [
    ("aspirin vs aspirin (identical)",
     "CC(=O)Oc1ccccc1C(=O)O", "CC(=O)Oc1ccccc1C(=O)O"),
    ("aspirin vs aspirin amide analog (terminal O -> N, one character)",
     "CC(=O)Oc1ccccc1C(=O)O", "CC(=O)Oc1ccccc1C(=O)N"),
    ("benzene vs toluene (added methyl)",
     "c1ccccc1", "Cc1ccccc1"),
    ("benzene vs pyridine (one ring atom C -> N)",
     "c1ccccc1", "c1ccncc1"),
    ("benzene vs cyclohexane (aromatic vs saturated ring)",
     "c1ccccc1", "C1CCCCC1"),
]


def main():
    results = {
        "demo": "molecular-identity chemistry verification",
        "payload_type": "canonical SMILES strings (byte-string payloads)",
        "quantum": {
            "simulator": "AerSimulator, matrix_product_state, noiseless",
            "shots": SHOTS,
            "threshold": quantum_verify.DEFAULT_THRESHOLD,
            "fingerprint": "12-block hashrope codeword, symbols mod 16, "
                           "Ry(s * pi/8) product state, full SWAP test",
        },
        "pairs": [],
    }
    print(f"{'case':58s} {'truth':6s} {'classical':10s} "
          f"{'hamming':>7s} {'analytic':>8s} {'est. P(0)':>9s} {'quantum':7s}")
    for name, ref, cand in PAIRS:
        c = classical_verify.verify_pair(ref, cand)
        q = quantum_verify.verify_pair(ref, cand, shots=SHOTS)
        results["pairs"].append({
            "case": name,
            "reference_smiles": ref,
            "candidate_smiles": cand,
            "ground_truth_equal": ref == cand,
            "classical": c,
            "quantum": q,
        })
        print(f"{name:58s} {str(ref == cand):6s} "
              f"{('equal' if c['rope_equal'] else 'differ'):10s} "
              f"{q['codeword_hamming']:7d} {q['analytic_p0']:8.4f} "
              f"{q['estimated_p0']:9.4f} "
              f"{'equal' if q['decision_equal'] else 'differ':7s}")
    out = Path(__file__).with_name("results.json")
    out.write_text(json.dumps(results, indent=2))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
