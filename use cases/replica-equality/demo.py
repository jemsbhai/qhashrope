"""Replica equality demo (ledger record strings, about 3.4 KB).

Constraint: the link between replica holders is constrained; both send an O(log n) qubit fingerprint to a referee instead of the record, and the position of a difference must not matter.

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

def _ledger() -> str:
    lines = []
    for i in range(60):
        lines.append(f"2026-11-08T00:{i:02d}:00|shard=3|seq={i:06d}|"
                     f"value={0x9E3779B9 * (i + 1) % (1 << 32):08x}|ok")
    return "\n".join(lines) + "\n"


_ref = _ledger()
_end = _ref[:-2] + ("0" if _ref[-2] != "0" else "1") + _ref[-1]
_start = ("X" if _ref[0] != "X" else "Y") + _ref[1:]
PAIRS = [
    ("replica vs itself (identical)", _ref, _ref),
    ("replica with one byte changed at the end", _ref, _end),
    ("replica with one byte changed at the start", _ref, _start),
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
