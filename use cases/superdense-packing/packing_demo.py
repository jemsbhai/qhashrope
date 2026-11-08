"""Demo for the superdense-packing use case (the pack stage itself).

Superdense coding trials: 20 trials of 8-bit payloads (4 Bell pairs,
2 bits per transmitted qubit), at three noise conditions: noiseless,
depolarizing p=0.01, depolarizing p=0.05 (Aer noise model on all gates).
Records message accuracy and bit accuracy per condition.
Writes results.json next to this script.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from qhashrope import qnoise, quantum_pack  # noqa: E402

SHOTS = 1024
TRIALS = 20


def main():
    results = {
        "demo": "entanglement-assisted dense packing (superdense coding)",
        "payload": "8 classical bits per trial on 4 transmitted qubits "
                   "(4 pre-shared Bell pairs)",
        "shots": SHOTS,
        "trials_per_condition": TRIALS,
        "conditions": {},
    }
    for label, p in (("noiseless", None), ("depolarizing p=0.01", 0.01),
                     ("depolarizing p=0.05", 0.05)):
        nm = qnoise.depolarizing(p) if p else None
        r = quantum_pack.run_trials(n_trials=TRIALS, shots=SHOTS,
                                    noise_model=nm)
        results["conditions"][label] = {
            "message_accuracy": r["message_accuracy"],
            "bit_accuracy": r["bit_accuracy"],
        }
        print(f"{label:22s} message acc={r['message_accuracy']:.2f} "
              f"bit acc={r['bit_accuracy']:.4f}")
    out = Path(__file__).with_name("results.json")
    out.write_text(json.dumps(results, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
