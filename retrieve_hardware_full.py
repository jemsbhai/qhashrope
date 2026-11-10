"""Harvest the ibm_fez two-server per-bit jobs (hardware_full_jobs.json).

Polls until every job reaches a terminal state, then applies the same
analysis as the simulation experiment: per-bit P(0), a bit is decided
differ when P(0) < 0.75, and the Golay radius-3 rule decides equal when
at most 3 bits differ. Bit errors count positions where the decided
state disagrees with the true codeword-bit equality.

Writes hardware_full_results.json and prints a summary table.
"""

import json
import time
from pathlib import Path

from qiskit_ibm_runtime import QiskitRuntimeService

HERE = Path(__file__).resolve().parent
THRESH = 0.75
TERMINAL = {"DONE", "ERROR", "CANCELLED"}


def counts_of(pub_result):
    for attr in vars(pub_result.data).values():
        if hasattr(attr, "get_counts"):
            return attr.get_counts()
    raise RuntimeError("no counts in pub result")


def main():
    record = json.loads((HERE / "hardware_full_jobs.json").read_text())
    service = QiskitRuntimeService()
    jobs = {e["pair_id"]: service.job(e["job_id"]) for e in record["jobs"]}

    deadline = time.time() + 3 * 3600
    while time.time() < deadline:
        states = {pid: str(j.status()) for pid, j in jobs.items()}
        pending = [p for p, s in states.items() if s not in TERMINAL]
        print(f"[{time.strftime('%H:%M:%S')}] pending: {len(pending)}", flush=True)
        if not pending:
            break
        time.sleep(60)

    results = {"backend": record["backend"], "threshold": THRESH,
               "shots_per_circuit": record["shots_per_circuit"], "pairs": []}
    n_correct = 0
    total_bit_errors = 0
    total_bits = 0
    for e in record["jobs"]:
        job = jobs[e["pair_id"]]
        status = str(job.status())
        entry = {"pair_id": e["pair_id"], "label": e["label"], "job_id": e["job_id"],
                 "status": status, "ground_truth_equal": e["ground_truth_equal"],
                 "codeword_hamming": e["codeword_hamming"]}
        if status == "DONE":
            res = job.result()
            p0s = []
            for i in range(len(e["codeword_ref"])):
                counts = counts_of(res[i])
                p0s.append(counts.get("0", 0) / record["shots_per_circuit"])
            bits_differ = [a != b for a, b in zip(e["codeword_ref"], e["codeword_cand"])]
            decided = [p < THRESH for p in p0s]
            bit_errors = sum(1 for d, t in zip(decided, bits_differ) if d != t)
            n_differ = sum(decided)
            entry.update({
                "per_bit_p0": [round(p, 4) for p in p0s],
                "n_bits_decided_differ": n_differ,
                "bit_errors": bit_errors,
                "R3_golay_equal": n_differ <= 3,
                "decision_correct": (n_differ <= 3) == e["ground_truth_equal"],
            })
            n_correct += entry["decision_correct"]
            total_bit_errors += bit_errors
            total_bits += len(p0s)
        results["pairs"].append(entry)

    results["summary"] = {
        "pairs_done": sum(1 for p in results["pairs"] if p["status"] == "DONE"),
        "decisions_correct": n_correct,
        "total_bit_errors": total_bit_errors,
        "total_bit_decisions": total_bits,
    }
    with open(HERE / "hardware_full_results.json", "w") as fh:
        json.dump(results, fh, indent=2)
    print(json.dumps(results["summary"], indent=2))
    for p in results["pairs"]:
        print(f"{p['pair_id']:22s} {p['status']:6s} true_eq={p['ground_truth_equal']} "
              f"ndiff={p.get('n_bits_decided_differ')} biterr={p.get('bit_errors')} "
              f"correct={p.get('decision_correct')}", flush=True)


if __name__ == "__main__":
    main()
