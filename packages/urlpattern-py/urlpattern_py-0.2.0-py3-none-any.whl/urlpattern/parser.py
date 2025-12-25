"""
Tokenizer for URL Pattern strings.

This module converts raw pattern strings into a stream of tokens
following the WHATWG URL Pattern Standard specification.
"""

import unicodedata
from typing import List, NamedTuple


class Token(NamedTuple):
    """
    Represents a single lexical token in a URL pattern.

    Attributes:
        type: Token type identifier following WHATWG spec.
        value: The actual string content of the token.
        index: Position in the original pattern string.
    """

    type: str
    value: str
    index: int


def is_identifier_start_char(char: str) -> bool:
    """Check if a character can start a valid identifier."""
    if not char:
        return False
    if char in ("$", "_"):
        return True
    codepoint = ord(char)
    if codepoint < 128:
        return ("A" <= char <= "Z") or ("a" <= char <= "z")
    if char.isidentifier():
        return True
    return unicodedata.category(char) in ("Ll", "Lu", "Lt", "Lo", "Lm", "Nl")


def is_identifier_part_char(char: str) -> bool:
    """Check if a character can be part of a valid identifier."""
    if not char:
        return False
    codepoint = ord(char)
    if codepoint < 128:
        return char.isalnum() or char in ("$", "_")
    if is_identifier_start_char(char):
        return True
    if char.isdigit() or char in ("\u200c", "\u200d"):
        return True
    return unicodedata.category(char) in ("Mn", "Mc", "Nd", "Pc")


class Tokenizer:
    """
    Stateful tokenizer for URL patterns.
    """

    def __init__(self, pattern_string: str, policy: str = "lenient"):
        self.pattern_string = pattern_string
        self.policy = policy
        self.length = len(pattern_string)
        self.index = 0
        self.tokens: List[Token] = []
        self._append = self.tokens.append

    def tokenize(self) -> List[Token]:
        """Convert the pattern string into a list of tokens."""
        while self.index < self.length:
            if not self._try_consume_special():
                self._consume_char()

        self._append(Token(type="end", value="", index=self.length))
        return self.tokens

    def _tokenizing_error(self, next_pos: int, value_pos: int) -> int:
        if self.policy == "strict":
            raise TypeError(f"Invalid character at index {value_pos}")
        value = self.pattern_string[value_pos:next_pos]
        self._append(Token(type="invalid-char", value=value, index=value_pos))
        return next_pos

    def _consume_char(self) -> None:
        char = self.pattern_string[self.index]
        self._append(Token(type="char", value=char, index=self.index))
        self.index += 1

    def _try_consume_special(self) -> bool:
        """
        Try to consume a special token (wildcard, modifier, escape, group, name).
        Returns True if a token was consumed, False if it was a regular char.
        """
        char = self.pattern_string[self.index]

        if char == "*":
            self._append(Token(type="asterisk", value="*", index=self.index))
            self.index += 1
            return True

        if char in ("+", "?"):
            self._append(Token(type="other-modifier", value=char, index=self.index))
            self.index += 1
            return True

        if char == "\\":
            return self._consume_escaped_char()

        if char == "{":
            self._append(Token(type="open", value="{", index=self.index))
            self.index += 1
            return True

        if char == "}":
            self._append(Token(type="close", value="}", index=self.index))
            self.index += 1
            return True

        if char == ":":
            return self._consume_name()

        if char == "(":
            return self._consume_regexp_group()

        return False

    def _consume_escaped_char(self) -> bool:
        if self.index + 1 >= self.length:
            self.index = self._tokenizing_error(self.index + 1, self.index)
            return True

        escaped_char = self.pattern_string[self.index + 1]
        self._append(Token(type="escaped-char", value=escaped_char, index=self.index))
        self.index += 2
        return True

    def _consume_name(self) -> bool:
        name_start = self.index + 1
        name_end = name_start

        if name_end < self.length:
            first_char = self.pattern_string[name_end]
            if ord(first_char) < 128 and not (
                ("A" <= first_char <= "Z")
                or ("a" <= first_char <= "z")
                or first_char in ("$", "_")
            ):
                self.index = self._tokenizing_error(name_start, self.index)
                return True

        while name_end < self.length:
            name_char = self.pattern_string[name_end]
            codepoint = ord(name_char)
            if codepoint < 128:
                valid = name_char.isalnum() or name_char in ("$", "_")
            else:
                is_first = name_end == name_start
                if is_first:
                    valid = is_identifier_start_char(name_char)
                else:
                    valid = is_identifier_part_char(name_char)

            if not valid:
                break
            name_end += 1

        if name_end > name_start:
            name_value = self.pattern_string[name_start:name_end]
            self._append(Token(type="name", value=name_value, index=self.index))
            self.index = name_end
        else:
            self.index = self._tokenizing_error(name_start, self.index)

        return True

    def _consume_regexp_group(self) -> bool:
        depth = 1
        regexp_start = self.index + 1
        regexp_pos = regexp_start
        error = False

        while regexp_pos < self.length:
            regexp_char = self.pattern_string[regexp_pos]

            if not regexp_char.isascii():
                error = True
                break

            if regexp_pos == regexp_start and regexp_char == "?":
                error = True
                break

            if regexp_char == "\\":
                if regexp_pos == self.length - 1:
                    error = True
                    break
                escaped_char = self.pattern_string[regexp_pos + 1]
                if not escaped_char.isascii():
                    error = True
                    break
                regexp_pos += 2
                continue

            if regexp_char == ")":
                depth -= 1
                if depth == 0:
                    regexp_pos += 1
                    break
            elif regexp_char == "(":
                depth += 1
                if regexp_pos == self.length - 1:
                    error = True
                    break
                if self.pattern_string[regexp_pos + 1] != "?":
                    error = True
                    break

            regexp_pos += 1

        if error:
            self.index = self._tokenizing_error(regexp_start, self.index)
            return True

        if depth != 0:
            self.index = self._tokenizing_error(regexp_start, self.index)
            return True

        regexp_length = regexp_pos - regexp_start - 1
        if regexp_length == 0:
            self.index = self._tokenizing_error(regexp_start, self.index)
            return True

        regexp_value = self.pattern_string[regexp_start : regexp_pos - 1]
        self._append(Token(type="regexp", value=regexp_value, index=self.index))
        self.index = regexp_pos
        return True


def tokenize(pattern_string: str, policy: str = "lenient") -> List[Token]:
    """
    Convert a URL pattern string into a list of tokens.

    Implements the WHATWG URL Pattern tokenization algorithm.

    Args:
        pattern_string: The pattern string to tokenize (e.g., "/users/:id")
        policy: Tokenization policy ('strict' or 'lenient'). Default 'lenient'.

    Returns:
        List of Token objects representing the parsed pattern

    Raises:
        TypeError: If the pattern contains invalid syntax in strict mode
    """
    return Tokenizer(pattern_string, policy).tokenize()
