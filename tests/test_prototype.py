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
    """Distinct strings: Golay-encoded fingerprints are exactly orthogonal,
    so P(0) must be ~0.5. (Updated 2026-11-08: the original version of this
    test fed raw legacy symbol lists into the encoder and asserted on the
    legacy graded overlap; it now asserts the classification behaviour of
    the fixed encoding instead.)"""
    cw_a = quantum_verify.codeword("ACGT" * 24)
    cw_b = quantum_verify.codeword("TTTTGGGGCCCCAAAA" * 6)
    assert cw_a != cw_b
    assert quantum_verify.codeword_hamming(cw_a, cw_b) >= 8
    analytic = quantum_verify.analytic_overlap2(cw_a, cw_b)
    assert analytic == 0.0, f"analytic overlap should be exactly 0, got {analytic}"
    p0 = quantum_verify.estimate_p0(cw_a, cw_b, shots=4096)
    assert abs(p0 - 0.5) <= 0.03, f"maximally-different P(0) = {p0}"
    print(f"PASS swap orthogonal: P(0) = {p0:.4f} (theory 0.5)")


def test_golay_min_distance():
    """The extended Golay code (24,12,8) is linear, so its minimum distance
    equals the minimum weight of a nonzero codeword: enumerate all 4096."""
    min_weight = min(
        sum(quantum_verify.golay_encode(m)) for m in range(1, 4096)
    )
    assert min_weight >= quantum_verify.GOLAY_MIN_DISTANCE, min_weight
    print(f"PASS golay: min nonzero weight = {min_weight} (distance >= 8)")


def test_position_seeding():
    """Same block content at different positions must not systematically get
    the same symbol (the original benzene/cyclohexane collision mode)."""
    symbols = quantum_verify.hash_symbols("ACGT" * 24)
    assert len(set(symbols)) > 1, f"position seeding failed: {symbols}"
    print(f"PASS position seeding: {len(set(symbols))} distinct symbols "
          f"for a periodic segment")


def test_chemistry_pairs_separate():
    """The five SMILES pairs from the 2026-11-08 chemistry demo, at the
    analytic level: identical -> overlap 1; distinct -> encoded Hamming
    distance >= 8 and analytic P(0) exactly 0.5."""
    pairs = [
        ("CC(=O)Oc1ccccc1C(=O)O", "CC(=O)Oc1ccccc1C(=O)O", True),
        ("CC(=O)Oc1ccccc1C(=O)O", "CC(=O)Oc1ccccc1C(=O)N", False),
        ("c1ccccc1", "Cc1ccccc1", False),
        ("c1ccccc1", "c1ccncc1", False),
        ("c1ccccc1", "C1CCCCC1", False),
    ]
    for a, b, equal in pairs:
        ca, cb = quantum_verify.codeword(a), quantum_verify.codeword(b)
        ov = quantum_verify.analytic_overlap2(ca, cb)
        if equal:
            assert ov == 1.0 and ca == cb
        else:
            assert ov == 0.0 and quantum_verify.codeword_hamming(ca, cb) >= 8
    print("PASS chemistry pairs: all 5 separate analytically (0 / >=8 / 0.5)")


if __name__ == "__main__":
    test_superdense_all_messages()
    test_multispecqr_roundtrip()
    test_hashrope_ground_truth()
    test_swap_identical_within_tolerance()
    test_swap_maximally_different_near_half()
    test_golay_min_distance()
    test_position_seeding()
    test_chemistry_pairs_separate()
    print("ALL TESTS PASSED")
