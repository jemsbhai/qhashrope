"""Two-server / per-block decomposition experiment for qhashrope noisy verify.

Question: the fixed (Golay) fingerprint's monolithic 49-qubit SWAP test
contracts identical pairs to P(0) ~ 0.72-0.74 at depolarizing p = 0.02,
below the 0.75 threshold (RESULTS.md, stage 5). The fingerprint state is
a product state over the 24 Golay codeword bits, and for two basis-state
fingerprints |a>, |b> the overlap factorises exactly:

    |<a|b>|^2 = prod_j delta(a_j, b_j).

So the single deep SWAP network can be replaced by 24 independent
3-qubit per-bit SWAP tests (ancilla + 1 + 1 qubits, <= 5 noisy gates
each), whose classical estimates the client recombines - the same
architectural move as the two-server secret-sharing paper: many small
partial computations, exact classical recombination.

Recombinations tested (all decisions fixed in advance, nothing tuned):
  R1 product   : f_j = clip(2*p0_j - 1, 0, 1); O = prod f_j;
                 global P(0) = (1 + O)/2; equal iff >= 0.75.
  R2 AND       : bit decided equal iff p0_j >= 0.75; equal iff all 24.
  R3 Golay     : d = #bits decided differ; equal iff d <= 3
                 (unique-decoding radius of the (24,12,8) code).
  R4 relative  : like R1 but threshold = (C + 0.5)/2 where C is the
                 product estimate of an independent known-identical
                 control pair measured under the same noise (common-mode
                 calibration, the legacy stage-5 analogue).

Noise: qhashrope.qnoise.depolarizing(0.02) - identical model to
RESULTS.md. Simulator: qv.default_sim (MPS). Shots: 4096 per circuit.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qiskit import QuantumCircuit, transpile

from qhashrope import quantum_verify as qv
from qhashrope import qnoise
from qhashrope import sequences

P = 0.02
SHOTS = 4096
THRESH = 0.75

noise = qnoise.depolarizing(P)
sim = qv.default_sim(noise)


def per_bit_swap_circuit(bit_a: int, bit_b: int) -> QuantumCircuit:
    qc = QuantumCircuit(3, 1)
    qc.compose(qv.fingerprint_circuit([bit_a]), qubits=[1], inplace=True)
    qc.compose(qv.fingerprint_circuit([bit_b]), qubits=[2], inplace=True)
    qc.h(0)
    qc.cswap(0, 1, 2)
    qc.h(0)
    qc.measure(0, 0)
    return qc


def per_bit_p0(cw_a, cw_b):
    out = []
    for j in range(len(cw_a)):
        qc = per_bit_swap_circuit(cw_a[j], cw_b[j])
        counts = sim.run(transpile(qc, sim), shots=SHOTS).result().get_counts()
        out.append(counts.get("0", 0) / SHOTS)
    return out


def recombine(p0s):
    f = [min(1.0, max(0.0, 2 * p - 1)) for p in p0s]
    prod = 1.0
    for x in f:
        prod *= x
    global_p0 = (1 + prod) / 2
    n_differ = sum(1 for p in p0s if p < THRESH)
    return {
        "per_bit_p0": [round(p, 4) for p in p0s],
        "product_overlap": prod,
        "product_global_p0": global_p0,
        "R1_product_equal": global_p0 >= THRESH,
        "n_bits_decided_differ": n_differ,
        "R2_and_equal": n_differ == 0,
        "R3_golay_equal": n_differ <= 3,
    }


def run_pair(name, ref, cand):
    cw_a, cw_b = qv.codeword(ref), qv.codeword(cand)
    mono = qv.estimate_p0(cw_a, cw_b, shots=SHOTS, sim=sim, noise_model=noise)
    rec = recombine(per_bit_p0(cw_a, cw_b))
    rec.update({
        "pair": name,
        "ground_truth_equal": ref == cand,
        "codeword_hamming": qv.codeword_hamming(cw_a, cw_b),
        "monolithic_p0": mono,
        "monolithic_equal": mono >= THRESH,
    })
    return rec


def main():
    results = {"p": P, "shots": SHOTS, "threshold": THRESH, "pairs": []}

    # Gate counts: monolithic vs per-bit.
    demo_a = qv.codeword("ACGTACGT")
    mono_qc = qv.swap_test_circuit(demo_a, demo_a)
    bit_qc = per_bit_swap_circuit(1, 1)
    results["circuits"] = {
        "monolithic_qubits": mono_qc.num_qubits,
        "monolithic_ops": dict(mono_qc.count_ops()),
        "per_bit_qubits": bit_qc.num_qubits,
        "per_bit_ops": dict(bit_qc.count_ops()),
    }

    # Control pair for R4: independent segment, known identical.
    import random
    ctrl = sequences.make_segment(random.Random(999))
    ctrl_rec = run_pair("CONTROL identical (independent segment)", ctrl, ctrl)
    results["control"] = ctrl_rec
    c_prod = ctrl_rec["product_global_p0"]
    rel_thresh = (c_prod + 0.5) / 2
    results["relative_threshold"] = rel_thresh

    _, pairs = sequences.make_pair_set()
    chosen = []
    for mut, k in ((0, 3), (1, 3), (10, 3)):
        chosen += [p for p in pairs if p["mutations"] == mut][:k]
    for p in chosen:
        name = f"DNA identical" if p["equal"] else f"DNA {p['mutations']} substitutions"
        results["pairs"].append(run_pair(name, p["reference"], p["candidate"]))

    chem = [
        ("aspirin vs amide analog", "CC(=O)Oc1ccccc1C(=O)O", "CC(=O)Oc1ccccc1C(=O)N"),
        ("benzene vs cyclohexane", "c1ccccc1", "C1CCCCC1"),
        ("aspirin vs aspirin (identical)", "CC(=O)Oc1ccccc1C(=O)O", "CC(=O)Oc1ccccc1C(=O)O"),
    ]
    for name, a, b in chem:
        results["pairs"].append(run_pair(name, a, b))

    for r in results["pairs"] + [results["control"]]:
        r["R4_relative_equal"] = r["product_global_p0"] >= rel_thresh

    with open(Path(__file__).with_name("two_server_results.json"), "w") as fh:
        json.dump(results, fh, indent=2)

    print(json.dumps(results["circuits"], indent=2))
    print(f"relative threshold (from control product {c_prod:.4f}): {rel_thresh:.4f}")
    hdr = f"{'pair':38s} {'true':5s} {'mono':>7s} {'M':1s} {'prod':>7s} {'R1':2s} {'R2':2s} {'R3':2s} {'R4':2s} {'ndiff':>5s}"
    print(hdr)
    for r in results["pairs"] + [results["control"]]:
        print(f"{r['pair']:38s} {str(r['ground_truth_equal']):5s} "
              f"{r['monolithic_p0']:7.4f} {'Y' if r['monolithic_equal'] else 'n':1s} "
              f"{r['product_global_p0']:7.4f} "
              f"{'Y' if r['R1_product_equal'] else 'n':2s} "
              f"{'Y' if r['R2_and_equal'] else 'n':2s} "
              f"{'Y' if r['R3_golay_equal'] else 'n':2s} "
              f"{'Y' if r['R4_relative_equal'] else 'n':2s} "
              f"{r['n_bits_decided_differ']:5d}")


if __name__ == "__main__":
    main()
