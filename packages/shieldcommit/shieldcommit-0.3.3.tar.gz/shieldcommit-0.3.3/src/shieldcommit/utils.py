import math

def shannon_entropy(s: str) -> float:
    """Compute Shannon entropy for a string."""
    if not s:
        return 0.0
    probs = [s.count(c) / len(s) for c in set(s)]
    return -sum(p * math.log2(p) for p in probs)

def is_high_entropy(s: str, threshold=4.0) -> bool:
    return shannon_entropy(s) >= threshold
