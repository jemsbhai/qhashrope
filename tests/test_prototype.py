#!/usr/bin/env python3
"""Assertions for the deterministic / near-deterministic parts of qhashrope.

Run:  ~/workspace/.qiskit-venv/bin/python tests/test_prototype.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from qiskit import transpile
from qiskit_aer import AerSimulator

from qhashrope import (classical_pack, classical_verify, quantum_pack,
                       quantum_verify)


def test_superdense_all_messages():
    """Superdense coding must decode all four 2-bit messages exactly."""
    sim = AerSimulator()
    for msg in quantum_pack.ALL_MESSAGES:
        qc = quantum_pack.superdense_circuit([msg])
        counts = sim.run(transpile(qc, sim), shots=256).result().get_counts()
        top = max(counts, key=counts.get)
        decoded = quantum_pack.decode_key(top, 1)
        assert decoded == [msg], f"superdense {msg} decoded as {decoded}"
        assert counts[top] == 256, f"superdense {msg} not deterministic: {counts}"
    print("PASS superdense: all 4 messages, 256/256 shots each")


def test_multispecqr_roundtrip():
    payloads = ["TEST-R", "TEST-G", "TEST-B"]
    res = classical_pack.roundtrip(payloads)
    assert res["all_ok"], f"MultiSpecQR round-trip failed: {res['decoded']}"
    print("PASS multispecqr: 3 payloads round-trip lossless")


def test_hashrope_ground_truth():
    a = "ACGTACGTACGTACGT"
    b = "ACGTACGTACGTACGA"  # one substitution
    assert classical_verify.ropes_equal(a, a)
    assert not classical_verify.ropes_equal(a, b)
    assert classical_verify.fingerprint(a) != classical_verify.fingerprint(b)
    print("PASS hashrope: identical ropes equal, 1-substitution ropes differ")


def test_swap_identical_within_tolerance():
    """SWAP test of a fingerprint against itself: P(0) must be 1 (noiseless)."""
    seg = "ACGT" * 24
    cw = quantum_verify.codeword(seg)
    p0 = quantum_verify.estimate_p0(cw, cw, shots=4096)
    assert abs(p0 - 1.0) <= 0.02, f"identical-pair P(0) = {p0}"
    print(f"PASS swap identical: P(0) = {p0:.4f} (theory 1.0)")


def test_swap_maximally_different_near_half():
    """Codewords differing in every symbol by half the alphabet: P(0) ~ 0.5."""
    sym_a = [0] * quantum_verify.M_BLOCKS
    sym_b = [quantum_verify.K_SYMBOLS // 2] * quantum_verify.M_BLOCKS
    analytic = quantum_verify.analytic_overlap2(sym_a, sym_b)
    assert analytic < 1e-6, f"analytic overlap should be ~0, got {analytic}"
    p0 = quantum_verify.estimate_p0(sym_a, sym_b, shots=4096)
    assert abs(p0 - 0.5) <= 0.03, f"maximally-different P(0) = {p0}"
    print(f"PASS swap orthogonal-ish: P(0) = {p0:.4f} (theory 0.5)")


if __name__ == "__main__":
    test_superdense_all_messages()
    test_multispecqr_roundtrip()
    test_hashrope_ground_truth()
    test_swap_identical_within_tolerance()
    test_swap_maximally_different_near_half()
    print("ALL TESTS PASSED")
