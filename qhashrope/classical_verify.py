"""Classical verify stage: hashrope polynomial fingerprints.

Ground truth for a pair is exact string equality; the hashrope check compares
rope fingerprints (61-bit Mersenne polynomial hash) and full rope equality.
"""

import hashrope

_H = hashrope.PolynomialHash()  # default profile: prime 2**61 - 1, base 131


def fingerprint(segment: str) -> int:
    """hashrope root fingerprint of a segment."""
    return hashrope.rope_hash(hashrope.rope_from_bytes(segment.encode(), _H))


def ropes_equal(a: str, b: str) -> bool:
    ra = hashrope.rope_from_bytes(a.encode(), _H)
    rb = hashrope.rope_from_bytes(b.encode(), _H)
    return hashrope.rope_equal(ra, rb)


def verify_pair(reference: str, candidate: str) -> dict:
    return {
        "fingerprint_ref": fingerprint(reference),
        "fingerprint_cand": fingerprint(candidate),
        "fingerprint_match": fingerprint(reference) == fingerprint(candidate),
        "rope_equal": ropes_equal(reference, candidate),
        "ground_truth_equal": reference == candidate,
    }
