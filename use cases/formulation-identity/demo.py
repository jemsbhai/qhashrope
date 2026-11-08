"""Formulation identity demo (sponsor vs contract manufacturer).

Constraint: the composition is a trade secret in both directions; no proportions, ingredients, or doses cross, and equality is the only permitted output.

Runs the case's documented record pairs through both qhashrope verifiers:
classical hashrope exact equality and the quantum fingerprint SWAP test
(Golay (24,12,8) encoding, noiseless MPS simulator, 4096 shots, global
threshold 0.75). Prints a per-pair verdict table and a summary line.

The identical pair is also run under depolarizing noise p = 0.02 in the
two-server per-bit form (24 split SWAP tests, Golay radius-3 decision),
following two_server_experiment.py at the repo root.

Run:  python demo.py   (from this folder, with the project venv)
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from qiskit import QuantumCircuit, transpile  # noqa: E402

from qhashrope import qnoise  # noqa: E402

from qhashrope import classical_verify, quantum_verify  # noqa: E402

SHOTS = 4096

PAIRS = [
    ('identical formulation, sponsor vs manufacturer',
     'FORM|product:tablet-A|api:paracetamol 500mg|excipients:MCC 120mg,lactose-monohydrate 80mg,PVP-K30 25mg,croscarmellose-Na 15mg,Mg-stearate 5mg|coating:HPMC 10mg|spec:QS-2026-114', 'FORM|product:tablet-A|api:paracetamol 500mg|excipients:MCC 120mg,lactose-monohydrate 80mg,PVP-K30 25mg,croscarmellose-Na 15mg,Mg-stearate 5mg|coating:HPMC 10mg|spec:QS-2026-114'),
    ('one proportion changed (Mg-stearate 5mg to 6mg)',
     'FORM|product:tablet-A|api:paracetamol 500mg|excipients:MCC 120mg,lactose-monohydrate 80mg,PVP-K30 25mg,croscarmellose-Na 15mg,Mg-stearate 5mg|coating:HPMC 10mg|spec:QS-2026-114', 'FORM|product:tablet-A|api:paracetamol 500mg|excipients:MCC 120mg,lactose-monohydrate 80mg,PVP-K30 25mg,croscarmellose-Na 15mg,Mg-stearate 6mg|coating:HPMC 10mg|spec:QS-2026-114'),
    ('a different formulation (suspension product)',
     'FORM|product:tablet-A|api:paracetamol 500mg|excipients:MCC 120mg,lactose-monohydrate 80mg,PVP-K30 25mg,croscarmellose-Na 15mg,Mg-stearate 5mg|coating:HPMC 10mg|spec:QS-2026-114', 'FORM|product:suspension-B|api:ibuprofen 100mg/5mL|excipients:sucrose 2000mg,xanthan-gum 45mg,citric-acid 30mg,sodium-benzoate 25mg,flavor-orange 12mg|vehicle:purified-water qs|spec:QS-2026-208'),
]

P_NOISE = 0.02
THRESH = quantum_verify.DEFAULT_THRESHOLD


def per_bit_p0(cw_a, cw_b, sim):
    out = []
    for j in range(len(cw_a)):
        qc = QuantumCircuit(3, 1)
        qc.compose(quantum_verify.fingerprint_circuit([cw_a[j]]),
                   qubits=[1], inplace=True)
        qc.compose(quantum_verify.fingerprint_circuit([cw_b[j]]),
                   qubits=[2], inplace=True)
        qc.h(0)
        qc.cswap(0, 1, 2)
        qc.h(0)
        qc.measure(0, 0)
        counts = sim.run(transpile(qc, sim), shots=SHOTS).result().get_counts()
        out.append(counts.get("0", 0) / SHOTS)
    return out

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

    # Two-server check on the identical pair under depolarizing noise.
    ref, cand = PAIRS[0][1], PAIRS[0][2]
    noise = qnoise.depolarizing(P_NOISE)
    nsim = quantum_verify.default_sim(noise)
    cw_a, cw_b = quantum_verify.codeword(ref), quantum_verify.codeword(cand)
    mono = quantum_verify.estimate_p0(cw_a, cw_b, shots=SHOTS, sim=nsim,
                                      noise_model=noise)
    p0s = per_bit_p0(cw_a, cw_b, nsim)
    n_differ = sum(1 for p in p0s if p < THRESH)
    ts_equal = n_differ <= 3
    print(f"two-server (identical pair, p={P_NOISE}): monolithic "
          f"P(0)={mono:.4f}, decided-differ bits={n_differ}/24, "
          f"verdict={'equal' if ts_equal else 'differ'} "
          f"({'PASS' if ts_equal else 'FAIL'})")

    print(f"SUMMARY: {n_pass}/{len(PAIRS)} pairs PASS "
          f"(classical {n_c}/{len(PAIRS)}, quantum {n_q}/{len(PAIRS)})")


if __name__ == "__main__":
    main()
