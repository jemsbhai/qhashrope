"""Superdense packing demo (the pack stage itself).

Constraint: bandwidth during a short contact window is the scarce
resource. With Bell pairs shared in advance, each transmitted qubit
carries 2 classical bits, so an 8-bit payload crosses on 4 transmitted
qubits. This case is the packing primitive, not a verification pair
set, so the demo is a pack/unpack round trip: each payload is encoded
with qhashrope.quantum_pack, sent, Bell-decoded, and compared bit for
bit with what was sent.

Run:  python demo.py   (from this folder, with the project venv)
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from qhashrope import quantum_pack  # noqa: E402

SHOTS = 1024

# Each payload is 4 (phase, flip) messages: 8 classical bits on 4 qubits.
PAYLOADS = [
    [(0, 0), (0, 0), (0, 0), (0, 0)],
    [(1, 1), (1, 1), (1, 1), (1, 1)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(1, 0), (1, 0), (0, 1), (0, 1)],
    [(0, 1), (1, 1), (1, 0), (0, 0)],
    [(1, 1), (0, 0), (1, 0), (0, 1)],
]


def bits(messages):
    return "".join(f"{phase}{flip}" for phase, flip in messages)


def main():
    print(f"{'payload sent':<12s} {'decoded':<12s} {'bit errors':>10s} "
          f"verdict")
    n_pass = 0
    total_bits = total_errors = 0
    for payload in PAYLOADS:
        r = quantum_pack.run_payload(payload, shots=SHOTS)
        ok = r["message_ok"]
        n_pass += ok
        total_bits += 2 * len(payload)
        total_errors += r["bit_errors"]
        print(f"{bits(r['sent']):<12s} {bits(r['decoded']):<12s} "
              f"{r['bit_errors']:>10d} {'PASS' if ok else 'FAIL'}")
    print(f"SUMMARY: {n_pass}/{len(PAYLOADS)} payloads round-tripped "
          f"exactly ({total_bits - total_errors}/{total_bits} bits)")


if __name__ == "__main__":
    main()
