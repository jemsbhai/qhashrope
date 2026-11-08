"""Record linkage without disclosure demo (fictional person records).

Constraint: pooling the records is prohibited; equality is the only lawful disclosure between the two institutions. All people are invented.

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
    ('same record held by both institutions',
     'LAST=DOE;FIRST=JANE;MID=Q;DOB=1990-04-12;ID=X7845120;ZIP=32901;PLAN=GOLD;PCP=DR-4417', 'LAST=DOE;FIRST=JANE;MID=Q;DOB=1990-04-12;ID=X7845120;ZIP=32901;PLAN=GOLD;PCP=DR-4417'),
    ('one field differs by one character (DOB day)',
     'LAST=DOE;FIRST=JANE;MID=Q;DOB=1990-04-12;ID=X7845120;ZIP=32901;PLAN=GOLD;PCP=DR-4417', 'LAST=DOE;FIRST=JANE;MID=Q;DOB=1990-04-13;ID=X7845120;ZIP=32901;PLAN=GOLD;PCP=DR-4417'),
    ('a different person',
     'LAST=DOE;FIRST=JANE;MID=Q;DOB=1990-04-12;ID=X7845120;ZIP=32901;PLAN=GOLD;PCP=DR-4417', 'LAST=SMITH;FIRST=JOHN;MID=R;DOB=1985-11-30;ID=Y2093814;ZIP=10001;PLAN=SILVER;PCP=DR-9021'),
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
