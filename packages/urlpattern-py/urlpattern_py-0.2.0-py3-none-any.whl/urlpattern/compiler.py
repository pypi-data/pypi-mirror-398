"""
Compiler for converting tokens into Python regular expressions.

This module takes the token stream from the parser and converts it
into a valid Python `re` regex pattern.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from .normalizer import escape_pattern_string, normalize_regex_pattern
from .parser import Token


def _get_segment_wildcard_pattern(context: str, separator: Optional[str] = None) -> str:
    """
    Get the regex pattern for segment wildcards based on context and separator.
    """
    if separator:
        escaped = escape_pattern_string(separator)
        return f"[^{escaped}]+?"

    # Default patterns if no separator provided
    patterns = {
        "pathname": "[^/]+?",
        "hostname": "[^.]+?",
        "protocol": "[^:/?#]+?",
        "username": "[^:/?#@]+?",
        "password": "[^:/?#@]+?",
        "port": "\\d*",
        "search": "[^#]*?",
        "hash": ".*?",
    }
    return patterns.get(context, "[^/]+?")


def _get_full_wildcard_pattern() -> str:
    """
    Get the regex pattern for full wildcards.

    Per spec: "full-wildcard" greedily matches all code points.
    This is used for standalone * wildcards.

    Returns:
        Regex pattern string for matching everything
    """
    return ".*"


def _split_simple_group_tokens(tokens: List[Token]) -> Optional[Dict[str, Any]]:
    """Return components for a trivial {prefix:name:suffix} group or None."""
    prefix_tokens = []
    idx = 0
    while idx < len(tokens) and tokens[idx].type in ("char", "escaped-char"):
        prefix_tokens.append(tokens[idx].value)
        idx += 1

    if idx >= len(tokens):
        return None

    unit_token = tokens[idx]
    if unit_token.type not in ("name", "regexp", "asterisk"):
        return None
    idx += 1

    unit_regexp = None
    if unit_token.type == "name" and idx < len(tokens) and tokens[idx].type == "regexp":
        unit_regexp = tokens[idx]
        idx += 1

    suffix_tokens = tokens[idx:]
    if any(token.type not in ("char", "escaped-char") for token in suffix_tokens):
        return None

    return {
        "prefix": "".join(prefix_tokens),
        "unit_token": unit_token,
        "unit_regexp": unit_regexp,
        "suffix": "".join(token.value for token in suffix_tokens),
    }


class RegexCompiler:
    """
    Stateful compiler to convert a list of tokens into a Python regex string.
    """

    def __init__(
        self,
        tokens: List[Token],
        context: str,
        state: Optional[Dict],
        delimiter: Optional[str],
    ):
        self.tokens = tokens
        self.context = context
        self.delimiter = delimiter
        self.index = 0
        self.regex_parts: List[str] = []
        self._append = self.regex_parts.append
        self.group_names: List[str] = []

        # Shared state for recursion (anonymous group counts, duplicate name checks)
        self.state = (
            state
            if state is not None
            else {"anonymous_group_count": 0, "seen_names": {}}
        )

        # Determine separator
        self.separator = delimiter
        if self.separator is None:
            if context == "pathname":
                self.separator = "/"
            elif context == "hostname":
                self.separator = "."

        self.escaped_separator = (
            escape_pattern_string(self.separator) if self.separator else None
        )

    def compile(self, validate: bool = True) -> Tuple[str, List[str]]:
        """Run the compilation process."""
        while self.index < len(self.tokens):
            token = self.tokens[self.index]

            if token.type == "end":
                break
            elif token.type in ("char", "escaped-char"):
                self._handle_literal(token)
            elif token.type in ("name", "regexp", "asterisk"):
                self._handle_simple_unit(token)
            elif token.type == "open":
                self._handle_open_group(token)
            elif token.type == "other-modifier":
                raise TypeError(
                    f"Modifier '{token.value}' at index {token.index} has no preceding group"
                )
            elif token.type == "close":
                raise TypeError(f"Unmatched close brace at index {token.index}")
            elif token.type == "invalid-char":
                raise TypeError(
                    f"Invalid character '{token.value}' at index {token.index}"
                )
            else:
                # Unknown or unexpected token, skip (matches original behavior)
                self.index += 1

        regex_string = "".join(self.regex_parts)

        if validate:
            # Validate the generated regex
            try:
                re.compile(regex_string)
            except re.error as e:
                raise TypeError(f"Generated invalid regex: {regex_string}\nError: {e}")

        return regex_string, self.group_names

    def _handle_literal(self, token: Token) -> None:
        self._append(escape_pattern_string(token.value))
        self.index += 1

    def _get_next_token(self) -> Optional[Token]:
        if self.index + 1 < len(self.tokens):
            return self.tokens[self.index + 1]
        return None

    def _register_name(self, name: str) -> None:
        if name in self.state["seen_names"]:
            raise TypeError(f"Duplicate group name: {name}")
        self.state["seen_names"][name] = 0
        self.group_names.append(name)

    def _get_anonymous_group_name(self) -> str:
        name = str(self.state["anonymous_group_count"])
        self.state["anonymous_group_count"] += 1
        self.group_names.append(name)
        return name

    def _handle_simple_unit(self, token: Token) -> None:
        """Handle name, regexp, or asterisk tokens."""
        unit_pattern = ""
        unit_group_name = ""
        is_capturing = True
        is_name_token = token.type == "name"
        is_asterisk_token = token.type == "asterisk"

        # Lookahead for custom regexp after name
        next_token = self._get_next_token()
        consumed_next = False

        if token.type == "name":
            name = token.value
            if next_token and next_token.type == "regexp":
                unit_pattern = normalize_regex_pattern(next_token.value)
                consumed_next = True
            else:
                unit_pattern = _get_segment_wildcard_pattern(
                    self.context, self.separator
                )

            self._register_name(name)
            unit_group_name = name

        elif token.type == "regexp":
            unit_pattern = normalize_regex_pattern(token.value)
            unit_group_name = self._get_anonymous_group_name()

        elif token.type == "asterisk":
            unit_pattern = _get_full_wildcard_pattern()
            unit_group_name = self._get_anonymous_group_name()

        next_index_after_unit = self.index + (2 if consumed_next else 1)
        self._apply_modifier(
            unit_pattern,
            unit_group_name,
            is_capturing,
            is_name_token,
            is_asterisk_token,
            next_index_after_unit,
        )

    def _handle_open_group(self, token: Token) -> None:
        """Handle { ... } groups."""
        # Find matching close brace
        depth = 1
        group_start = self.index + 1
        group_end = group_start

        while group_end < len(self.tokens) and depth > 0:
            t = self.tokens[group_end]
            if t.type == "open":
                depth += 1
            elif t.type == "close":
                depth -= 1
            group_end += 1

        if depth != 0:
            raise TypeError(f"Unclosed group starting at index {token.index}")

        group_tokens = self.tokens[group_start : group_end - 1]

        # Check for nested groups
        for t in group_tokens:
            if t.type == "open":
                raise TypeError(f"Nested groups are not allowed at index {t.index}")

        open_group_simple = _split_simple_group_tokens(group_tokens)
        next_index_after_group = group_end

        # Check if we can apply the simple group optimization
        modifier, modifier_len = self._peek_modifier(next_index_after_group)

        if (
            modifier in ("*", "+")
            and open_group_simple is not None
            and open_group_simple["unit_token"].type == "name"
        ):
            self._handle_optimized_open_group(
                open_group_simple, modifier, next_index_after_group + modifier_len
            )
            return

        # Standard group handling (recursive compilation)
        # Recurse using the wrapper function to maintain abstraction
        group_regex, group_group_names = compile_tokens_to_regex(
            group_tokens, self.context, self.state, self.separator, validate=False
        )

        self.group_names.extend(group_group_names)

        # Open groups are non-capturing containers
        self._apply_modifier(
            group_regex,
            "",  # No group name for the container itself
            False,  # Not capturing
            False,  # Not a name token
            False,  # Not asterisk
            next_index_after_group,
        )

    def _handle_optimized_open_group(
        self, simple_group: Dict[str, Any], modifier: str, next_index: int
    ) -> None:
        """Handle the special optimized case for {prefix:name:suffix}+ or *."""
        name_token = simple_group["unit_token"]
        name = name_token.value
        self._register_name(name)

        if simple_group["unit_regexp"] is not None:
            unit_pattern = normalize_regex_pattern(simple_group["unit_regexp"].value)
        else:
            unit_pattern = _get_segment_wildcard_pattern(self.context, self.separator)

        prefix_regex = escape_pattern_string(simple_group["prefix"])
        suffix_regex = escape_pattern_string(simple_group["suffix"])

        joiner = f"{suffix_regex}{prefix_regex}"
        if joiner:
            core = f"{unit_pattern}(?:{joiner}{unit_pattern})*"
        else:
            core = f"{unit_pattern}(?:{unit_pattern})*"

        if modifier == "*":
            if prefix_regex or suffix_regex:
                self._append(f"(?:{prefix_regex}(?P<{name}>{core}){suffix_regex})?")
            else:
                self._append(f"(?P<{name}>{core})?")
        else:  # modifier == "+"
            if prefix_regex or suffix_regex:
                self._append(f"{prefix_regex}(?P<{name}>{core}){suffix_regex}")
            else:
                self._append(f"(?P<{name}>{core})")

        self.index = next_index

    def _peek_modifier(self, index: int) -> Tuple[Optional[str], int]:
        """Look ahead for a modifier token. Returns (modifier, length_consumed)."""
        if index < len(self.tokens):
            token = self.tokens[index]
            if token.type == "other-modifier":
                return token.value, 1
            elif token.type == "asterisk":
                return "*", 1
        return None, 0

    def _apply_modifier(
        self,
        unit_pattern: str,
        unit_group_name: str,
        is_capturing: bool,
        is_name_token: bool,
        is_asterisk_token: bool,
        next_index: int,
    ) -> None:
        """
        Constructs the final regex for a unit, applying modifiers (?, +, *)
        and handling segment prefixes.
        """
        modifier, modifier_len = self._peek_modifier(next_index)
        next_index += modifier_len

        # In this context, 'open' groups are passed with is_capturing=False,
        # while simple units (name, regexp, asterisk) are passed with is_capturing=True.
        is_open_group = not is_capturing

        # Check for preceding separator
        has_preceding_separator = False
        if (
            self.separator
            and not is_open_group
            and self.regex_parts
            and self.regex_parts[-1].endswith(self.escaped_separator)
        ):
            has_preceding_separator = True

        atom = f"(?:{unit_pattern})"

        if modifier == "?":
            if has_preceding_separator:
                # Case: /:foo? -> (?:/(?P<foo>...))?
                last_part = self.regex_parts.pop()
                prefix = last_part[: -len(self.escaped_separator)]
                if prefix:
                    self._append(prefix)

                if is_capturing:
                    if is_name_token:
                        self._append(
                            f"(?:{self.escaped_separator}(?P<{unit_group_name}>{unit_pattern}))?"
                        )
                    else:
                        self._append(f"(?:{self.escaped_separator}({unit_pattern}))?")
                else:
                    self._append(f"(?:{self.escaped_separator}{unit_pattern})?")
            else:
                # Standard optional
                actual_pattern = unit_pattern
                # Python re matches (.*)? as "" instead of None when empty.
                if unit_pattern == ".*":
                    actual_pattern = ".+"

                if is_capturing:
                    if is_name_token:
                        self._append(f"(?P<{unit_group_name}>{actual_pattern})?")
                    else:
                        self._append(f"({actual_pattern})?")
                else:
                    self._append(f"{atom}?")

        elif modifier == "+":
            # Note: is_asterisk_token check comes from original logic
            should_repeat_separator = (
                self.separator
                and not is_open_group  # token.type != "open"
                and not is_asterisk_token
            )

            if should_repeat_separator:
                # Complex pattern: atom (?: separator atom )*
                complex_pattern = (
                    f"{unit_pattern}(?:{self.escaped_separator}{unit_pattern})*"
                )

                if is_name_token:
                    self._append(f"(?P<{unit_group_name}>{complex_pattern})")
                elif is_capturing:
                    self._append(f"({complex_pattern})")
                else:
                    self._append(f"(?:{complex_pattern})")
            else:
                repeated_atom = f"{atom}+"
                if is_name_token:
                    self._append(f"(?P<{unit_group_name}>{repeated_atom})")
                elif is_capturing:
                    self._append(f"({repeated_atom})")
                else:
                    self._append(repeated_atom)

        elif modifier == "*":
            should_repeat_separator = (
                self.separator and not is_open_group and not is_asterisk_token
            )

            if has_preceding_separator:
                last_part = self.regex_parts.pop()
                prefix = last_part[: -len(self.escaped_separator)]
                if prefix:
                    self._append(prefix)

                if should_repeat_separator:
                    core_pattern = (
                        f"{unit_pattern}(?:{self.escaped_separator}{unit_pattern})*"
                    )
                else:
                    core_pattern = f"{atom}+"

                if is_name_token:
                    self._append(
                        f"(?:{self.escaped_separator}(?P<{unit_group_name}>{core_pattern}))?"
                    )
                elif is_capturing:
                    self._append(f"(?:{self.escaped_separator}({core_pattern}))?")
                else:
                    self._append(f"(?:{self.escaped_separator}{core_pattern})?")
            else:
                if should_repeat_separator:
                    core_pattern = (
                        f"{unit_pattern}(?:{self.escaped_separator}{unit_pattern})*"
                    )
                    if is_name_token:
                        self._append(f"(?P<{unit_group_name}>{core_pattern})?")
                    elif is_capturing:
                        self._append(f"({core_pattern})?")
                    else:
                        self._append(f"(?:{core_pattern})?")
                else:
                    repeated_atom = f"{atom}*"
                    if is_name_token:
                        self._append(f"(?P<{unit_group_name}>{repeated_atom})")
                    elif is_capturing:
                        self._append(f"({repeated_atom})")
                    else:
                        self._append(repeated_atom)

        else:
            # No modifier
            if is_capturing:
                if is_name_token:
                    self._append(f"(?P<{unit_group_name}>{unit_pattern})")
                else:
                    self._append(f"({unit_pattern})")
            else:
                self._append(atom)

        self.index = next_index


def compile_tokens_to_regex(
    tokens: List[Token],
    context: str = "pathname",
    _state: Optional[Dict[str, Any]] = None,
    delimiter: Optional[str] = None,
    validate: bool = True,
) -> Tuple[str, List[str]]:
    """
    Compile URL pattern tokens into a Python regex string.

    This function wraps RegexCompiler to maintain the existing API.
    """
    compiler = RegexCompiler(tokens, context, _state, delimiter)
    return compiler.compile(validate=validate)
