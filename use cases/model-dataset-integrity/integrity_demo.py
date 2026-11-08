"""Demo for the model-dataset-integrity use case.

Byte payloads standing in for a model checkpoint record (header + a
weight-digest body), verified with classical hashrope and the quantum
fingerprint SWAP test (fixed Golay encoding), noiseless MPS, 4096 shots,
global threshold 0.75. Pairs: identical record; a copy differing in three
bytes; a different checkpoint. Writes results.json next to this script.
"""

import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from qhashrope import classical_verify, quantum_verify  # noqa: E402

SHOTS = 4096


def checkpoint(seed: int, tag: str) -> str:
    rng = random.Random(seed)
    body = ",".join("%08x" % rng.getrandbits(32) for _ in range(360))
    return (f"MODEL:resnet-mini;TAG:{tag};LAYERS:12;PARAMS:184320\n"
            f"WEIGHTS_SHA_BLOCK:{body}\nEND\n")


def main():
    ref = checkpoint(4242, "certified-v7")
    few = list(ref)
    for pos in (500, 1500, 2500):  # three bytes changed inside the body
        few[pos] = "0" if few[pos] != "0" else "1"
    few = "".join(few)
    pairs = [
        ("certified record vs itself (identical)", ref, ref),
        ("certified record vs copy with 3 bytes changed", ref, few),
        ("certified record vs a different checkpoint",
         ref, checkpoint(999, "candidate-v8")),
    ]
    results = {
        "demo": "model/dataset integrity attestation",
        "payload_type": "synthetic checkpoint record strings (~3.2 KB)",
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
            "bytes_differing": sum(1 for x, y in zip(a, b) if x != y)
                                 + abs(len(a) - len(b)),
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
