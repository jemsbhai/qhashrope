"""Demo for the genomic-identity-verification use case.

Seeded 96 bp DNA-like segment pairs (identical / 1 / 3 / 10 substitutions)
through both verifiers: classical hashrope (exact) and the quantum
fingerprint SWAP test (fixed Golay encoding, 2026-11-08), noiseless MPS
simulator, 4096 shots, global threshold 0.75.

Writes results.json next to this script. Run with the project venv.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from qhashrope import classical_verify, quantum_verify, sequences  # noqa: E402

SHOTS = 4096


def main():
    _, pairs = sequences.make_pair_set(n_per_class=(3, 3, 3, 3))
    sim = quantum_verify.default_sim()
    results = {
        "demo": "genomic identity verification",
        "payload_type": "seeded 96 bp DNA-like segments",
        "quantum": {
            "simulator": "AerSimulator, matrix_product_state, noiseless",
            "shots": SHOTS,
            "threshold": quantum_verify.DEFAULT_THRESHOLD,
            "fingerprint": "12 position-seeded block symbols (mod 4096), "
                           "odd-weight fold to a 12-bit message, extended "
                           "Golay (24,12,8) encoding, orthogonal bit states, "
                           "full SWAP test",
        },
        "pairs": [],
    }
    correct_q = correct_c = 0
    for p in pairs:
        c = classical_verify.verify_pair(p["reference"], p["candidate"])
        q = quantum_verify.verify_pair(p["reference"], p["candidate"],
                                       shots=SHOTS, sim=sim)
        ok_q = q["decision_equal"] == p["equal"]
        ok_c = c["rope_equal"] == p["equal"]
        correct_q += ok_q
        correct_c += ok_c
        results["pairs"].append({
            "mutations": p["mutations"],
            "ground_truth_equal": p["equal"],
            "classical_rope_equal": c["rope_equal"],
            "quantum": q,
            "quantum_correct": ok_q,
        })
        print(f"mut={p['mutations']:2d} truth={str(p['equal']):5s} "
              f"classical={'equal' if c['rope_equal'] else 'differ':6s} "
              f"P(0)={q['estimated_p0']:.4f} "
              f"quantum={'equal' if q['decision_equal'] else 'differ':6s} "
              f"correct={ok_q}")
    results["classical_accuracy"] = correct_c / len(pairs)
    results["quantum_accuracy"] = correct_q / len(pairs)
    print(f"\nclassical {correct_c}/{len(pairs)}, quantum {correct_q}/{len(pairs)}")
    out = Path(__file__).with_name("results.json")
    out.write_text(json.dumps(results, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
