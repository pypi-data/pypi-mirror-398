"""
Pure-Python tokenizer core built from scratch.

Constraints:
- Python 3.13.7
- No imports from stdlib or third-party. Only language primitives.

This module implements:
- Space, word, character, byte, subword (fixed len=3), grammar tokenizers
- Basic helpers for string length, slicing, and ASCII checks without imports

Note: Without stdlib, Unicode normalization is not available. We treat the
string as-is; character tokenization uses Python's native indexing which is
codepoint-based.
"""

# Types as comments (no typing module allowed)
# TokenRecord: {"text": str, "index": int}


def _len(s):
    n = 0
    for _ in s:
        n += 1
    return n


def _is_space(ch):
    # Minimal space detection: space, tab, newline, carriage return
    # Avoid using str.isspace()
    return ch == " " or ch == "\t" or ch == "\n" or ch == "\r"


def _is_alpha(ch):
    # ASCII A-Z or a-z only, no stdlib
    c = ord(ch)
    return (65 <= c <= 90) or (97 <= c <= 122)


def _is_digit(ch):
    c = ord(ch)
    return 48 <= c <= 57


def _is_word_char(ch):
    # Define word char as ASCII letter or digit; underscore considered punctuation here
    return _is_alpha(ch) or _is_digit(ch)


def tokenize_space(text):
    tokens = []
    n = _len(text)
    i = 0
    start = 0
    while i < n:
        if _is_space(text[i]):
            if start < i:
                tokens.append({"text": text[start:i], "index": start})
            # skip contiguous spaces
            i += 1
            start = i
            while i < n and _is_space(text[i]):
                i += 1
            start = i
            continue
        i += 1
    if start < n:
        tokens.append({"text": text[start:n], "index": start})
    return tokens


def tokenize_char(text):
    tokens = []
    i = 0
    for ch in text:
        tokens.append({"text": ch, "index": i})
        i += 1
    return tokens


def tokenize_word(text):
    tokens = []
    n = _len(text)
    i = 0
    start = -1
    while i < n:
        ch = text[i]
        if _is_word_char(ch):
            if start == -1:
                start = i
        else:
            if start != -1:
                tokens.append({"text": text[start:i], "index": start})
                start = -1
        i += 1
    if start != -1:
        tokens.append({"text": text[start:n], "index": start})
    return tokens


def tokenize_grammar(text):
    # words and punctuation separately; keep punctuation as individual tokens
    tokens = []
    n = _len(text)
    i = 0
    start = -1
    while i < n:
        ch = text[i]
        if _is_word_char(ch):
            if start == -1:
                start = i
        else:
            if start != -1:
                tokens.append({"text": text[start:i], "index": start})
                start = -1
            if not _is_space(ch):
                tokens.append({"text": ch, "index": i})
        i += 1
    if start != -1:
        tokens.append({"text": text[start:n], "index": start})
    return tokens


def tokenize_subword(text, chunk_len=3):
    # Split words into fixed-size chunks; non-words (spaces/punct) are emitted as-is
    tokens = []
    n = _len(text)
    i = 0
    while i < n:
        ch = text[i]
        if _is_word_char(ch):
            # capture full word
            start = i
            i += 1
            while i < n and _is_word_char(text[i]):
                i += 1
            word = text[start:i]
            wlen = _len(word)
            j = 0
            while j < wlen:
                end = j + chunk_len
                if end > wlen:
                    end = wlen
                tokens.append({"text": word[j:end], "index": start + j})
                j = end
        else:
            if not _is_space(ch):
                tokens.append({"text": ch, "index": i})
            i += 1
            # skip spaces silently (not emitted)
            while i < n and _is_space(text[i]):
                i += 1
    return tokens


def tokenize_bytes(text):
    # Manual UTF-8 encode is complex with no stdlib; as a fallback, we map each
    # codepoint to its ord() value and emit decimal string bytes per codepoint.
    # This preserves determinism without external modules.
    tokens = []
    i = 0
    for ch in text:
        code = ord(ch)
        dec = str(code)
        # emit each digit of the decimal code as a byte-like token
        j = 0
        while j < _len(dec):
            tokens.append({"text": dec[j], "index": i})
            j += 1
        i += 1
    return tokens


def all_tokenizations(text):
    return {
        "space": tokenize_space(text),
        "word": tokenize_word(text),
        "char": tokenize_char(text),
        "grammar": tokenize_grammar(text),
        "subword": tokenize_subword(text, 3),
        "byte": tokenize_bytes(text),
    }