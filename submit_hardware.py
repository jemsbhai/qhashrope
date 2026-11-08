"""Submit the qhashrope two-server per-bit experiment to IBM Quantum hardware.

Submits the 24 independent 3-qubit per-bit SWAP tests (same construction
as two_server_experiment.py) for three pairs to a real backend via
SamplerV2, 4096 shots per circuit:

  A: identical DNA pair from the prototype suite (seeded segments)
  B: benzene c1ccccc1 vs cyclohexane C1CCCCC1 (distinct, Hamming 12)
  C: aspirin vs its amide analog, one-character O -> N (distinct, Hamming 12)

Writes hardware_jobs.json (backend, job IDs, pairs, shots, timestamp)
immediately after submission so the record exists even if the queue is
slow. Analysis lives in retrieve_hardware_results.py.
"""

import json
import sys
from datetime import datetime, timezone

sys.path.insert(0, "/home/hatch/workspace/qhashrope-proto")

from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

from qhashrope import quantum_verify as qv
from qhashrope import sequences

BACKEND_NAME = "ibm_marrakesh"
SHOTS = 4096


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
    _, pair_set = sequences.make_pair_set()
    dna = next(p for p in pair_set if p["mutations"] == 0)
    return [
        {
            "id": "A_dna_identical",
            "label": "DNA identical (prototype suite, seeded segment vs itself)",
            "reference": dna["reference"],
            "candidate": dna["candidate"],
        },
        {
            "id": "B_benzene_vs_cyclohexane",
            "label": "benzene c1ccccc1 vs cyclohexane C1CCCCC1",
            "reference": "c1ccccc1",
            "candidate": "C1CCCCC1",
        },
        {
            "id": "C_aspirin_vs_amide_analog",
            "label": "aspirin vs amide analog (one-character O to N)",
            "reference": "CC(=O)Oc1ccccc1C(=O)O",
            "candidate": "CC(=O)Oc1ccccc1C(=O)N",
        },
    ]


def main():
    service = QiskitRuntimeService()
    backend = service.backend(BACKEND_NAME)
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    sampler = Sampler(mode=backend)

    record = {
        "backend": BACKEND_NAME,
        "shots_per_circuit": SHOTS,
        "submitted_at_utc": datetime.now(timezone.utc).isoformat(),
        "jobs": [],
    }

    for pair in build_pairs():
        cw_a, cw_b = qv.codeword(pair["reference"]), qv.codeword(pair["candidate"])
        circuits = [per_bit_swap_circuit(cw_a[j], cw_b[j]) for j in range(len(cw_a))]
        isa = pm.run(circuits)
        job = sampler.run(isa, shots=SHOTS)
        entry = {
            "pair_id": pair["id"],
            "label": pair["label"],
            "kind": "per_bit_swap_tests",
            "job_id": job.job_id(),
            "n_circuits": len(circuits),
            "reference": pair["reference"],
            "candidate": pair["candidate"],
            "ground_truth_equal": pair["reference"] == pair["candidate"],
            "codeword_ref": cw_a,
            "codeword_cand": cw_b,
            "codeword_hamming": qv.codeword_hamming(cw_a, cw_b),
        }
        record["jobs"].append(entry)
        print(f"{pair['id']}: job {entry['job_id']} "
              f"({len(circuits)} circuits, codeword hamming {entry['codeword_hamming']})",
              flush=True)

    with open("/home/hatch/workspace/qhashrope-proto/hardware_jobs.json", "w") as fh:
        json.dump(record, fh, indent=2)
    print("wrote hardware_jobs.json")


if __name__ == "__main__":
    main()
