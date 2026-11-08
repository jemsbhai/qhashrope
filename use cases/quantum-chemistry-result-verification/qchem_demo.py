"""Demo for the quantum-chemistry-result-verification use case.

Computation-result record strings (method header + geometry block)
compared with classical hashrope and the quantum fingerprint SWAP test
(fixed Golay encoding), noiseless MPS, 4096 shots, global threshold 0.75.
Pairs: identical records from two "machines"; one record with a single
coordinate changed in the third decimal; a record for a different
geometry. Writes results.json next to this script.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from qhashrope import classical_verify, quantum_verify  # noqa: E402

SHOTS = 4096

HEADER = "RESULT|METHOD:B3LYP|BASIS:6-31G(d)|E_HARTREE:-76.40896132\nGEOMETRY\n"
WATER = (HEADER +
         "O  0.000000  0.000000  0.117176\n"
         "H  0.000000  0.756453 -0.468703\n"
         "H  0.000000 -0.756453 -0.468703\nEND\n")
WATER_3RD_DECIMAL = (HEADER +
                     "O  0.000000  0.000000  0.117176\n"
                     "H  0.000000  0.756453 -0.469703\n"
                     "H  0.000000 -0.756453 -0.468703\nEND\n")
METHANE = ("RESULT|METHOD:B3LYP|BASIS:6-31G(d)|E_HARTREE:-40.51839174\n"
           "GEOMETRY\n"
           "C  0.000000  0.000000  0.000000\n"
           "H  0.629118  0.629118  0.629118\n"
           "H -0.629118 -0.629118  0.629118\n"
           "H -0.629118  0.629118 -0.629118\n"
           "H  0.629118 -0.629118 -0.629118\nEND\n")


def main():
    pairs = [
        ("same result record from two machines (identical)", WATER, WATER),
        ("one coordinate changed in the third decimal",
         WATER, WATER_3RD_DECIMAL),
        ("a different geometry (methane record)", WATER, METHANE),
    ]
    results = {
        "demo": "quantum chemistry result verification",
        "payload_type": "computation-result record strings "
                        "(method header + geometry block)",
        "quantum": {
            "simulator": "AerSimulator, matrix_product_state, noiseless",
            "shots": SHOTS,
            "threshold": quantum_verify.DEFAULT_THRESHOLD,
            "fingerprint": "Golay (24,12,8) encoded fingerprint, SWAP test",
        },
        "pairs": [],
    }
    for name, a, b in pairs:
        c = classical_verify.verify_pair(a, b)
        q = quantum_verify.verify_pair(a, b, shots=SHOTS)
        truth = a == b
        results["pairs"].append({
            "case": name,
            "ground_truth_equal": truth,
            "classical_rope_equal": c["rope_equal"],
            "quantum": q,
            "quantum_correct": q["decision_equal"] == truth,
        })
        print(f"{name:52s} truth={str(truth):5s} "
              f"P(0)={q['estimated_p0']:.4f} "
              f"quantum={'equal' if q['decision_equal'] else 'differ':6s} "
              f"correct={q['decision_equal'] == truth}")
    out = Path(__file__).with_name("results.json")
    out.write_text(json.dumps(results, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
