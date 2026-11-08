"""Quantum pack stage: superdense coding.

Each entangled pair carries one 2-bit message (phase bit, flip bit) on a
single transmitted qubit, given a pre-shared Bell pair. A payload here is
N_PAIRS messages = 8 classical bits sent on 4 transmitted qubits.

Bit-order note (verified empirically, see logs): a Qiskit counts key reads
classical bits high-to-low; for pair i, Alice's qubit result is the phase bit
and Bob's qubit result is the flip bit.
"""

import random

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

N_PAIRS = 4
ALL_MESSAGES = [(0, 0), (0, 1), (1, 0), (1, 1)]  # (phase, flip)


def superdense_circuit(messages):
    """messages: list of (phase, flip) bit tuples, one per entangled pair."""
    n = len(messages)
    qc = QuantumCircuit(2 * n, 2 * n)
    for i, (phase, flip) in enumerate(messages):
        a, b = 2 * i, 2 * i + 1  # Alice, Bob
        qc.h(a)
        qc.cx(a, b)  # shared Bell pair
        if flip:
            qc.x(a)
        if phase:
            qc.z(a)
        qc.cx(a, b)  # Bell-basis decode
        qc.h(a)
    qc.measure(range(2 * n), range(2 * n))
    return qc


def decode_key(key, n_pairs):
    """Decode a counts key back to a list of (phase, flip) messages."""
    length = len(key)
    out = []
    for i in range(n_pairs):
        alice = int(key[length - 1 - 2 * i])  # clbit 2i   -> phase bit
        bob = int(key[length - 1 - (2 * i + 1)])  # clbit 2i+1 -> flip bit
        out.append((alice, bob))
    return out


def run_payload(messages, shots=1024, sim=None, noise_model=None):
    if sim is None:
        sim = AerSimulator(noise_model=noise_model) if noise_model else AerSimulator()
    qc = superdense_circuit(messages)
    counts = sim.run(transpile(qc, sim), shots=shots).result().get_counts()
    top_key = max(counts, key=counts.get)
    decoded = decode_key(top_key, len(messages))
    bit_errors = sum(
        (p1 != p2) + (f1 != f2)
        for (p1, f1), (p2, f2) in zip(messages, decoded)
    )
    return {
        "sent": list(messages),
        "decoded": decoded,
        "message_ok": decoded == list(messages),
        "bit_errors": bit_errors,
        "top_key_fraction": counts[top_key] / shots,
    }


def run_trials(n_trials=20, shots=1024, seed=20261107, noise_model=None):
    rng = random.Random(seed)
    sim = AerSimulator(noise_model=noise_model) if noise_model else AerSimulator()
    trials = []
    for _ in range(n_trials):
        msgs = [rng.choice(ALL_MESSAGES) for _ in range(N_PAIRS)]
        trials.append(run_payload(msgs, shots=shots, sim=sim))
    total_bits = n_trials * N_PAIRS * 2
    total_bit_errors = sum(t["bit_errors"] for t in trials)
    return {
        "n_trials": n_trials,
        "shots": shots,
        "payload_bits_per_trial": N_PAIRS * 2,
        "message_accuracy": sum(t["message_ok"] for t in trials) / n_trials,
        "bit_accuracy": 1 - total_bit_errors / total_bits,
        "trials": trials,
    }
