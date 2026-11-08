"""Quantum chemistry result verification demo (result records).

Constraint: result records run from kilobytes to tens of gigabytes and may be restricted; a referee checks agreement from fingerprints only and sees neither record.

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

PAIRS = [
    ('same result record from two machines (identical)',
     'RESULT|METHOD:B3LYP|BASIS:6-31G(d)|E_HARTREE:-76.40896132\nGEOMETRY\nO  0.000000  0.000000  0.117176\nH  0.000000  0.756453 -0.468703\nH  0.000000 -0.756453 -0.468703\nEND\n', 'RESULT|METHOD:B3LYP|BASIS:6-31G(d)|E_HARTREE:-76.40896132\nGEOMETRY\nO  0.000000  0.000000  0.117176\nH  0.000000  0.756453 -0.468703\nH  0.000000 -0.756453 -0.468703\nEND\n'),
    ('one coordinate changed in the third decimal',
     'RESULT|METHOD:B3LYP|BASIS:6-31G(d)|E_HARTREE:-76.40896132\nGEOMETRY\nO  0.000000  0.000000  0.117176\nH  0.000000  0.756453 -0.468703\nH  0.000000 -0.756453 -0.468703\nEND\n', 'RESULT|METHOD:B3LYP|BASIS:6-31G(d)|E_HARTREE:-76.40896132\nGEOMETRY\nO  0.000000  0.000000  0.117176\nH  0.000000  0.756453 -0.469703\nH  0.000000 -0.756453 -0.468703\nEND\n'),
    ('a different geometry (methane record)',
     'RESULT|METHOD:B3LYP|BASIS:6-31G(d)|E_HARTREE:-76.40896132\nGEOMETRY\nO  0.000000  0.000000  0.117176\nH  0.000000  0.756453 -0.468703\nH  0.000000 -0.756453 -0.468703\nEND\n', 'RESULT|METHOD:B3LYP|BASIS:6-31G(d)|E_HARTREE:-40.51839174\nGEOMETRY\nC  0.000000  0.000000  0.000000\nH  0.629118  0.629118  0.629118\nH -0.629118 -0.629118  0.629118\nH -0.629118  0.629118 -0.629118\nH  0.629118 -0.629118 -0.629118\nEND\n'),
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
