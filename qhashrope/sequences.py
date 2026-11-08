"""Deterministic DNA-like test segments and point-mutation pair generation."""

import random

BASES = "ACGT"
SEED = 20261107
SEGMENT_LEN = 96  # bp


def make_segment(rng: random.Random, length: int = SEGMENT_LEN) -> str:
    return "".join(rng.choice(BASES) for _ in range(length))


def mutate(segment: str, k: int, rng: random.Random) -> str:
    """Return a copy of `segment` with exactly k point substitutions."""
    if k == 0:
        return segment
    positions = rng.sample(range(len(segment)), k)
    chars = list(segment)
    for p in positions:
        choices = [b for b in BASES if b != chars[p]]
        chars[p] = rng.choice(choices)
    return "".join(chars)


def hamming(a: str, b: str) -> int:
    return sum(1 for x, y in zip(a, b) if x != y)


def make_pair_set(n_per_class=(3, 5, 5, 5), seed: int = SEED):
    """Build labelled pairs: (reference, candidate, n_mutations, ground_truth_equal).

    n_per_class counts are for classes [identical, 1, 3, 10] mutations.
    """
    rng = random.Random(seed)
    base = make_segment(rng)
    classes = [0, 1, 3, 10]
    pairs = []
    for cls, count in zip(classes, n_per_class):
        for _ in range(count):
            cand = mutate(base, cls, rng) if cls else base
            assert hamming(base, cand) == cls
            pairs.append(
                {
                    "reference": base,
                    "candidate": cand,
                    "mutations": cls,
                    "equal": cls == 0,
                }
            )
    return base, pairs
