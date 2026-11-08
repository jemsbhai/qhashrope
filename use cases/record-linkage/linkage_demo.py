"""Demo for the record-linkage use case.

Fictional person-record strings (fielded, semicolon-separated) compared
with classical hashrope and the quantum fingerprint SWAP test (fixed Golay
encoding), noiseless MPS, 4096 shots, global threshold 0.75. Pairs: the
same record on both sides; one field differing by one character (a DOB
digit); a different person. All people are invented. Writes results.json.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from qhashrope import classical_verify, quantum_verify  # noqa: E402

SHOTS = 4096

REC = ("LAST=DOE;FIRST=JANE;MID=Q;DOB=1990-04-12;ID=X7845120;"
       "ZIP=32901;PLAN=GOLD;PCP=DR-4417")
REC_DOB = ("LAST=DOE;FIRST=JANE;MID=Q;DOB=1990-04-13;ID=X7845120;"
           "ZIP=32901;PLAN=GOLD;PCP=DR-4417")
OTHER = ("LAST=SMITH;FIRST=JOHN;MID=R;DOB=1985-11-30;ID=Y2093814;"
         "ZIP=10001;PLAN=SILVER;PCP=DR-9021")


def main():
    pairs = [
        ("same record held by both institutions", REC, REC),
        ("one field differs by one character (DOB day)", REC, REC_DOB),
        ("a different person", REC, OTHER),
    ]
    results = {
        "demo": "record linkage without disclosure",
        "payload_type": "fictional fielded person-record strings",
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
        print(f"{name:50s} truth={str(truth):5s} "
              f"P(0)={q['estimated_p0']:.4f} "
              f"quantum={'equal' if q['decision_equal'] else 'differ':6s} "
              f"correct={q['decision_equal'] == truth}")
    out = Path(__file__).with_name("results.json")
    out.write_text(json.dumps(results, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
