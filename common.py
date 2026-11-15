"""Shared helpers for the BTC / Polymarket research scripts.

Deliberately small: only the functions that were copy-pasted across files.
"""
def wilson(k, n, z=1.96):
    """Wilson score interval for a binomial proportion -> (low, high)."""
    if n <= 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return c - h, c + h


def maximal_runs(labels):
    """[(label, length, start_index)] for every maximal run of equal labels."""
    out, i, n = [], 0, len(labels)
    while i < n:
        j = i
        while j + 1 < n and labels[j + 1] == labels[i]:
            j += 1
        out.append((labels[i], j - i + 1, i))
        i = j + 1
    return out


def segments(ts, step=300):
    """Split a sorted timestamp list into contiguous stretches of `step` seconds."""
    if not ts:
        return []
    out, cur = [], [ts[0]]
    for a, b in zip(ts, ts[1:]):
        if b - a == step:
            cur.append(b)
        else:
            out.append(cur)
            cur = [b]
    out.append(cur)
    return out
