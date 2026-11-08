"""Compound library deduplication without disclosure demo.

Constraint: neither organization's library is pooled or disclosed; the
library itself is the trade secret, and the only permitted output per
cross pair is same or different.

Two small fictional libraries of canonical SMILES (8 compounds each)
with a planted overlap of exactly 4 compounds. All 64 cross pairs are
run through both qhashrope verifiers: classical hashrope exact equality
and the quantum fingerprint SWAP test (Golay (24,12,8) encoding,
noiseless MPS simulator, 4096 shots, global threshold 0.75). The demo
passes iff every pair's verdicts match the expected equality and the
recovered match set equals the planted duplicate set exactly.

Run:  python demo.py   (from this folder, with the project venv)
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from qhashrope import classical_verify, quantum_verify  # noqa: E402

SHOTS = 4096

LIBRARY_A = {
    "aspirin": "CC(=O)Oc1ccccc1C(=O)O",
    "ibuprofen": "CC(C)Cc1ccc(C(C)C(=O)O)cc1",
    "caffeine": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
    "paracetamol": "CC(=O)Nc1ccc(O)cc1",
    "benzene": "c1ccccc1",
    "toluene": "Cc1ccccc1",
    "ethanol": "CCO",
    "phenol": "Oc1ccccc1",
}

LIBRARY_B = {
    "pyridine": "c1ccncc1",
    "caffeine": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
    "cyclohexane": "C1CCCCC1",
    "aspirin": "CC(=O)Oc1ccccc1C(=O)O",
    "acetone": "CC(C)=O",
    "benzene": "c1ccccc1",
    "methanol": "CO",
    "ethanol": "CCO",
}

PLANTED = {"aspirin", "benzene", "caffeine", "ethanol"}


def main():
    sim = quantum_verify.default_sim()
    print(f"{'cross pair (A vs B)':<38s} {'classical':<9s} {'P(0)':>7s} "
          f"{'quantum':<7s} {'expected':<8s} verdict")
    n_pass = n_c = n_q = 0
    quantum_matches = set()
    classical_matches = set()
    total = 0
    for name_a, smi_a in LIBRARY_A.items():
        for name_b, smi_b in LIBRARY_B.items():
            total += 1
            expected = smi_a == smi_b
            c = classical_verify.verify_pair(smi_a, smi_b)
            q = quantum_verify.verify_pair(smi_a, smi_b, shots=SHOTS,
                                           sim=sim)
            if q["decision_equal"]:
                quantum_matches.add(name_a)
            if c["rope_equal"]:
                classical_matches.add(name_a)
            ok_c = c["rope_equal"] == expected
            ok_q = q["decision_equal"] == expected
            ok = ok_c and ok_q
            n_pass += ok
            n_c += ok_c
            n_q += ok_q
            print(f"{name_a + ' vs ' + name_b:<38s} "
                  f"{'equal' if c['rope_equal'] else 'differ':<9s} "
                  f"{q['estimated_p0']:7.4f} "
                  f"{'equal' if q['decision_equal'] else 'differ':<7s} "
                  f"{'equal' if expected else 'differ':<8s} "
                  f"{'PASS' if ok else 'FAIL'}")
    exact = quantum_matches == PLANTED and classical_matches == PLANTED
    print(f"planted duplicates: {sorted(PLANTED)}")
    print(f"quantum match set:  {sorted(quantum_matches)}")
    print(f"classical match set: {sorted(classical_matches)}")
    print(f"SUMMARY: {n_pass}/{total} cross pairs PASS "
          f"(classical {n_c}/{total}, quantum {n_q}/{total}), "
          f"match set exact: {exact}")


if __name__ == "__main__":
    main()
