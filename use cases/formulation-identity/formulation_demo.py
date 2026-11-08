"""Demo for the formulation-identity use case.

Formulation records (product, active ingredient, excipient proportions)
compared with classical hashrope and the quantum fingerprint SWAP test
(fixed Golay encoding), noiseless MPS, 4096 shots, global threshold
0.75. Pairs: the identical formulation held by the sponsor and by a
contract manufacturer; one component proportion changed; a different
formulation. The equality answer is the only thing the protocol
returns: the manufacturer confirms a match without the protocol ever
transmitting the formulation itself. The identical pair is additionally
run under depolarizing noise p = 0.02 in both the monolithic circuit
and the two-server per-bit decomposition (Golay radius-3 decision),
following two_server_experiment.py at the repo root. Writes
results.json next to this script.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from qiskit import QuantumCircuit, transpile  # noqa: E402

from qhashrope import classical_verify, quantum_verify  # noqa: E402
from qhashrope import qnoise  # noqa: E402

SHOTS = 4096
P_NOISE = 0.02
THRESH = quantum_verify.DEFAULT_THRESHOLD

FORMULATION = (
    "FORM|product:tablet-A|api:paracetamol 500mg"
    "|excipients:MCC 120mg,lactose-monohydrate 80mg,PVP-K30 25mg,"
    "croscarmellose-Na 15mg,Mg-stearate 5mg"
    "|coating:HPMC 10mg|spec:QS-2026-114"
)
FORMULATION_PROP = FORMULATION.replace("Mg-stearate 5mg", "Mg-stearate 6mg")
FORMULATION_OTHER = (
    "FORM|product:suspension-B|api:ibuprofen 100mg/5mL"
    "|excipients:sucrose 2000mg,xanthan-gum 45mg,citric-acid 30mg,"
    "sodium-benzoate 25mg,flavor-orange 12mg"
    "|vehicle:purified-water qs|spec:QS-2026-208"
)


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


def two_server_run(ref, cand):
    noise = qnoise.depolarizing(P_NOISE)
    sim = quantum_verify.default_sim(noise)
    cw_a, cw_b = quantum_verify.codeword(ref), quantum_verify.codeword(cand)
    mono = quantum_verify.estimate_p0(cw_a, cw_b, shots=SHOTS, sim=sim,
                                      noise_model=noise)
    p0s = per_bit_p0(cw_a, cw_b, sim)
    n_differ = sum(1 for p in p0s if p < THRESH)
    return {
        "p_noise": P_NOISE,
        "shots_per_circuit": SHOTS,
        "monolithic_p0": mono,
        "monolithic_decision_equal": mono >= THRESH,
        "per_bit_p0": [round(p, 4) for p in p0s],
        "n_bits_decided_differ": n_differ,
        "codeword_hamming": quantum_verify.codeword_hamming(cw_a, cw_b),
        "two_server_golay_radius": 3,
        "two_server_decision_equal": n_differ <= 3,
        "ground_truth_equal": ref == cand,
    }


def main():
    pairs = [
        ("identical formulation, sponsor vs contract manufacturer",
         FORMULATION, FORMULATION),
        ("one component proportion changed (Mg-stearate 5mg to 6mg)",
         FORMULATION, FORMULATION_PROP),
        ("a different formulation (suspension product)",
         FORMULATION, FORMULATION_OTHER),
    ]
    results = {
        "demo": "formulation identity",
        "payload_type": "formulation records (product, active ingredient, "
                        "excipient proportions)",
        "quantum": {
            "simulator": "AerSimulator, matrix_product_state, noiseless",
            "shots": SHOTS,
            "threshold": THRESH,
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
        print(f"{name:52s} truth={str(truth):5s} "
              f"P(0)={q['estimated_p0']:.4f} "
              f"quantum={'equal' if q['decision_equal'] else 'differ':6s} "
              f"correct={q['decision_equal'] == truth}")

    ts = two_server_run(FORMULATION, FORMULATION)
    ts["case"] = "identical formulation pair under depolarizing noise"
    results["two_server_noisy"] = ts
    print(f"two-server p={P_NOISE}: monolithic P(0)={ts['monolithic_p0']:.4f} "
          f"(equal={ts['monolithic_decision_equal']}), "
          f"decided-differ bits={ts['n_bits_decided_differ']}, "
          f"two-server equal={ts['two_server_decision_equal']}")

    out = Path(__file__).with_name("results.json")
    out.write_text(json.dumps(results, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
