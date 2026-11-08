"""Demo for the replica-equality use case.

Long record strings (~4 KB of ledger-style lines) compared with classical
hashrope and the quantum fingerprint SWAP test (fixed Golay encoding),
noiseless MPS, 4096 shots, global threshold 0.75. Pairs: identical
replicas; one byte changed at the very end; one byte changed at the very
start. Position of the difference must not matter. Writes results.json.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from qhashrope import classical_verify, quantum_verify  # noqa: E402

SHOTS = 4096


def ledger() -> str:
    lines = []
    for i in range(60):
        lines.append(f"2026-11-08T00:{i:02d}:00|shard=3|seq={i:06d}|"
                     f"value={0x9E3779B9 * (i + 1) % (1 << 32):08x}|ok")
    return "\n".join(lines) + "\n"


def main():
    ref = ledger()
    end = ref[:-2] + ("0" if ref[-2] != "0" else "1") + ref[-1]
    start = ("X" if ref[0] != "X" else "Y") + ref[1:]
    pairs = [
        ("replica vs itself (identical)", ref, ref),
        ("replica with one byte changed at the end", ref, end),
        ("replica with one byte changed at the start", ref, start),
    ]
    results = {
        "demo": "replica equality over constrained links",
        "payload_type": "ledger record strings (~4 KB)",
        "record_bytes": len(ref),
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
        print(f"{name:46s} truth={str(truth):5s} "
              f"P(0)={q['estimated_p0']:.4f} "
              f"quantum={'equal' if q['decision_equal'] else 'differ':6s} "
              f"correct={q['decision_equal'] == truth}")
    out = Path(__file__).with_name("results.json")
    out.write_text(json.dumps(results, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
