"""Submit the qhashrope Bell-basis (destructive SWAP test) experiment to
IBM Quantum hardware.

One 48-qubit Bell-measurement circuit per pair for the same 13
comparisons as two_server_experiment.py / bell_experiment.py, submitted
to ibm_marrakesh via SamplerV2, 4096 shots per circuit (matching the
per-bit hardware run of submit_hardware.py). Simulation validation in
bell_experiment.py must PASS before this script is run; the test set is
re-cross-checked here against two_server_results.json regardless.

Writes bell_hardware_jobs.json (backend, job IDs, pairs, transpiled
resource counts, shots, timestamp) immediately after submission.
Analysis lives in retrieve_bell_hardware.py.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

from qhashrope import quantum_verify as qv
from bell_experiment import build_pairs, cross_check_test_set, bell_circuit

BACKEND_NAME = "ibm_marrakesh"
SHOTS = 4096
ROOT = Path(__file__).resolve().parent

PAIR_IDS = [
    "pair_01_control_identical",
    "pair_02_dna_identical",
    "pair_03_dna_identical",
    "pair_04_dna_identical",
    "pair_05_dna_1_substitution",
    "pair_06_dna_1_substitution",
    "pair_07_dna_1_substitution",
    "pair_08_dna_10_substitutions",
    "pair_09_dna_10_substitutions",
    "pair_10_dna_10_substitutions",
    "pair_11_aspirin_vs_amide_analog",
    "pair_12_benzene_vs_cyclohexane",
    "pair_13_aspirin_identical",
]


def main():
    pairs = build_pairs()
    cross_check_test_set(pairs)
    assert len(pairs) == len(PAIR_IDS) == 13

    service = QiskitRuntimeService()
    backend = service.backend(BACKEND_NAME)
    print("backend status:", backend.status(), flush=True)
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    sampler = Sampler(mode=backend)

    record = {
        "backend": BACKEND_NAME,
        "shots_per_circuit": SHOTS,
        "submitted_at_utc": datetime.now(timezone.utc).isoformat(),
        "kind": "bell_basis_destructive_swap",
        "jobs": [],
    }

    for pair_id, pair in zip(PAIR_IDS, pairs):
        cw_a, cw_b = qv.codeword(pair["reference"]), qv.codeword(pair["candidate"])
        qc = bell_circuit(cw_a, cw_b)
        isa = pm.run(qc)
        ops = {k: int(v) for k, v in isa.count_ops().items()}
        job = sampler.run([isa], shots=SHOTS)
        entry = {
            "pair_id": pair_id,
            "label": pair["name"],
            "kind": "bell_basis_destructive_swap",
            "job_id": job.job_id(),
            "n_circuits": 1,
            "reference": pair["reference"],
            "candidate": pair["candidate"],
            "ground_truth_equal": pair["reference"] == pair["candidate"],
            "codeword_ref": cw_a,
            "codeword_cand": cw_b,
            "codeword_hamming": qv.codeword_hamming(cw_a, cw_b),
            "transpiled_ops": ops,
            "transpiled_depth": isa.depth(),
            "transpiled_cz": ops.get("cz", 0),
        }
        record["jobs"].append(entry)
        print(f"{pair_id} ({pair['name']}): job {entry['job_id']} "
              f"transpiled cz={entry['transpiled_cz']} depth={entry['transpiled_depth']} "
              f"hamming={entry['codeword_hamming']}", flush=True)

    with open(ROOT / "bell_hardware_jobs.json", "w") as fh:
        json.dump(record, fh, indent=2)
    print("wrote bell_hardware_jobs.json")


if __name__ == "__main__":
    main()
