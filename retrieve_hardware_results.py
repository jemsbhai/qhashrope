"""Retrieve and analyse the qhashrope IBM Quantum hardware run.

Reads hardware_jobs.json (written by submit_hardware.py), polls the jobs
until they finish (or the wait budget expires), then applies exactly the
decision rule of two_server_experiment.py to the hardware counts:

  bit j decided DIFFER iff its SWAP-test P(0) < 0.75 (midpoint of the
  analytic values 1.0 for agreeing bits and 0.5 for differing bits);
  R3 Golay recombination: pair decided EQUAL iff #differ <= 3
  (unique-decoding radius of the (24,12,8) Golay code). R1 (product)
  and R2 (AND) are also reported, as in the simulation.

Writes hardware_results.json and HARDWARE_RESULTS.md and appends a
'Hardware run, 2026-11-08' section to RESULTS.md. Nothing is estimated
or filled in: pairs whose jobs have not finished are reported as
pending and no results files are written for them.

Usage: python retrieve_hardware_results.py [--wait-seconds 3000]
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, "/home/hatch/workspace/qhashrope-proto")

ROOT = "/home/hatch/workspace/qhashrope-proto"
THRESH = 0.75
DONE = {"DONE"}
FAILED = {"ERROR", "CANCELLED"}


def recombine(p0s):
    """Identical to two_server_experiment.recombine."""
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


def counts_of(pub_result):
    data = pub_result.data
    for name in ("c", "meas"):
        if hasattr(data, name):
            return getattr(data, name).get_counts()
    # fallback: first attribute with get_counts
    for name in dir(data):
        obj = getattr(data, name)
        if hasattr(obj, "get_counts"):
            return obj.get_counts()
    raise RuntimeError("no counts found in pub result")


def job_status(service, job_id):
    return str(service.job(job_id).status())


def wait_for_jobs(service, job_ids, budget_s, poll_s=120):
    deadline = time.time() + budget_s
    status = {}
    while True:
        for jid in job_ids:
            if status.get(jid) not in DONE | FAILED:
                status[jid] = job_status(service, jid)
        print(f"[{datetime.now(timezone.utc).isoformat()}] "
              + ", ".join(f"{j[-6:]}={s}" for j, s in status.items()), flush=True)
        if all(s in DONE | FAILED for s in status.values()):
            return status
        if time.time() >= deadline:
            return status
        time.sleep(poll_s)


def sim_reference():
    sim = json.load(open(f"{ROOT}/two_server_results.json"))
    by_name = {}
    for r in sim["pairs"]:
        by_name.setdefault(r["pair"], r)
    return {
        "A_dna_identical": by_name.get("DNA identical"),
        "B_benzene_vs_cyclohexane": by_name.get("benzene vs cyclohexane"),
        "C_aspirin_vs_amide_analog": by_name.get("aspirin vs amide analog"),
    }


def analyse_pair(service, entry):
    job = service.job(entry["job_id"])
    result = job.result()
    p0s = []
    for i in range(entry["n_circuits"]):
        counts = counts_of(result[i])
        total = sum(counts.values())
        p0s.append(counts.get("0", 0) / total)
    rec = recombine(p0s)
    cw_a, cw_b = entry["codeword_ref"], entry["codeword_cand"]
    bit_errors = sum(
        1 for j, p in enumerate(p0s)
        if (p < THRESH) != (cw_a[j] != cw_b[j])
    )
    rec.update({
        "pair_id": entry["pair_id"],
        "label": entry["label"],
        "job_id": entry["job_id"],
        "ground_truth_equal": entry["ground_truth_equal"],
        "codeword_hamming": entry["codeword_hamming"],
        "bit_decision_errors": bit_errors,
        "decision_equal_R3": rec["R3_golay_equal"],
        "correct_R3": rec["R3_golay_equal"] == entry["ground_truth_equal"],
    })
    return rec


def analyse_monolithic(service, entry):
    job = service.job(entry["job_id"])
    result = job.result()
    counts = counts_of(result[0])
    total = sum(counts.values())
    p0 = counts.get("0", 0) / total
    return {
        "pair_id": entry["pair_id"],
        "label": entry["label"],
        "job_id": entry["job_id"],
        "kind": "monolithic_swap_test_exploratory",
        "p0": round(p0, 4),
        "decision_equal": p0 >= THRESH,
        "ground_truth_equal": entry["ground_truth_equal"],
        "correct": (p0 >= THRESH) == entry["ground_truth_equal"],
    }


def fmt_range(vals):
    return f"{min(vals):.4f}-{max(vals):.4f}"


def write_reports(record, analysed, mono, status_map):
    sims = sim_reference()
    out = {
        "backend": record["backend"],
        "shots_per_circuit": record["shots_per_circuit"],
        "submitted_at_utc": record["submitted_at_utc"],
        "harvested_at_utc": datetime.now(timezone.utc).isoformat(),
        "threshold": THRESH,
        "pairs": analysed,
        "monolithic_exploratory": mono,
    }
    with open(f"{ROOT}/hardware_results.json", "w") as fh:
        json.dump(out, fh, indent=2)

    lines = []
    lines.append("# Hardware run, 2026-11-08 (IBM Quantum, ibm_marrakesh)")
    lines.append("")
    lines.append(f"Backend: **{record['backend']}** (156 qubits). SamplerV2, "
                 f"{record['shots_per_circuit']} shots per circuit. Submitted "
                 f"{record['submitted_at_utc']}; job record in `hardware_jobs.json`. "
                 "Decision rule identical to the simulation: per-bit P(0) decided "
                 "differ below 0.75; Golay radius-3 recombination (equal iff "
                 "decided-differ <= 3). Analysis by `retrieve_hardware_results.py`.")
    lines.append("")
    lines.append("## Per-bit two-server verification on hardware")
    lines.append("")
    lines.append("| Pair | Job | Truth | True Hamming | Decided differ | Bit errors | R3 decision | Correct |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in analysed:
        lines.append(
            f"| {r['pair_id']} | {r['job_id']} | "
            f"{'equal' if r['ground_truth_equal'] else 'differ'} | "
            f"{r['codeword_hamming']} | {r['n_bits_decided_differ']} | "
            f"{r['bit_decision_errors']} | "
            f"{'equal' if r['decision_equal_R3'] else 'differ'} | "
            f"{'yes' if r['correct_R3'] else 'NO'} |")
    lines.append("")
    lines.append("Per-bit P(0) detail (hardware | simulated depolarizing p=0.02 from "
                 "`two_server_results.json`; noiseless analytic values are 1.0 for "
                 "agreeing bits and 0.5 for differing bits):")
    lines.append("")
    for r in analysed:
        sim = sims.get(r["pair_id"])
        agree_hw = [p for j, p in enumerate(r["per_bit_p0"])
                    ]
        lines.append(f"- **{r['pair_id']}** ({r['label']}): hardware per-bit P(0) "
                     f"range {fmt_range(agree_hw)}; decided differ "
                     f"{r['n_bits_decided_differ']} of 24 "
                     f"(true Hamming {r['codeword_hamming']}); "
                     f"bit decision errors {r['bit_decision_errors']}.")
        if sim:
            lines.append(
                f"  Simulation p=0.02 for the same pair: per-bit P(0) range "
                f"{fmt_range(sim['per_bit_p0'])}, decided differ "
                f"{sim['n_bits_decided_differ']}, bit decision errors 0.")
        lines.append(f"  Hardware per-bit P(0): {r['per_bit_p0']}")
    lines.append("")
    lines.append("## Exploratory monolithic 49-qubit SWAP test (pair A)")
    lines.append("")
    if mono is None:
        st = ", ".join(f"{e['job_id']}={status_map.get(e['job_id'])}"
                       for e in record["jobs"]
                       if e["kind"].startswith("monolithic"))
        lines.append(f"Not harvested in this run ({st}). No result is claimed.")
    else:
        lines.append(
            f"Job {mono['job_id']}: measured P(0) = {mono['p0']:.4f} "
            f"(threshold 0.75), decision "
            f"{'equal' if mono['decision_equal'] else 'differ'}, ground truth equal, "
            f"{'correct' if mono['correct'] else 'INCORRECT'}. For reference, the "
            "same quantity in simulation was 1.0 noiseless (analytic) and "
            "0.7244-0.7402 under depolarizing p=0.02.")
    lines.append("")
    lines.append("## What the hardware did and did not show")
    lines.append("")
    n_pairs = len(analysed)
    n_correct = sum(1 for r in analysed if r["correct_R3"])
    total_bit_errors = sum(r["bit_decision_errors"] for r in analysed)
    lines.append(
        f"The per-bit two-server protocol was executed end-to-end on a real "
        f"device: {n_correct} of {n_pairs} pair decisions were correct under "
        f"the same Golay radius-3 rule that classified 13/13 in the p=0.02 "
        f"simulation. Across all harvested pairs there were {total_bit_errors} "
        "individual bit decision errors (a bit whose hardware P(0) fell on the "
        "wrong side of 0.75 relative to the true codeword bits). Unlike the "
        "Aer depolarizing model used in simulation, the real device also has "
        "readout error, T1/T2 decoherence and crosstalk; the numbers above "
        "include all of those effects and are reported as measured, bit "
        "errors included. The hardware run does not by itself establish a "
        "scaling claim: circuits were 3-qubit tests transpiled by the "
        "standard preset pass manager, one device, one calibration cycle.")
    lines.append("")
    with open(f"{ROOT}/HARDWARE_RESULTS.md", "w") as fh:
        fh.write("\n".join(lines))

    with open(f"{ROOT}/RESULTS.md", "a") as fh:
        fh.write("\n## Hardware run, 2026-11-08\n\n"
                 f"The two-server per-bit protocol was run on IBM Quantum "
                 f"hardware (**{record['backend']}**): {n_correct} of {n_pairs} "
                 "pair decisions correct under the Golay radius-3 rule, "
                 f"{total_bit_errors} bit decision errors in total. Full "
                 "per-bit values, job IDs and the exploratory monolithic "
                 "49-qubit job are in `HARDWARE_RESULTS.md` "
                 "(`hardware_results.json`, `hardware_jobs.json`).\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wait-seconds", type=int, default=3000)
    args = ap.parse_args()

    from qiskit_ibm_runtime import QiskitRuntimeService
    service = QiskitRuntimeService()
    record = json.load(open(f"{ROOT}/hardware_jobs.json"))
    per_bit = [e for e in record["jobs"] if e["kind"] == "per_bit_swap_tests"]
    mono_entries = [e for e in record["jobs"]
                    if e["kind"].startswith("monolithic")]
    all_ids = [e["job_id"] for e in record["jobs"]]

    status = wait_for_jobs(service, all_ids, args.wait_seconds)

    pending = [e["pair_id"] for e in per_bit
               if status.get(e["job_id"]) not in DONE]
    if pending:
        print("PENDING per-bit jobs:", pending,
              {e["job_id"]: status.get(e["job_id"]) for e in per_bit})
        print("No results files written. Re-run this script to harvest later.")
        return 2

    analysed = [analyse_pair(service, e) for e in per_bit]
    mono = None
    if mono_entries and status.get(mono_entries[0]["job_id"]) in DONE:
        mono = analyse_monolithic(service, mono_entries[0])
    elif mono_entries:
        print("monolithic exploratory job status:",
              status.get(mono_entries[0]["job_id"]))

    write_reports(record, analysed, mono, status)
    print("wrote hardware_results.json, HARDWARE_RESULTS.md, appended RESULTS.md")
    for r in analysed:
        print(f"{r['pair_id']}: decided_differ={r['n_bits_decided_differ']} "
              f"(true {r['codeword_hamming']}), bit_errors={r['bit_decision_errors']}, "
              f"R3={'equal' if r['decision_equal_R3'] else 'differ'}, "
              f"correct={r['correct_R3']}")
    if mono:
        print(f"monolithic exploratory: p0={mono['p0']}, correct={mono['correct']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
