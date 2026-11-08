"""Bell-basis (destructive SWAP test) verification for qhashrope.

Experiment 3 from the Qiskit Fall Fest 2026 deck: instead of 24 separate
3-qubit per-bit SWAP tests (two_server_experiment.py) or one monolithic
49-qubit SWAP network, verify a pair of 24-qubit Golay fingerprints with
ONE 48-qubit circuit that Bell-measures every bit position
(Garcia-Escartin & Chamorro-Posada destructive SWAP test):

    for each position j:  CNOT A_j -> B_j,  H on A_j,  measure both.

A position lands in the Psi sector (outcomes 01 or 11, i.e. the B_j
outcome bit is 1) iff the two codeword bits differ, and in the Phi sector
(00 or 10) iff they agree; for basis-state fingerprints this is exact.
Decision rule, identical to the two-server per-bit protocol: a position
is decided differ by majority over shots (Psi fraction > 0.5), and the
pair is decided EQUAL iff decided-differ positions <= 3 (Golay radius-3
recombination). A per-shot vote (pair equal iff a majority of individual
shots show <= 3 differ positions) is reported as a secondary rule.

Test set: the same 13 comparisons as two_server_experiment.py (control
identical segment, 9 seeded DNA pairs, 3 chemistry pairs); the set is
cross-checked against two_server_results.json before anything runs.

Noise: qhashrope.qnoise.depolarizing(0.02), the identical model and
simulator construction as two_server_experiment.py. Shots: 4096.
"""

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qiskit import QuantumCircuit, transpile

from qhashrope import quantum_verify as qv
from qhashrope import qnoise
from qhashrope import sequences

P = 0.02
SHOTS = 4096
RADIUS = 3
ROOT = Path(__file__).resolve().parent


def build_pairs():
    """The 13 comparisons of two_server_experiment.py, same order."""
    out = []
    ctrl = sequences.make_segment(random.Random(999))
    out.append({
        "name": "CONTROL identical (independent segment)",
        "reference": ctrl, "candidate": ctrl,
    })
    _, pairs = sequences.make_pair_set()
    chosen = []
    for mut, k in ((0, 3), (1, 3), (10, 3)):
        chosen += [p for p in pairs if p["mutations"] == mut][:k]
    for p in chosen:
        name = "DNA identical" if p["equal"] else f"DNA {p['mutations']} substitutions"
        out.append({"name": name, "reference": p["reference"],
                    "candidate": p["candidate"]})
    chem = [
        ("aspirin vs amide analog", "CC(=O)Oc1ccccc1C(=O)O", "CC(=O)Oc1ccccc1C(=O)N"),
        ("benzene vs cyclohexane", "c1ccccc1", "C1CCCCC1"),
        ("aspirin vs aspirin (identical)", "CC(=O)Oc1ccccc1C(=O)O", "CC(=O)Oc1ccccc1C(=O)O"),
    ]
    for name, a, b in chem:
        out.append({"name": name, "reference": a, "candidate": b})
    return out


def cross_check_test_set(pairs):
    """Abort unless the rebuilt pairs reproduce the recorded Hamming
    distances of two_server_results.json, in order."""
    rec = json.load(open(ROOT / "two_server_results.json"))
    expected = [(rec["control"]["pair"], rec["control"]["codeword_hamming"])]
    expected += [(r["pair"], r["codeword_hamming"]) for r in rec["pairs"]]
    got = [(p["name"], qv.codeword_hamming(qv.codeword(p["reference"]),
                                            qv.codeword(p["candidate"])))
           for p in pairs]
    if got != expected:
        raise SystemExit(f"TEST SET MISMATCH:\n got      {got}\n expected {expected}")
    return True


def bell_circuit(cw_a, cw_b) -> QuantumCircuit:
    """One 48-qubit destructive-SWAP circuit. Qubit layout: position j
    occupies A = 2j, B = 2j+1; classical bit i = qubit i."""
    L = len(cw_a)
    qc = QuantumCircuit(2 * L, 2 * L)
    qc.compose(qv.fingerprint_circuit(cw_a),
               qubits=list(range(0, 2 * L, 2)), inplace=True)
    qc.compose(qv.fingerprint_circuit(cw_b),
               qubits=list(range(1, 2 * L, 2)), inplace=True)
    for j in range(L):
        qc.cx(2 * j, 2 * j + 1)
        qc.h(2 * j)
    qc.measure(range(2 * L), range(2 * L))
    return qc


def analyse_counts(counts, cw_a, cw_b):
    """Sector analysis of Bell-measurement counts.

    Position j is in the Psi sector for a shot iff the measured B_j bit
    (classical bit 2j+1) is 1. Returns per-position Psi fractions, the
    majority-rule decided-differ count and decision, the per-shot vote
    decision, and majority-rule bit errors against the true codewords.
    """
    L = len(cw_a)
    total = sum(counts.values())
    psi = [0] * L
    shot_dist = {}
    for bitstr, n in counts.items():
        bits = bitstr.replace(" ", "")
        nbits = len(bits)
        dc = 0
        for j in range(L):
            if bits[nbits - 1 - (2 * j + 1)] == "1":
                psi[j] += n
                dc += 1
        shot_dist[dc] = shot_dist.get(dc, 0) + n
    psi_frac = [c / total for c in psi]
    decided = [f > 0.5 for f in psi_frac]
    n_differ = sum(decided)
    bit_errors = sum(1 for j in range(L)
                     if decided[j] != (cw_a[j] != cw_b[j]))
    shots_le_radius = sum(n for dc, n in shot_dist.items() if dc <= RADIUS)
    return {
        "shots": total,
        "psi_fraction": [round(f, 4) for f in psi_frac],
        "n_bits_decided_differ": n_differ,
        "bit_decision_errors": bit_errors,
        "majority_equal": n_differ <= RADIUS,
        "shot_differ_distribution": {str(k): v for k, v in sorted(shot_dist.items())},
        "vote_frac_shots_within_radius": round(shots_le_radius / total, 4),
        "vote_equal": shots_le_radius / total > 0.5,
    }


def run_sim(pairs, noise_model):
    sim = qv.default_sim(noise_model)
    out = []
    for p in pairs:
        cw_a, cw_b = qv.codeword(p["reference"]), qv.codeword(p["candidate"])
        qc = bell_circuit(cw_a, cw_b)
        counts = sim.run(transpile(qc, sim), shots=SHOTS).result().get_counts()
        rec = analyse_counts(counts, cw_a, cw_b)
        rec.update({
            "pair": p["name"],
            "ground_truth_equal": p["reference"] == p["candidate"],
            "codeword_hamming": qv.codeword_hamming(cw_a, cw_b),
        })
        rec["majority_correct"] = rec["majority_equal"] == rec["ground_truth_equal"]
        rec["vote_correct"] = rec["vote_equal"] == rec["ground_truth_equal"]
        out.append(rec)
    return out


def main():
    pairs = build_pairs()
    cross_check_test_set(pairs)
    print(f"test set cross-checked against two_server_results.json: "
          f"{len(pairs)} pairs, Hamming distances match")

    demo_a = qv.codeword("ACGTACGT")
    demo = bell_circuit(demo_a, demo_a)
    abstract = {
        "qubits": demo.num_qubits,
        "ops": {k: int(v) for k, v in demo.count_ops().items()},
        "depth": demo.depth(),
        "two_qubit_gates_cx": int(demo.count_ops().get("cx", 0)),
    }
    print("abstract Bell circuit:", abstract)

    noiseless = run_sim(pairs, None)
    nl_exact = all(
        r["n_bits_decided_differ"] == r["codeword_hamming"]
        and r["bit_decision_errors"] == 0 and r["majority_correct"]
        for r in noiseless)
    print(f"noiseless: exact decided-differ == true Hamming on all pairs: {nl_exact}")
    for r in noiseless:
        if not (r["n_bits_decided_differ"] == r["codeword_hamming"]):
            print("  NOISELESS MISMATCH:", r["pair"], r["n_bits_decided_differ"],
                  "vs true", r["codeword_hamming"])

    noisy = run_sim(pairs, qnoise.depolarizing(P))
    n_maj = sum(r["majority_correct"] for r in noisy)
    n_vote = sum(r["vote_correct"] for r in noisy)
    tot_bit_err = sum(r["bit_decision_errors"] for r in noisy)
    print(f"p={P}: majority rule {n_maj}/{len(noisy)} correct, "
          f"vote rule {n_vote}/{len(noisy)}, bit errors {tot_bit_err}")
    for r in noisy:
        print(f"  {r['pair']:38s} truth={'equal' if r['ground_truth_equal'] else 'differ':6s} "
              f"hamming={r['codeword_hamming']:2d} decided={r['n_bits_decided_differ']:2d} "
              f"bit_err={r['bit_decision_errors']} "
              f"maj={'OK' if r['majority_correct'] else 'WRONG'} "
              f"vote={'OK' if r['vote_correct'] else 'WRONG'} "
              f"vote_frac={r['vote_frac_shots_within_radius']}")

    results = {
        "p": P, "shots": SHOTS, "radius": RADIUS,
        "abstract_circuit": abstract,
        "noiseless": noiseless,
        "noiseless_exact": nl_exact,
        "noisy": noisy,
        "noisy_majority_correct": n_maj,
        "noisy_vote_correct": n_vote,
        "noisy_bit_errors": tot_bit_err,
    }
    with open(ROOT / "bell_sim_results.json", "w") as fh:
        json.dump(results, fh, indent=2)
    print("wrote bell_sim_results.json")

    ok = nl_exact and n_maj == len(pairs)
    print("VALIDATION:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
