"""
Deterministic UID generator and neighbor-aware sequencing without imports.

Implements a simple xorshift64* PRNG seeded by a provided integer.
Generates sequential UIDs for tokens by advancing the PRNG.
"""


class XorShift64Star:
    def __init__(self, seed):
        if seed == 0:
            seed = 0x9E3779B97F4A7C15  # non-zero default
        self.state = seed & ((1 << 64) - 1)

    def next_u64(self):
        x = self.state
        x ^= (x >> 12) & ((1 << 64) - 1)
        x ^= (x << 25) & ((1 << 64) - 1)
        x ^= (x >> 27) & ((1 << 64) - 1)
        # multiply by a constant; keep 64-bit wrap
        x = (x * 2685821657736338717) & ((1 << 64) - 1)
        self.state = x
        return x


def assign_uids(tokens, seed):
    rng = XorShift64Star(seed)
    assigned = []
    for t in tokens:
        uid = rng.next_u64()
        assigned.append({
            "uid": uid,
            "text": t["text"],
            "index": t["index"],
        })
    return assigned


def neighbor_uids(token_records):
    n = 0
    for _ in token_records:
        n += 1
    result = []
    i = 0
    while i < n:
        prev_uid = token_records[i - 1]["uid"] if i > 0 else None
        next_uid = token_records[i + 1]["uid"] if (i + 1) < n else None
        rec = token_records[i]
        result.append({
            "uid": rec["uid"],
            "text": rec["text"],
            "index": rec["index"],
            "prev_uid": prev_uid,
            "next_uid": next_uid,
        })
        i += 1
    return result