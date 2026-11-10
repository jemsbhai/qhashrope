"""Submit the remaining two-server per-bit pairs to IBM Quantum hardware.

The 13-pair suite of two_server_experiment.py ran 3 pairs on hardware
on 2026-11-08 (ibm_marrakesh: first DNA identical pair, benzene vs
cyclohexane, aspirin vs amide analog; see HARDWARE_RESULTS.md). This
script submits the other 10 pairs, same construction (24 independent
3-qubit per-bit SWAP tests per pair, SamplerV2, 4096 shots), to
ibm_fez, a second Heron r2 device, on 2026-11-10.

Writes hardware_full_jobs.json immediately after submission.
Analysis lives in retrieve_hardware_full.py.
"""

import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

from qhashrope import quantum_verify as qv
from qhashrope import sequences

BACKEND_NAME = "ibm_fez"
SHOTS = 4096
OUT = Path(__file__).with_name("hardware_full_jobs.json")


def per_bit_swap_circuit(bit_a: int, bit_b: int) -> QuantumCircuit:
    qc = QuantumCircuit(3, 1)
    qc.compose(qv.fingerprint_circuit([bit_a]), qubits=[1], inplace=True)
    qc.compose(qv.fingerprint_circuit([bit_b]), qubits=[2], inplace=True)
    qc.h(0)
    qc.cswap(0, 1, 2)
    qc.h(0)
    qc.measure(0, 0)
    return qc


def build_pairs():
    """The 13-pair suite minus the 3 pairs already run on hardware."""
    pairs = []
    ctrl = sequences.make_segment(random.Random(999))
    pairs.append(("control_identical", "CONTROL identical (independent segment)", ctrl, ctrl))
    _, pair_set = sequences.make_pair_set()
    chosen = []
    for mut, k in ((0, 3), (1, 3), (10, 3)):
        chosen += [p for p in pair_set if p["mutations"] == mut][:k]
    counters = {0: 0, 1: 0, 10: 0}
    for p in chosen:
        mut = p["mutations"]
        counters[mut] += 1
        if mut == 0:
            pid = f"dna_identical_{counters[mut]}"
            label = "DNA identical"
        else:
            pid = f"dna_{mut}sub_{counters[mut]}"
            label = f"DNA {mut} substitutions"
        pairs.append((pid, label, p["reference"], p["candidate"]))
    pairs.append(("aspirin_vs_amide", "aspirin vs amide analog",
                  "CC(=O)Oc1ccccc1C(=O)O", "CC(=O)Oc1ccccc1C(=O)N"))
    pairs.append(("benzene_vs_cyclohexane", "benzene vs cyclohexane",
                  "c1ccccc1", "C1CCCCC1"))
    pairs.append(("aspirin_identical", "aspirin vs aspirin (identical)",
                  "CC(=O)Oc1ccccc1C(=O)O", "CC(=O)Oc1ccccc1C(=O)O"))
    done_on_hardware = {"dna_identical_1", "aspirin_vs_amide", "benzene_vs_cyclohexane"}
    return [p for p in pairs if p[0] not in done_on_hardware]


def main():
    service = QiskitRuntimeService()
    backend = service.backend(BACKEND_NAME)
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    sampler = Sampler(mode=backend)

    record = {
        "backend": BACKEND_NAME,
        "shots_per_circuit": SHOTS,
        "submitted_at_utc": datetime.now(timezone.utc).isoformat(),
        "note": "Remaining 10 of the 13-pair two-server suite; 3 pairs ran "
                "2026-11-08 on ibm_marrakesh (HARDWARE_RESULTS.md).",
        "jobs": [],
    }

    for pid, label, ref, cand in build_pairs():
        cw_a, cw_b = qv.codeword(ref), qv.codeword(cand)
        circuits = [per_bit_swap_circuit(cw_a[j], cw_b[j]) for j in range(len(cw_a))]
        isa = pm.run(circuits)
        job = sampler.run(isa, shots=SHOTS)
        record["jobs"].append({
            "pair_id": pid,
            "label": label,
            "kind": "per_bit_swap_tests",
            "job_id": job.job_id(),
            "n_circuits": len(circuits),
            "reference": ref if isinstance(ref, str) else ref.decode(),
            "candidate": cand if isinstance(cand, str) else cand.decode(),
            "ground_truth_equal": ref == cand,
            "codeword_ref": cw_a,
            "codeword_cand": cw_b,
            "codeword_hamming": qv.codeword_hamming(cw_a, cw_b),
        })
        print(f"{pid}: job {job.job_id()} (24 circuits, hamming "
              f"{record['jobs'][-1]['codeword_hamming']})", flush=True)

    with open(OUT, "w") as fh:
        json.dump(record, fh, indent=2)
    print(f"wrote {OUT.name}: {len(record['jobs'])} jobs")


if __name__ == "__main__":
    main()
