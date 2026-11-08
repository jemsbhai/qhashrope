"""Model and dataset integrity attestation demo (checkpoint records).

Constraint: the artifact is gigabyte-scale; the check moves a fingerprint logarithmic in the artifact size instead of the artifact, binding the deployed copy to the certified one.

Runs the case's documented record pairs through both qhashrope verifiers:
classical hashrope exact equality and the quantum fingerprint SWAP test
(Golay (24,12,8) encoding, noiseless MPS simulator, 4096 shots, global
threshold 0.75). Prints a per-pair verdict table and a summary line.

Run:  python demo.py   (from this folder, with the project venv)
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from qhashrope import classical_verify, quantum_verify  # noqa: E402

SHOTS = 4096

import random  # noqa: E402


def _checkpoint(seed: int, tag: str) -> str:
    rng = random.Random(seed)
    body = ",".join("%08x" % rng.getrandbits(32) for _ in range(360))
    return (f"MODEL:resnet-mini;TAG:{tag};LAYERS:12;PARAMS:184320\n"
            f"WEIGHTS_SHA_BLOCK:{body}\nEND\n")


_ref = _checkpoint(4242, "certified-v7")
_few = list(_ref)
for _pos in (500, 1500, 2500):  # three bytes changed inside the body
    _few[_pos] = "0" if _few[_pos] != "0" else "1"
PAIRS = [
    ("certified record vs itself (identical)", _ref, _ref),
    ("certified record vs copy with 3 bytes changed",
     _ref, "".join(_few)),
    ("certified record vs a different checkpoint",
     _ref, _checkpoint(999, "candidate-v8")),
]

def main():
    sim = quantum_verify.default_sim()
    print(f"{'pair':<62s} {'classical':<9s} {'P(0)':>7s} "
          f"{'quantum':<7s} {'expected':<8s} verdict")
    n_pass = n_c = n_q = 0
    for name, ref, cand in PAIRS:
        expected = ref == cand
        c = classical_verify.verify_pair(ref, cand)
        q = quantum_verify.verify_pair(ref, cand, shots=SHOTS, sim=sim)
        ok_c = c["rope_equal"] == expected
        ok_q = q["decision_equal"] == expected
        ok = ok_c and ok_q
        n_pass += ok
        n_c += ok_c
        n_q += ok_q
        print(f"{name:<62s} "
              f"{'equal' if c['rope_equal'] else 'differ':<9s} "
              f"{q['estimated_p0']:7.4f} "
              f"{'equal' if q['decision_equal'] else 'differ':<7s} "
              f"{'equal' if expected else 'differ':<8s} "
              f"{'PASS' if ok else 'FAIL'}")

    print(f"SUMMARY: {n_pass}/{len(PAIRS)} pairs PASS "
          f"(classical {n_c}/{len(PAIRS)}, quantum {n_q}/{len(PAIRS)})")


if __name__ == "__main__":
    main()
