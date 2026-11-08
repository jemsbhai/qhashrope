"""Demo for the cell-line-authentication use case.

STR marker profile records (the standard short tandem repeat panel used
for human cell line authentication) compared with classical hashrope
and the quantum fingerprint SWAP test (fixed Golay encoding), noiseless
MPS, 4096 shots, global threshold 0.75. Pairs: a sample profile
identical to the reference profile; one marker differing by one allele;
a different cell line's profile. Profiles are illustrative records in
the usual published format. The identical pair is additionally run
under depolarizing noise p = 0.02 in both the monolithic circuit and
the two-server per-bit decomposition (Golay radius-3 decision),
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

PROFILE = (
    "CELL|line:HeLa|source:reference-bank"
    "|AMEL:X|CSF1PO:9,10|D13S317:12,13.3|D16S539:9,10|D5S818:11,12"
    "|D7S820:8,12|TH01:7,9.3|TPOX:8,12|vWA:16,18"
)
PROFILE_MARKER = PROFILE.replace("|TH01:7,9.3|", "|TH01:7,8|")
PROFILE_OTHER = (
    "CELL|line:HEK293|source:reference-bank"
    "|AMEL:X|CSF1PO:11,12|D13S317:12,14|D16S539:9,13|D5S818:8,9"
    "|D7S820:11|TH01:7,8,9|TPOX:11|vWA:16,19"
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
        ("sample profile identical to the reference profile",
         PROFILE, PROFILE),
        ("one marker differing by one allele (TH01 9.3 to 8)",
         PROFILE, PROFILE_MARKER),
        ("a different cell line's profile (HEK293)",
         PROFILE, PROFILE_OTHER),
    ]
    results = {
        "demo": "cell line authentication",
        "payload_type": "STR marker profile records "
                        "(cell line authentication panel)",
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

    ts = two_server_run(PROFILE, PROFILE)
    ts["case"] = "identical profile pair under depolarizing noise"
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
