"""End-to-end flow: pack payloads, corrupt a segment in transit, verify.

The verify stage runs both the classical hashrope check and the quantum
fingerprint SWAP test (the latter optionally under an Aer depolarizing noise
model, standing in for device/channel noise on the quantum side).
"""

from . import classical_pack, classical_verify, quantum_pack, quantum_verify
from . import qnoise, sequences

PAYLOADS = ["QHASHROPE-DEMO", "PACK:MSQR+SDC", "VERIFY:SWAP-TEST"]


def run_end_to_end(mutation_trials=(0, 0, 0, 1, 1, 3, 3, 10, 10),
                   shots=4096, noise_p=0.02, seed=20261107):
    import random

    rng = random.Random(seed + 1)

    # Pack stage (both carriers)
    pack_c = classical_pack.roundtrip(PAYLOADS)
    pack_q = quantum_pack.run_trials(n_trials=5, shots=1024, seed=seed)

    # A reference segment "in transit"; each trial corrupts it by k mutations.
    base = sequences.make_segment(rng)
    noise_model = qnoise.depolarizing(noise_p) if noise_p else None
    sim = quantum_verify.default_sim(noise_model)

    # Noise-aware threshold calibration (the analogue of MultiSpecQR's color
    # calibration card): measure a known-identical pair under the SAME noise
    # model and put the threshold midway between that value and 0.5, the
    # fully-different limit. A fixed noiseless threshold fails under noise:
    # depolarizing error pulls identical-pair P(0) from 1.0 toward 0.5
    # (~0.89 at p=0.01, ~0.64 at p=0.05; see the stage-6 sweep).
    cw_base = quantum_verify.codeword(base)
    cal_p0 = quantum_verify.estimate_p0(cw_base, cw_base, shots=shots, sim=sim)
    threshold = (cal_p0 + 0.5) / 2

    trials = []
    for k in mutation_trials:
        cand = sequences.mutate(base, k, rng) if k else base
        cv = classical_verify.verify_pair(base, cand)
        qv = quantum_verify.verify_pair(base, cand, shots=shots, sim=sim,
                                        threshold=threshold)
        trials.append(
            {
                "mutations": k,
                "ground_truth_equal": k == 0,
                "classical_decision_equal": cv["rope_equal"],
                "quantum_decision_equal": qv["decision_equal"],
                "quantum_p0": qv["estimated_p0"],
                "quantum_analytic_p0": qv["analytic_p0"],
                "codeword_hamming": qv["codeword_hamming"],
            }
        )

    def confusion(key):
        tp = sum(1 for t in trials if t["ground_truth_equal"] and t[key])
        tn = sum(1 for t in trials if not t["ground_truth_equal"] and not t[key])
        fp = sum(1 for t in trials if not t["ground_truth_equal"] and t[key])
        fn = sum(1 for t in trials if t["ground_truth_equal"] and not t[key])
        return {"TP": tp, "TN": tn, "FP": fp, "FN": fn,
                "accuracy": (tp + tn) / len(trials)}

    return {
        "classical_pack_all_ok": pack_c["all_ok"],
        "quantum_pack_message_accuracy": pack_q["message_accuracy"],
        "noise_p": noise_p,
        "calibration_identical_p0": cal_p0,
        "calibrated_threshold": threshold,
        "trials": trials,
        "classical_verify_confusion": confusion("classical_decision_equal"),
        "quantum_verify_confusion": confusion("quantum_decision_equal"),
    }
