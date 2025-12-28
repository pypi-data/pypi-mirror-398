"""
Manual numerology, weighted sums, backend number, and 9-centric folding.

No imports; only Python primitives.
"""


def _len(s):
    n = 0
    for _ in s:
        n += 1
    return n


def ascii_upper(ch):
    # Convert a-z to A-Z without .upper()
    o = ord(ch)
    if 97 <= o <= 122:
        return chr(o - 32)
    return ch


def numerology_value(ch):
    # A=1..I=9, J=1..R=9, S=1..Z=8
    # Non-letters contribute 0
    cu = ascii_upper(ch)
    o = ord(cu)
    if 65 <= o <= 90:
        # 0-based within alphabet
        k = o - 65  # 0..25
        # Map to 1..9 repeating
        return (k % 9) + 1
    return 0


def numerology_sum(token_text):
    total = 0
    for ch in token_text:
        total += numerology_value(ch)
    return total


def weighted_char_sum(token_text):
    # S = sum( ASCII(char) * i ), i starts from 1
    i = 1
    total = 0
    for ch in token_text:
        total += ord(ch) * i
        i += 1
    return total


def compose_backend_number(token_text, position_in_sentence, uid, neighbor_prev_uid, neighbor_next_uid, embedding_bit):
    # Compute S
    s = weighted_char_sum(token_text)
    # Optionally multiply by token length
    length = 0
    for _ in token_text:
        length += 1
    s = s * (1 + (length - 1))  # multiply by length
    # Add position
    s = s + position_in_sentence
    # Numerology
    s_num = s + numerology_sum(token_text)
    # XOR with uid (bitwise on Python int)
    m = s_num ^ uid
    # Add neighbors and embedding bit
    m = m + (neighbor_prev_uid if neighbor_prev_uid is not None else 0)
    m = m + (neighbor_next_uid if neighbor_next_uid is not None else 0)
    m = m + (1 if embedding_bit else 0)
    # Ensure non-negative (Python ints are unbounded; just keep as-is)
    return m


def digital_root_9(n):
    # 9-centric digital root in 1..9
    if n <= 0:
        # Map non-positive to 9 to keep sacred-9 emphasis
        return 9
    r = (n - 1) % 9
    return r + 1


def fold_to_digit_9_centric(m, embedding_bit):
    d = digital_root_9(m)
    if embedding_bit:
        d = digital_root_9(d + 1)
    return d