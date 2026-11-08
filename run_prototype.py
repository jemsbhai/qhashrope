#!/usr/bin/env python3
"""Run the full qhashrope prototype suite and write results.json.

Usage:  ~/workspace/.qiskit-venv/bin/python run_prototype.py
"""

import json
import os
import platform
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import qiskit
import qiskit_aer

from qhashrope import (classical_pack, classical_verify, pipeline, qnoise,
                       quantum_pack, quantum_verify, sequences)

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS_SWAP = 4096


def main():
    t_start = time.time()
    results = {
        "environment": {
            "python": platform.python_version(),
            "qiskit": qiskit.__version__,
            "qiskit_aer": qiskit_aer.__version__,
            "multispecqr": __import__("multispecqr").__version__,
            "machine": platform.machine(),
        }
    }

    # ---- Stage 1: classical pack (MultiSpecQR RGB) ----
    img_path = os.path.join(HERE, "packed_rgb.png")
    s1 = classical_pack.roundtrip(pipeline.PAYLOADS, image_path=img_path)
    results["stage1_classical_pack"] = s1
    print("Stage 1 classical pack: all_ok =", s1["all_ok"], s1["decoded"])

    # ---- Stage 2: quantum pack (superdense coding, noiseless) ----
    s2 = quantum_pack.run_trials(n_trials=20, shots=1024)
    results["stage2_quantum_pack"] = {
        k: s2[k] for k in ("n_trials", "shots", "payload_bits_per_trial",
                           "message_accuracy", "bit_accuracy")
    }
    print("Stage 2 quantum pack: message_accuracy =", s2["message_accuracy"],
          " bit_accuracy =", s2["bit_accuracy"])

    # ---- Stages 3+4: verify pairs, classical + quantum ----
    _, pairs = sequences.make_pair_set(n_per_class=(3, 5, 5, 5))
    sim = quantum_verify.default_sim()
    pair_rows = []
    for p in pairs:
        cv = classical_verify.verify_pair(p["reference"], p["candidate"])
        qv = quantum_verify.verify_pair(p["reference"], p["candidate"],
                                        shots=SHOTS_SWAP, sim=sim)
        pair_rows.append({
            "mutations": p["mutations"],
            "ground_truth_equal": p["equal"],
            "classical_fingerprint_match": cv["fingerprint_match"],
            "classical_rope_equal": cv["rope_equal"],
            "codeword_hamming": qv["codeword_hamming"],
            "analytic_p0": qv["analytic_p0"],
            "estimated_p0": qv["estimated_p0"],
            "quantum_decision_equal": qv["decision_equal"],
            "quantum_correct": qv["decision_equal"] == p["equal"],
        })
        print("  pair mut=%2d dH=%2d analytic=%.4f estimated=%.4f correct=%s"
              % (p["mutations"], qv["codeword_hamming"], qv["analytic_p0"],
                 qv["estimated_p0"], qv["decision_equal"] == p["equal"]))
    by_class = {}
    for cls in (0, 1, 3, 10):
        rows = [r for r in pair_rows if r["mutations"] == cls]
        by_class[str(cls)] = {
            "n": len(rows),
            "mean_estimated_p0": sum(r["estimated_p0"] for r in rows) / len(rows),
            "quantum_accuracy": sum(r["quantum_correct"] for r in rows) / len(rows),
            "classical_accuracy": sum(
                r["classical_rope_equal"] == r["ground_truth_equal"]
                for r in rows) / len(rows),
        }
    results["stage3_4_verify"] = {
        "pairs": pair_rows,
        "by_class": by_class,
        "quantum_accuracy_overall": sum(r["quantum_correct"] for r in pair_rows) / len(pair_rows),
        "max_abs_p0_error_vs_analytic": max(
            abs(r["estimated_p0"] - r["analytic_p0"]) for r in pair_rows),
    }
    print("Stage 3+4 verify: quantum accuracy overall =",
          results["stage3_4_verify"]["quantum_accuracy_overall"],
          " max |est - analytic| =",
          round(results["stage3_4_verify"]["max_abs_p0_error_vs_analytic"], 4))

    # ---- Stage 5: end-to-end (with depolarizing noise p=0.02 on quantum verify) ----
    s5 = pipeline.run_end_to_end()
    results["stage5_end_to_end"] = s5
    print("Stage 5 end-to-end: classical confusion =", s5["classical_verify_confusion"],
          " quantum confusion =", s5["quantum_verify_confusion"])

    # ---- Stage 6: noise sweep ----
    sweep = {}
    ident_pairs = [p for p in pairs if p["mutations"] == 0][:2]
    for p_level in (0.01, 0.05):
        nm = qnoise.depolarizing(p_level)
        sd = quantum_pack.run_trials(n_trials=8, shots=1024,
                                     seed=777, noise_model=nm)
        nsim = quantum_verify.default_sim(nm)
        p0s = [quantum_verify.estimate_p0(quantum_verify.codeword(pr["reference"]),
                                          quantum_verify.codeword(pr["candidate"]),
                                          shots=SHOTS_SWAP, sim=nsim)
               for pr in ident_pairs]
        sweep[str(p_level)] = {
            "superdense_message_accuracy": sd["message_accuracy"],
            "superdense_bit_accuracy": sd["bit_accuracy"],
            "swap_identical_p0": p0s,
        }
        print("Stage 6 noise p =", p_level, sweep[str(p_level)])
    results["stage6_noise_sweep"] = sweep

    results["runtime_seconds"] = round(time.time() - t_start, 1)
    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print("Wrote results.json in %.1fs" % results["runtime_seconds"])


if __name__ == "__main__":
    main()
