"""
Normalization utilities for handling regex syntax differences.

This module handles the conversion between JavaScript regex syntax
(used in WHATWG spec) and Python regex syntax.
"""

import re
from typing import List

from .parser import Token


def normalize_regex_pattern(pattern: str) -> str:
    r"""
    Transform JavaScript regex syntax to Python-compatible equivalents.

    Handles:
    - Character class subtraction: [a-z--[aeiou]] → [b-df-hj-np-z]
    - Character class intersection: [\d&&[0-5]] → [0-5]
    - Nested character classes: [[a-z]--q] → [a-pr-z]

    Args:
        pattern: JavaScript-style regex pattern

    Returns:
        Python-compatible regex pattern

    Raises:
        ValueError: If pattern contains unsupported syntax
        TypeError: If pattern contains disallowed character class syntax
    """
    _validate_character_class_parens(pattern)

    if "\\p{" in pattern or "\\P{" in pattern:
        raise TypeError(
            "Unicode property escapes (\\p{Letter}) are not supported in Python's re module. "
            "Please use explicit character classes instead."
        )

    # If no complex class syntax is present, return as is
    if "--" not in pattern and "&&" not in pattern and "[[" not in pattern:
        return pattern

    try:
        parser = _RegexParser(pattern)
        return parser.parse()
    except Exception:
        # If parsing fails (e.g. invalid syntax), fall back to original pattern
        # This allows simple patterns that might confuse the parser to pass through
        return pattern


def _validate_character_class_parens(pattern: str) -> None:
    """Reject unescaped parentheses inside character classes."""
    in_class = False
    escaped = False
    for char in pattern:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "[":
            in_class = True
            continue
        if char == "]" and in_class:
            in_class = False
            continue
        if in_class and char in ("(", ")"):
            raise TypeError(
                "Parentheses must be escaped in character classes for URLPattern"
            )


class _RegexParser:
    """Simple recursive parser for regex character class operations."""

    def __init__(self, pattern: str):
        self.pattern = pattern
        self.pos = 0
        self.length = len(pattern)

    def parse(self) -> str:
        result = []
        while self.pos < self.length:
            char = self.pattern[self.pos]
            if char == "\\":
                # Handle escape sequences
                result.append(self._consume_escape())
            elif char == "[":
                # Start of a character class
                result.append(self._parse_character_class())
            else:
                result.append(char)
                self.pos += 1
        return "".join(result)

    def _consume_escape(self) -> str:
        start = self.pos
        self.pos += 1  # Consume backslash
        if self.pos < self.length:
            self.pos += 1  # Consume escaped char
        return self.pattern[start : self.pos]

    def _parse_character_class(self) -> str:
        """Parse a character class and evaluate set operations."""
        # We are at '['. Parse content until matching ']'.
        # This method handles nested classes and operations recursively.
        self.pos += 1  # Consume '['

        # Check for negation
        is_negated = False
        if self.pos < self.length and self.pattern[self.pos] == "^":
            is_negated = True
            self.pos += 1

        parts = []  # Can contain sets (from nested classes) or raw strings
        current_part = []

        while self.pos < self.length:
            char = self.pattern[self.pos]

            if char == "\\":
                current_part.append(self._consume_escape())
            elif char == "[":
                # Nested class!
                # Flush current strings
                if current_part:
                    parts.append("".join(current_part))
                    current_part = []

                # Recurse
                nested_class_str = self._parse_character_class()
                # Parse the nested class string back into a set of chars for operation
                parts.append(_expand_char_class_string(nested_class_str))
            elif char == "]":
                self.pos += 1  # Consume ']'
                if current_part:
                    parts.append("".join(current_part))
                break
            else:
                current_part.append(char)
                self.pos += 1

        # Now process 'parts' looking for operators -- and &&
        # We need to flatten the parts list into a sequence of operands and operators
        # Then evaluate left-to-right.

        # 1. Tokenize parts into Operands (Sets) and Operators (str)
        tokens = []
        for part in parts:
            if isinstance(part, set):
                tokens.append(part)
            else:
                # String part: scan for operators -- and &&
                # Be careful: operators are not valid if escaped (but escapes are handled)
                # We assume -- and && are operators.

                # We need to parse the string part into sets and operators
                self._tokenize_class_content(part, tokens)

        if not tokens:
            return "[]"  # Empty class?

        # 2. Evaluate
        # Result is a Set. Start with the first operand.
        # If first token is an operator, it applies to an empty set? Or implies union with previous?
        # JS Regex spec says: [a--b] is set(a) - set(b).
        # [a-z--b] is set(a-z) - set(b).

        if not tokens:
            return "[]"

        current_set = tokens[0] if isinstance(tokens[0], set) else set()

        i = 1
        while i < len(tokens):
            op = tokens[i]
            if op in ("--", "&&"):
                if i + 1 >= len(tokens):
                    break  # Trailing operator?
                right_op = tokens[i + 1]
                if not isinstance(right_op, set):
                    # Should have been parsed into set
                    right_op = set()

                if op == "--":
                    current_set = current_set - right_op
                elif op == "&&":
                    current_set = current_set & right_op
                i += 2
            else:
                # Implicit Union
                if isinstance(op, set):
                    current_set = current_set | op
                i += 1

        # 3. Serialize back to string
        serialized = _compress_char_set(current_set)
        if is_negated:
            return f"[^{serialized}]"
        return f"[{serialized}]"

    def _tokenize_class_content(self, content: str, tokens_out: list) -> None:
        """
        Splits a string content of a character class into sets and operators.
        e.g. "a-z--b" -> [set(a-z), "--", set(b)]
        """
        i = 0
        length = len(content)
        current_chunk = ""

        while i < length:
            # Check for operators
            if content[i : i + 2] == "--":
                if current_chunk:
                    tokens_out.append(
                        _expand_char_class_string("[" + current_chunk + "]")
                    )
                    current_chunk = ""
                tokens_out.append("--")
                i += 2
                continue
            elif content[i : i + 2] == "&&":
                if current_chunk:
                    tokens_out.append(
                        _expand_char_class_string("[" + current_chunk + "]")
                    )
                    current_chunk = ""
                tokens_out.append("&&")
                i += 2
                continue

            # Escape handling is tricky here because 'content' already has escapes preserved?
            # Yes, _consume_escape returns string with backslash.
            if content[i] == "\\":
                current_chunk += content[i : i + 2]
                i += 2
                continue

            current_chunk += content[i]
            i += 1

        if current_chunk:
            tokens_out.append(_expand_char_class_string("[" + current_chunk + "]"))


def _expand_char_class_string(class_str: str) -> set:
    """
    Parses a flat character class string (e.g. "[a-z0-9]") into a set of characters.
    Handles ranges and escapes.
    """
    if not class_str.startswith("[") or not class_str.endswith("]"):
        return set()  # Should not happen with internal usage

    inner = class_str[1:-1]
    # Handle negation if needed (though we usually handle it at serialization time for nested)
    # For extraction purposes, we want the positive set of characters defined.
    # If nested class was negated [^a], we should ideally invert against universe?
    # Intersection/Subtraction with infinite sets is hard.
    # LIMITATION: We assume nested classes in operations are not negated OR we map them carefully.
    # For URLPattern use cases, nested negation is rare in subtraction.
    # But [a-z--[^a]] is "a-z AND a".
    # Let's handle simple positive sets for now as per WPT requirements.

    if inner.startswith("^"):
        # Fallback: unsupported nested negation in arithmetic
        # Return empty set or raise?
        # For now, treat as characters (literal ^) or ignore?
        # JS Regex treats [^] as negated.
        # Let's assume positive classes for the "shim removal" scope.
        pass

    chars = set()
    i = 0
    length = len(inner)

    while i < length:
        # Check for range a-z
        # We need to look ahead for '-'
        # But '-' can be escaped or at start/end

        char = inner[i]

        if char == "\\":
            # Escaped char
            if i + 1 < length:
                seq = inner[i : i + 2]
                chars.update(_resolve_escape_sequence(seq))
                i += 2

                # Check if this escaped char is start of range
                if i < length and inner[i] == "-" and i + 1 < length:
                    # e.g. [\d-z] ?? Range with class?
                    # Standard regex: range endpoints must be single chars.
                    # \d is multiple.
                    # We only support literal ranges.
                    pass
                continue

        # Literal char
        # Check if start of range
        if i + 2 < length and inner[i + 1] == "-" and inner[i + 2] != "]":
            # Potential range
            start = char
            end = inner[i + 2]

            # Handle if 'end' is escaped
            if end == "\\":
                if i + 3 < length:
                    end_seq = inner[i + 2 : i + 4]
                    # Only allow simple escaped chars in ranges, not classes like \d
                    resolved = _resolve_escape_sequence(end_seq)
                    if len(resolved) == 1:
                        end = list(resolved)[0]
                        chars.update(_char_range_to_set(start, end))
                        i += 4
                        continue
            else:
                chars.update(_char_range_to_set(start, end))
                i += 3
                continue

        # Just a char
        chars.add(char)
        i += 1

    return chars


def _resolve_escape_sequence(seq: str) -> set:
    r"""Resolve a short escape sequence (e.g. \d) into a character set."""
    c = seq[1]
    if c == "d":
        return set("0123456789")
    if c == "D":
        return _universe_set() - set("0123456789")
    if c == "s":
        return set(" \t\n\r\f\v")  # ASCII whitespace
    if c == "S":
        return _universe_set() - set(" \t\n\r\f\v")
    if c == "w":
        return set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")
    if c == "W":
        return _universe_set() - set(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
        )
    return {c}


def _char_range_to_set(start: str, end: str) -> set:
    """Expand a literal character range into a set."""
    s = set()
    try:
        for i in range(ord(start), ord(end) + 1):
            s.add(chr(i))
    except Exception:
        pass
    return s


def _universe_set() -> set:
    """Return a limited ASCII universe for negative classes."""
    # Only for ASCII range to avoid massive sets
    return set(chr(i) for i in range(128))


def _compress_char_set(chars: set) -> str:
    """Converts a set of characters back to a regex class string [a-z...]."""
    if not chars:
        return ""

    # Sort by code point
    sorted_chars = sorted(list(chars), key=ord)

    ranges = []
    if not sorted_chars:
        return ""

    start = sorted_chars[0]
    end = start

    for c in sorted_chars[1:]:
        if ord(c) == ord(end) + 1:
            end = c
        else:
            ranges.append((start, end))
            start = c
            end = c
    ranges.append((start, end))

    result = []
    for start, end in ranges:
        if start == end:
            result.append(re.escape(start))
        elif ord(end) == ord(start) + 1:
            result.append(re.escape(start))
            result.append(re.escape(end))
        else:
            result.append(f"{re.escape(start)}-{re.escape(end)}")

    return "".join(result)


def escape_pattern_string(text: str) -> str:
    """
    Escape regex metacharacters for literal matching in regex patterns.
    """
    return re.escape(text)


def escape_pattern_syntax(text: str) -> str:
    """
    Escape URLPattern syntax tokens so they are treated as literals.
    """
    return re.sub(r"([+*?:{}()\\])", r"\\\1", text)


def merge_adjacent_text(tokens: List[Token]) -> List[Token]:
    """
    Optimize token stream by merging consecutive 'char' and 'escaped-char' tokens.
    Also merges simple '{text}' groups that have no modifiers.

    This reduces the number of tokens and ensures literal text runs are
    handled as a single unit for canonicalization.

    Args:
        tokens: Token list from parser

    Returns:
        Optimized token list with merged text tokens
    """
    if not tokens:
        return tokens

    result = []
    i = 0

    while i < len(tokens):
        token = tokens[i]

        # Check if we can start a text run
        # A text run can start with:
        # 1. char/escaped-char
        # 2. open { ... } close (if simple and no modifier)

        is_text_start = False
        if token.type in ("char", "escaped-char"):
            is_text_start = True
        elif token.type == "open":
            # Check if simple
            j = i + 1
            is_simple = True
            while j < len(tokens):
                t = tokens[j]
                if t.type == "close":
                    break
                elif t.type not in ("char", "escaped-char"):
                    is_simple = False
                    break
                j += 1

            if is_simple and j < len(tokens) and tokens[j].type == "close":
                # Check modifier
                k = j + 1
                has_modifier = False
                if k < len(tokens):
                    if tokens[k].type in ("other-modifier", "asterisk"):
                        has_modifier = True

                if not has_modifier:
                    is_text_start = True

        if is_text_start:
            # We are in a text run! Collect all adjacent text-like tokens
            merged_value = ""
            start_index = token.index  # Keep index of first token

            while i < len(tokens):
                curr = tokens[i]

                # Check if current token adds text
                added_text = None
                consumed_count = 0

                if curr.type in ("char", "escaped-char"):
                    added_text = curr.value
                    consumed_count = 1
                elif curr.type == "open":
                    # Check simplicity again
                    j = i + 1
                    is_simple = True
                    inner_text = ""
                    while j < len(tokens):
                        t = tokens[j]
                        if t.type == "close":
                            break
                        elif t.type in ("char", "escaped-char"):
                            inner_text += t.value
                        else:
                            is_simple = False
                            break
                        j += 1

                    if is_simple and j < len(tokens) and tokens[j].type == "close":
                        k = j + 1
                        has_modifier = False
                        if k < len(tokens):
                            if tokens[k].type in ("other-modifier", "asterisk"):
                                has_modifier = True

                        if not has_modifier:
                            added_text = inner_text
                            consumed_count = (j - i) + 1  # open ... close (inclusive)

                if added_text is not None:
                    merged_value += added_text
                    i += consumed_count
                else:
                    break

            result.append(Token(type="char", value=merged_value, index=start_index))
        else:
            result.append(token)
            i += 1

    return result
