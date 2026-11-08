"""Quantum verify stage: product-state fingerprints with an ECC codeword.

Construction (fixed 2026-11-08; the original encoding is kept below behind
``legacy=True`` for reproducibility):

1. Hash codeword. The segment is split into M_BLOCKS blocks. The symbol of
   block j is

       s_j = mix64(hashrope_fingerprint(block_j) seeded by j) mod 4096,

   where mix64 is the splitmix64 finaliser. Hashing the block index together
   with the block content (position seeding) plus a 4096-symbol alphabet
   (was: unseeded, mod 16) removes the systematic collisions of the original
   encoding, in which short strings produced mostly empty or one-character
   blocks whose unseeded residues mod 16 coincided block after block (on
   2026-11-08 benzene and cyclohexane produced byte-identical codewords).

2. Message fold. The 12 symbols are folded to a 12-bit message

       m = ( sum_j (2j + 1) * s_j + 25 * len(segment) ) mod 4096.

   Every weight is odd, so if exactly one symbol changes, m changes with
   certainty (an odd multiple of a nonzero residue mod 4096 is nonzero);
   multi-symbol changes cancel only on a hash-collision-scale event
   (~2^-12). A changed block changes its symbol unless the position-seeded
   61-bit hash collides mod 4096 (~2^-12 per block).

3. Error-correcting expansion (Ablayev-Vasiliev step). The 12-bit message is
   encoded with the extended binary Golay code (24, 12, 8): any two distinct
   messages produce 24-bit codewords differing in at least 8 positions
   (verified by exhaustive enumeration in the tests).

4. Fingerprint state. Encoded bit b_j is prepared as the qubit state |b_j>
   (X gate where b_j = 1): differing bits are ORTHOGONAL states, not
   near-parallel rotations. The overlap therefore factorises to an exact
   bound: for distinct strings,

       |<psi|phi>|^2 = 0   exactly (at least 8 orthogonal factors),

   and for identical strings |<psi|phi>|^2 = 1 exactly. A SWAP test
   estimates P(0) = (1 + |<psi|phi>|^2) / 2, so analytically P(0) is 1.0 for
   equal strings and 0.5 for distinct strings.

Decision threshold. One global threshold for every pair in every demo,
fixed in advance from the bound above: the midpoint of the analytic
decision interval, (1.0 + 0.5) / 2 = 0.75. Shot noise at 4096 shots has
sigma <= 0.0078, so both analytic values sit more than 30 sigma from the
threshold; the margin on the equal side is what absorbs simulator/device
noise contraction toward 0.5 (measured identical-pair P(0) under
depolarizing p = 0.02 is reported as a diagnostic in the pipeline).

This is an equality test in the simultaneous-message communication model;
it is not a speedup over classical fingerprint comparison on one machine.
"""

import math

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from . import classical_verify

M_BLOCKS = 12          # segment split into 12 blocks
K_SYMBOLS = 4096       # hash-codeword alphabet (position-seeded hash mod 4096)
MESSAGE_BITS = 12      # folded message length in bits
E_BITS = 24            # Golay-encoded fingerprint length in qubits
GOLAY_MIN_DISTANCE = 8 # extended binary Golay code (24, 12, 8)
DEFAULT_THRESHOLD = 0.75  # midpoint of the analytic interval [0.5, 1.0]

# Legacy constants (original 2026-11-07 encoding, kept for reproducibility).
LEGACY_K_SYMBOLS = 16
STEP = math.pi / 8     # legacy rotation angle per symbol step

_MASK64 = (1 << 64) - 1
_GOLDEN = 0x9E3779B97F4A7C15


def _mix64(x: int) -> int:
    """splitmix64 finaliser: strong 64-bit avalanche mixer."""
    x &= _MASK64
    x ^= x >> 30
    x = (x * 0xBF58476D1CE4E5B9) & _MASK64
    x ^= x >> 27
    x = (x * 0x94D049BB133111EB) & _MASK64
    x ^= x >> 31
    return x


def _block_bounds(n: int):
    return [round(i * n / M_BLOCKS) for i in range(M_BLOCKS + 1)]


def hash_symbols(segment: str):
    """Position-seeded hash codeword: one symbol in 0..4095 per block."""
    bounds = _block_bounds(len(segment))
    symbols = []
    for j in range(M_BLOCKS):
        fp = classical_verify.fingerprint(segment[bounds[j]:bounds[j + 1]])
        seeded = _mix64(fp + (j + 1) * _GOLDEN)
        symbols.append(seeded % K_SYMBOLS)
    return symbols


def message_of(segment: str) -> int:
    """Fold the symbol codeword to a 12-bit message (odd-weight fold)."""
    symbols = hash_symbols(segment)
    total = 25 * (len(segment) % K_SYMBOLS)
    for j, s in enumerate(symbols):
        total += (2 * j + 1) * s
    return total % K_SYMBOLS


# --- Extended binary Golay code (24, 12, 8) ---------------------------------
# Cyclic Golay (23, 12, 7) with generator polynomial
# g(x) = x^11 + x^9 + x^7 + x^6 + x^5 + x + 1, systematic encoding, plus an
# overall parity bit -> (24, 12, 8). Minimum distance 8 is verified by
# exhaustive enumeration over all 4096 messages in the test suite.

_GOLAY_G = 0b101011100011  # g(x), bit i = coefficient of x^i (degree 11)


def _golay23_encode(msg: int) -> int:
    """Systematic cyclic encoding: 12-bit message -> 23-bit codeword."""
    shifted = msg << 11
    rem = shifted
    for i in range(22, 10, -1):
        if rem >> i & 1:
            rem ^= _GOLAY_G << (i - 11)
    return shifted ^ rem  # low 11 bits now hold the parity remainder


def golay_encode(msg: int):
    """12-bit message -> list of 24 bits, pairwise distance >= 8."""
    c23 = _golay23_encode(msg)
    parity = bin(c23).count("1") & 1
    c24 = (c23 << 1) | parity
    return [(c24 >> (23 - i)) & 1 for i in range(E_BITS)]


def encoded_codeword(segment: str):
    """Full pipeline: segment -> 24-bit Golay fingerprint codeword."""
    return golay_encode(message_of(segment))


def codeword(segment: str, legacy: bool = False):
    """Fingerprint codeword of a segment.

    Default (fixed) encoding: the 24 Golay-encoded bits. With
    ``legacy=True``: the original 2026-11-07 codeword (12 symbols, unseeded
    block hashes mod 16), kept for reproducing the original runs.
    """
    if legacy:
        return _legacy_codeword(segment)
    return encoded_codeword(segment)


def codeword_hamming(a, b) -> int:
    return sum(1 for x, y in zip(a, b) if x != y)


# --- Legacy encoding (2026-11-07), reproducibility only ----------------------

def _legacy_codeword(segment: str):
    bounds = _block_bounds(len(segment))
    return [
        classical_verify.fingerprint(segment[bounds[i]:bounds[i + 1]])
        % LEGACY_K_SYMBOLS
        for i in range(M_BLOCKS)
    ]


def _legacy_fingerprint_circuit(symbols) -> QuantumCircuit:
    qc = QuantumCircuit(len(symbols))
    for j, s in enumerate(symbols):
        if s:
            qc.ry(s * STEP, j)
    return qc


def _legacy_analytic_overlap2(sym_a, sym_b) -> float:
    out = 1.0
    for x, y in zip(sym_a, sym_b):
        out *= math.cos((x - y) * STEP / 2) ** 2
    return out


# --- Fingerprint states and the SWAP test ------------------------------------

def fingerprint_circuit(code, legacy: bool = False) -> QuantumCircuit:
    """Product fingerprint state. Fixed encoding: bit b -> |b> (X if b = 1).
    Legacy: symbol s -> Ry(s * pi / 8)."""
    if legacy:
        return _legacy_fingerprint_circuit(code)
    qc = QuantumCircuit(len(code))
    for j, b in enumerate(code):
        if b:
            qc.x(j)
    return qc


def analytic_overlap2(code_a, code_b, legacy: bool = False) -> float:
    """Exact |<psi|phi>|^2. Fixed encoding: 1.0 iff the encoded codewords
    are identical, else exactly 0.0 (orthogonal differing bits)."""
    if legacy:
        return _legacy_analytic_overlap2(code_a, code_b)
    return 1.0 if list(code_a) == list(code_b) else 0.0


def swap_test_circuit(code_a, code_b, legacy: bool = False) -> QuantumCircuit:
    """Full SWAP test: ancilla + two fingerprint registers (2*L + 1 qubits)."""
    m = len(code_a)
    qc = QuantumCircuit(2 * m + 1, 1)
    anc = 0
    reg_a = list(range(1, 1 + m))
    reg_b = list(range(1 + m, 1 + 2 * m))
    qc.compose(fingerprint_circuit(code_a, legacy=legacy), qubits=reg_a,
               inplace=True)
    qc.compose(fingerprint_circuit(code_b, legacy=legacy), qubits=reg_b,
               inplace=True)
    qc.h(anc)
    for x, y in zip(reg_a, reg_b):
        qc.cswap(anc, x, y)
    qc.h(anc)
    qc.measure(anc, 0)
    return qc


def default_sim(noise_model=None):
    """MPS simulator: fingerprint states are product states and the SWAP-test
    circuit entangles them only weakly, so MPS is essentially exact here and
    far faster than statevector at these sizes. Every estimate is
    cross-checked against the analytic overlap (see verify_pair)."""
    return AerSimulator(method="matrix_product_state", noise_model=noise_model)


def estimate_p0(code_a, code_b, shots=4096, sim=None, noise_model=None,
                legacy: bool = False):
    if sim is None:
        sim = default_sim(noise_model)
    qc = swap_test_circuit(code_a, code_b, legacy=legacy)
    counts = sim.run(transpile(qc, sim), shots=shots).result().get_counts()
    return counts.get("0", 0) / shots


def verify_pair(reference: str, candidate: str, shots=4096, sim=None,
                threshold=DEFAULT_THRESHOLD, noise_model=None,
                legacy: bool = False) -> dict:
    cw_ref, cw_cand = codeword(reference, legacy=legacy), codeword(candidate, legacy=legacy)
    p0 = estimate_p0(cw_ref, cw_cand, shots=shots, sim=sim,
                     noise_model=noise_model, legacy=legacy)
    ov2 = analytic_overlap2(cw_ref, cw_cand, legacy=legacy)
    out = {
        "codeword_ref": cw_ref,
        "codeword_cand": cw_cand,
        "codeword_hamming": codeword_hamming(cw_ref, cw_cand),
        "analytic_overlap2": ov2,
        "analytic_p0": (1 + ov2) / 2,
        "estimated_p0": p0,
        "shots": shots,
        "decision_equal": p0 >= threshold,
        "threshold": threshold,
        "ground_truth_equal": reference == candidate,
        "encoding": "legacy-2026-11-07" if legacy else "golay-2026-11-08",
    }
    if not legacy:
        out["hash_symbols_ref"] = hash_symbols(reference)
        out["hash_symbols_cand"] = hash_symbols(candidate)
        out["message_ref"] = message_of(reference)
        out["message_cand"] = message_of(candidate)
    return out
