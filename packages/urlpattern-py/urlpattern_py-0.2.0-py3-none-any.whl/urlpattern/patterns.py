import re
import urllib.parse
from typing import Any, Callable, Dict, List, Optional, Set

from .canonicalize import (
    _canonicalize_component_cached as _canonicalize_component,
)
from .canonicalize import (
    _encode_component,
    _is_ipv6_hostname,
    _replace_surrogates,
    _strip_control_whitespace,
)
from .compiler import compile_tokens_to_regex
from .constants import SPECIAL_SCHEMES
from .normalizer import escape_pattern_syntax
from .parser import is_identifier_part_char, tokenize
from .types import Modifier, Part, PartType


def _protocol_encode_callback(value: str) -> str:
    """Validate and canonicalize protocol patterns."""
    if value == "":
        return value
    if re.fullmatch(r"[-+.A-Za-z0-9]*", value):
        return value.lower()
    raise TypeError(f"Invalid protocol '{value}'.")


def _username_encode_callback(value: str) -> str:
    """Percent-encode username while preserving allowed delimiters."""
    return _encode_component(value, safe="!$&'()*+,;=%")


def _password_encode_callback(value: str) -> str:
    """Percent-encode password while preserving allowed delimiters."""
    return _encode_component(value, safe="!$&'()*+,;=%")


def _hostname_encode_callback(value: str) -> str:
    """Canonicalize hostname patterns using URL rules."""
    if value == "":
        return value
    return _canonicalize_component(value, "hostname", for_pattern=True)


def _ipv6_hostname_encode_callback(value: str) -> str:
    """Canonicalize IPv6 hostname patterns with IPv6 rules applied."""
    if value == "":
        return value
    return _canonicalize_component(
        value, "hostname", is_ipv6_context=True, for_pattern=True
    )


def _port_encode_callback(value: str) -> str:
    """Normalize a port pattern into its numeric prefix."""
    if value == "":
        return value
    # Deviation: accept leading digit prefix per WPT tests (spec would reject).
    cleaned = _strip_control_whitespace(value)
    digits = []
    for char in cleaned:
        if char.isdigit():
            digits.append(char)
        else:
            break
    if not digits:
        raise TypeError(f"Invalid port '{value}'.")
    port_value = "".join(digits)
    if int(port_value) > 65535:
        raise TypeError(f"Invalid port '{value}'.")
    return port_value


def _standard_url_pathname_encode_callback(value: str) -> str:
    """Canonicalize and percent-encode a hierarchical pathname pattern."""
    if value == "":
        return value
    value = _replace_surrogates(value)
    canonical = _canonicalize_component(
        value, "pathname", protocol="http", for_pattern=True
    )
    safe_chars = "/-._~!$&'()*+,;=:@%"
    return urllib.parse.quote(canonical, safe=safe_chars)


def _path_url_pathname_encode_callback(value: str) -> str:
    """Preserve opaque pathnames without encoding."""
    if value == "":
        return value
    return value


def _search_encode_callback(value: str) -> str:
    """Percent-encode search patterns with WHATWG-safe characters."""
    return _encode_component(value, safe="!$&'()*+,;=:@/?%{}=", replace_surrogates=True)


def _hash_encode_callback(value: str) -> str:
    """Percent-encode hash patterns with WHATWG-safe characters."""
    return _encode_component(value, safe="!$&'()*+,;=:@/?%{}=", replace_surrogates=True)


_COMPONENT_OPTIONS = {
    "protocol": {
        "delimiter": "",
        "prefixes": "",
        "encode_part": _protocol_encode_callback,
    },
    "username": {
        "delimiter": "",
        "prefixes": "",
        "encode_part": _username_encode_callback,
    },
    "password": {
        "delimiter": "",
        "prefixes": "",
        "encode_part": _password_encode_callback,
    },
    "port": {"delimiter": "", "prefixes": "", "encode_part": _port_encode_callback},
    "search": {"delimiter": "", "prefixes": "", "encode_part": _search_encode_callback},
    "hash": {"delimiter": "", "prefixes": "", "encode_part": _hash_encode_callback},
}


class PatternParser:
    """Parse a component pattern into Part objects for matching/generation."""

    def __init__(
        self,
        pattern_string: str,
        delimiter: str = "",
        prefixes: str = "",
        encode_part: Optional[Callable[[str], str]] = None,
    ):
        self.pattern_string = pattern_string
        self.delimiter = delimiter
        self.prefixes = prefixes
        self.encode_part = encode_part
        self.tokens = tokenize(pattern_string, policy="strict")
        self.result: List[Part] = []
        self.key = 0
        self.i = 0
        self.name_set: Set[Any] = set()
        self.pending_fixed: List[str] = []

        if delimiter:
            escaped = re.escape(delimiter)
            self.segment_wildcard_regex = f"[^{escaped}]+?"
        else:
            self.segment_wildcard_regex = ".+?"

    def parse(self) -> List[Part]:
        while self.i < len(self.tokens):
            char_token = self._try_consume("char")
            name_token = self._try_consume("name")
            regex_or_wildcard_token = self._try_consume("regexp")

            if not name_token and not regex_or_wildcard_token:
                regex_or_wildcard_token = self._try_consume("asterisk")

            if name_token or regex_or_wildcard_token:
                prefix = char_token or ""
                if prefix not in self.prefixes:
                    self._append_pending(prefix)
                    prefix = ""

                self._flush_pending()

                modifier_token = self._try_consume_modifier()
                self._add_part(
                    prefix, name_token, regex_or_wildcard_token, "", modifier_token
                )
                continue

            value = char_token or self._try_consume("escaped-char")
            if value:
                self._append_pending(value)
                continue

            open_token = self._try_consume("open")
            if open_token:
                prefix = self._consume_text()
                name_token = self._try_consume("name")
                regex_or_wildcard_token = self._try_consume("regexp")
                if not name_token and not regex_or_wildcard_token:
                    regex_or_wildcard_token = self._try_consume("asterisk")
                suffix = self._consume_text()
                self._must_consume("close")
                modifier_token = self._try_consume_modifier()
                self._add_part(
                    prefix, name_token, regex_or_wildcard_token, suffix, modifier_token
                )
                continue

            self._flush_pending()
            self._must_consume("end")

        return self.result

    def _encode(self, value: str) -> str:
        if self.encode_part:
            return self.encode_part(value)
        return value

    def _try_consume(self, token_type: str) -> Optional[str]:
        if self.i < len(self.tokens) and self.tokens[self.i].type == token_type:
            value = self.tokens[self.i].value
            self.i += 1
            return value
        return None

    def _try_consume_modifier(self) -> Optional[str]:
        return self._try_consume("other-modifier") or self._try_consume("asterisk")

    def _must_consume(self, token_type: str) -> str:
        value = self._try_consume(token_type)
        if value is not None:
            return value
        next_type = self.tokens[self.i].type if self.i < len(self.tokens) else "end"
        index = (
            self.tokens[self.i].index
            if self.i < len(self.tokens)
            else len(self.pattern_string)
        )
        raise TypeError(f"Unexpected {next_type} at {index}, expected {token_type}")

    def _consume_text(self) -> str:
        result_value = []
        while True:
            value = self._try_consume("char") or self._try_consume("escaped-char")
            if value is None:
                break
            result_value.append(value)
        return "".join(result_value)

    def _append_pending(self, value: str) -> None:
        if value:
            self.pending_fixed.append(value)

    def _flush_pending(self) -> None:
        if self.pending_fixed:
            self.result.append(
                Part(
                    PartType.FIXED,
                    "",
                    "",
                    self._encode("".join(self.pending_fixed)),
                    "",
                    Modifier.NONE,
                )
            )
            self.pending_fixed.clear()

    def _add_part(
        self,
        prefix,
        name_token,
        regex_or_wildcard_token,
        suffix,
        modifier_token,
    ):
        modifier = Modifier.NONE
        if modifier_token == "?":
            modifier = Modifier.OPTIONAL
        elif modifier_token == "*":
            modifier = Modifier.ZERO_OR_MORE
        elif modifier_token == "+":
            modifier = Modifier.ONE_OR_MORE

        if not name_token and not regex_or_wildcard_token and modifier == Modifier.NONE:
            self._append_pending(prefix)
            return

        self._flush_pending()

        if not name_token and not regex_or_wildcard_token:
            if not prefix:
                return
            self.result.append(
                Part(PartType.FIXED, "", "", self._encode(prefix), "", modifier)
            )
            return

        if not regex_or_wildcard_token:
            regex_value = self.segment_wildcard_regex
        elif regex_or_wildcard_token == "*":
            regex_value = ".*"
        else:
            regex_value = regex_or_wildcard_token

        part_type = PartType.REGEX
        if regex_value == self.segment_wildcard_regex:
            part_type = PartType.SEGMENT_WILDCARD
            regex_value = ""
        elif regex_value == ".*":
            part_type = PartType.FULL_WILDCARD
            regex_value = ""

        if name_token:
            name = name_token
        elif regex_or_wildcard_token:
            name = self.key
            self.key += 1
        else:
            name = ""

        if name in self.name_set:
            raise TypeError(f"Duplicate name '{name}'.")
        self.name_set.add(name)

        self.result.append(
            Part(
                part_type,
                name,
                self._encode(prefix),
                regex_value,
                self._encode(suffix),
                modifier,
            )
        )


def _parse_pattern_to_parts(
    pattern_string: str,
    *,
    delimiter: str = "",
    prefixes: str = "",
    encode_part: Optional[Callable[[str], str]] = None,
) -> List[Part]:
    return PatternParser(
        pattern_string,
        delimiter=delimiter,
        prefixes=prefixes,
        encode_part=encode_part,
    ).parse()


def _parse_options_for_component(
    component: str, protocol_pattern: str, component_pattern: str
):
    """Return parsing/encoding options for a component pattern."""
    default_options = _COMPONENT_OPTIONS.get(component)
    if default_options is not None:
        return default_options
    if component == "hostname":
        if _is_ipv6_hostname(component_pattern):
            encode_part = _ipv6_hostname_encode_callback
        else:
            encode_part = _hostname_encode_callback
        return {"delimiter": ".", "prefixes": "", "encode_part": encode_part}
    if component == "port":
        return _COMPONENT_OPTIONS[component]
    if component == "pathname":
        if _is_special_scheme_pattern(protocol_pattern, None):
            return {
                "delimiter": "/",
                "prefixes": "/",
                "encode_part": _standard_url_pathname_encode_callback,
            }
        return {
            "delimiter": "",
            "prefixes": "",
            "encode_part": _path_url_pathname_encode_callback,
        }
    if component in ("search", "hash"):
        return _COMPONENT_OPTIONS[component]
    raise TypeError(f"Invalid component '{component}'.")


def _parts_to_pattern(parts, options) -> str:
    """Serialize Part objects back into a URLPattern component string."""
    delimiter = options.get("delimiter", "")
    prefixes = options.get("prefixes", "")

    if delimiter:
        segment_wildcard_regex = f"[^{re.escape(delimiter)}]+?"
    else:
        segment_wildcard_regex = ".+?"

    chunks = []
    for i, part in enumerate(parts):
        if part.type == PartType.FIXED:
            if part.modifier == Modifier.NONE:
                chunks.append(escape_pattern_syntax(part.value))
            else:
                chunks.append("{")
                chunks.append(escape_pattern_syntax(part.value))
                chunks.append("}")
                chunks.append(part.modifier.to_string())
            continue

        custom_name = part.has_custom_name()
        needs_grouping = bool(part.suffix) or (
            bool(part.prefix) and (len(part.prefix) != 1 or part.prefix not in prefixes)
        )

        last_part = parts[i - 1] if i > 0 else None
        next_part = parts[i + 1] if i < len(parts) - 1 else None

        if (
            not needs_grouping
            and custom_name
            and part.type == PartType.SEGMENT_WILDCARD
            and part.modifier == Modifier.NONE
            and next_part
            and not next_part.prefix
            and not next_part.suffix
        ):
            if next_part.type == PartType.FIXED:
                code = next_part.value[0] if next_part.value else ""
                needs_grouping = is_identifier_part_char(code)
            else:
                needs_grouping = not next_part.has_custom_name()

        if (
            not needs_grouping
            and not part.prefix
            and last_part
            and last_part.type == PartType.FIXED
        ):
            code = last_part.value[-1] if last_part.value else ""
            needs_grouping = code in prefixes

        if needs_grouping:
            chunks.append("{")

        chunks.append(escape_pattern_syntax(part.prefix))

        if custom_name:
            chunks.append(f":{part.name}")

        if part.type == PartType.REGEX:
            chunks.append(f"({part.value})")
        elif part.type == PartType.SEGMENT_WILDCARD:
            if not custom_name:
                chunks.append(f"({segment_wildcard_regex})")
        elif part.type == PartType.FULL_WILDCARD:
            if not custom_name and (
                not last_part
                or last_part.type == PartType.FIXED
                or last_part.modifier != Modifier.NONE
                or needs_grouping
                or part.prefix != ""
            ):
                chunks.append("*")
            else:
                chunks.append("(.*)")

        if (
            part.type == PartType.SEGMENT_WILDCARD
            and custom_name
            and part.suffix
            and is_identifier_part_char(part.suffix[0])
        ):
            chunks.append("\\")

        chunks.append(escape_pattern_syntax(part.suffix))

        if needs_grouping:
            chunks.append("}")

        if part.modifier != Modifier.NONE:
            chunks.append(part.modifier.to_string())

    return "".join(chunks)


def _validate_no_nested_groups(tokens) -> None:
    """Raise if a token stream contains nested group braces."""
    depth = 0
    for token in tokens:
        if token.type == "open":
            if depth > 0:
                raise TypeError(f"Nested groups are not allowed at index {token.index}")
            depth += 1
        elif token.type == "close":
            if depth > 0:
                depth -= 1


def _validate_port_pattern(component_pattern: str, tokens) -> None:
    """Validate that a port pattern is numeric and in range when literal."""
    cleaned = _strip_control_whitespace(component_pattern)
    if not cleaned:
        return
    if any(token.type not in ("char", "escaped-char", "end") for token in tokens):
        return
    if any(not token.value.isdigit() for token in tokens if token.type != "end"):
        return
    port_num = int(cleaned)
    if port_num > 65535:
        raise TypeError("Port number out of range")


def _normalize_hostname_escapes(value: str) -> str:
    """Normalize hostname escapes to match URLPattern parsing rules."""
    special = set(".*+?^${}()|[]:\\")
    normalized = []
    i = 0
    while i < len(value):
        char = value[i]
        if char == "\\" and i + 1 < len(value):
            next_char = value[i + 1]
            if (
                next_char.isalnum() or next_char in ("_", "$") or ord(next_char) > 127
            ) and next_char not in special:
                normalized.append("\\\\")
                normalized.append(next_char)
                i += 2
                continue
            normalized.append(char)
            normalized.append(next_char)
            i += 2
            continue
        normalized.append(char)
        i += 1
    return "".join(normalized)


def _literal_protocol(pattern_value: Optional[str]) -> Optional[str]:
    """Return the literal protocol string if no pattern syntax is present."""
    if pattern_value is None:
        return None
    tokens = tokenize(pattern_value)
    if any(token.type not in ("char", "escaped-char", "end") for token in tokens):
        return None
    return "".join(token.value for token in tokens if token.type != "end")


def _literal_from_tokens(tokens) -> Optional[str]:
    """Return literal value for tokens containing no pattern syntax."""
    if not all(token.type in ("char", "escaped-char", "end") for token in tokens):
        return None
    return "".join(token.value for token in tokens if token.type != "end")


def _is_special_scheme_pattern(
    pattern_string: str,
    options: Dict = None,
    raise_on_error: bool = False,
) -> bool:
    """
    Check if a protocol pattern matches any special scheme.
    Used to determine if pathname should be treated as special (hierarchical) or opaque.
    """
    if not pattern_string:
        return True

    if pattern_string.lower() in SPECIAL_SCHEMES:
        return True

    try:
        tokens = tokenize(pattern_string)
        regex, _ = compile_tokens_to_regex(tokens, context="protocol", validate=False)
        flags = re.IGNORECASE if options and options.get("ignoreCase") else 0
        regex_obj = re.compile(f"^{regex}$", flags)

        for scheme in SPECIAL_SCHEMES:
            if regex_obj.match(scheme):
                return True
    except Exception:
        if raise_on_error:
            raise
        return False

    return False


class URLStringParser:
    """Parse a URL pattern string into components using the WHATWG spec algorithm."""

    def __init__(self, pattern: str):
        self.pattern = pattern
        self.tokens = tokenize(pattern, policy="lenient")
        self.result: Dict[str, str] = {}
        self.token_index = 0
        self.component_start_token_index = 0
        self.state = "init"
        self.group_depth = 0
        self.ipv6_depth = 0
        self.protocol_matches_special = False

    def parse(self) -> Dict[str, str]:
        while self.state != "done":
            if self.token_index >= len(self.tokens):
                break

            token = self.tokens[self.token_index]

            if token.type == "end":
                self._handle_end()
                if self.state == "done":
                    break
                continue

            if token.type == "open":
                self.group_depth += 1
                self.token_index += 1
                continue
            if token.type == "close":
                if self.group_depth > 0:
                    self.group_depth -= 1
                self.token_index += 1
                continue

            if self.group_depth > 0:
                self.token_index += 1
                continue

            token_increment = 1
            if self.state == "init":
                token_increment = self._handle_init()
            elif self.state == "protocol":
                token_increment = self._handle_protocol()
            elif self.state == "authority":
                token_increment = self._handle_authority()
            elif self.state == "hostname":
                token_increment = self._handle_hostname()
            elif self.state == "port":
                token_increment = self._handle_port()
            elif self.state == "pathname":
                token_increment = self._handle_pathname()
            elif self.state == "search":
                token_increment = self._handle_search()

            self.token_index += token_increment

        if "hostname" in self.result and "port" not in self.result:
            self.result["port"] = ""

        return self.result

    def _apply_pathname_search_defaults(self, next_state: str) -> None:
        if next_state in ("search", "hash"):
            if "pathname" not in self.result:
                self.result["pathname"] = "/" if self.protocol_matches_special else ""
        if next_state == "hash" and "search" not in self.result:
            self.result["search"] = ""

    def _get_component_string(self, start_idx: int, end_idx: int) -> str:
        if start_idx >= len(self.tokens) or start_idx >= end_idx:
            return ""
        start_pos = self.tokens[start_idx].index
        end_pos = (
            self.tokens[end_idx].index
            if end_idx < len(self.tokens)
            else len(self.pattern)
        )
        return self.pattern[start_pos:end_pos]

    def _is_search_prefix(self, idx: int) -> bool:
        if idx >= len(self.tokens):
            return False
        t = self.tokens[idx]
        if t.value != "?":
            return False
        if t.type in ("char", "escaped-char", "invalid-char"):
            return True
        if idx == 0:
            return True
        prev = self.tokens[idx - 1]
        if prev.type in ("name", "regexp", "close", "asterisk"):
            return False
        return True

    def _is_hash_prefix(self, idx: int) -> bool:
        if idx >= len(self.tokens):
            return False
        t = self.tokens[idx]
        return t.value == "#" and t.type in ("char", "escaped-char", "invalid-char")

    def _is_pathname_start(self, idx: int) -> bool:
        if idx >= len(self.tokens):
            return False
        t = self.tokens[idx]
        return t.value == "/" and t.type in ("char", "escaped-char", "invalid-char")

    def _is_non_special(self, idx: int, value: str) -> bool:
        if idx >= len(self.tokens):
            return False
        t = self.tokens[idx]
        if t.value != value:
            return False
        return t.type in ("char", "escaped-char", "invalid-char")

    def _handle_end(self) -> None:
        if self.state == "init":
            if self._is_hash_prefix(self.component_start_token_index):
                self.state = "hash"
                self.token_index = self.component_start_token_index + 1
                self.component_start_token_index = self.token_index
                return
            if self._is_search_prefix(self.component_start_token_index):
                self.state = "search"
                self.token_index = self.component_start_token_index + 1
                self.component_start_token_index = self.token_index
                return
            self.state = "pathname"
            self.token_index = self.component_start_token_index
            return
        if self.state == "authority":
            self.state = "hostname"
            self.token_index = self.component_start_token_index
            return
        if self.state not in ("init", "authority", "done"):
            self.result[self.state] = self._get_component_string(
                self.component_start_token_index, self.token_index
            )
        self.state = "done"

    def _handle_init(self) -> int:
        if self._is_non_special(self.token_index, ":"):
            self.state = "protocol"
            self.token_index = self.component_start_token_index
            return 0
        return 1

    def _handle_protocol(self) -> int:
        if self._is_non_special(self.token_index, ":"):
            protocol_val = self._get_component_string(
                self.component_start_token_index, self.token_index
            )
            self.result["protocol"] = protocol_val

            self.protocol_matches_special = _is_special_scheme_pattern(
                protocol_val, raise_on_error=True
            )
            is_special = self.protocol_matches_special

            if (
                self.token_index + 2 < len(self.tokens)
                and self.tokens[self.token_index + 1].value == "/"
                and self.tokens[self.token_index + 2].value == "/"
            ):
                self.state = "authority"
                self.token_index += 3
                self.component_start_token_index = self.token_index
            elif is_special:
                self.state = "authority"
                self.token_index += 1
                self.component_start_token_index = self.token_index
            else:
                self.state = "pathname"
                self.token_index += 1
                self.component_start_token_index = self.token_index
            return 0
        return 1

    def _handle_authority(self) -> int:
        if self._is_non_special(self.token_index, "@"):
            pass_token_idx = -1
            temp_depth = 0
            for j in range(self.component_start_token_index, self.token_index):
                t = self.tokens[j]
                if t.type == "open":
                    temp_depth += 1
                elif t.type == "close":
                    if temp_depth > 0:
                        temp_depth -= 1
                elif (
                    temp_depth == 0
                    and t.type in ("char", "escaped-char", "invalid-char")
                    and t.value == ":"
                ):
                    pass_token_idx = j
                    break

            if pass_token_idx != -1:
                self.result["username"] = self._get_component_string(
                    self.component_start_token_index, pass_token_idx
                )
                self.result["password"] = self._get_component_string(
                    pass_token_idx + 1, self.token_index
                )
            else:
                self.result["username"] = self._get_component_string(
                    self.component_start_token_index, self.token_index
                )

            self.state = "hostname"
            self.token_index += 1
            self.component_start_token_index = self.token_index
            return 0
        elif (
            self._is_pathname_start(self.token_index)
            or self._is_search_prefix(self.token_index)
            or self._is_hash_prefix(self.token_index)
        ):
            self.state = "hostname"
            self.token_index = self.component_start_token_index
            return 0
        return 1

    def _handle_hostname(self) -> int:
        if self._is_non_special(self.token_index, "["):
            self.ipv6_depth += 1
        elif self._is_non_special(self.token_index, "]"):
            if self.ipv6_depth > 0:
                self.ipv6_depth -= 1

        if self._is_non_special(self.token_index, ":") and self.ipv6_depth == 0:
            self.result["hostname"] = self._get_component_string(
                self.component_start_token_index, self.token_index
            )
            self.state = "port"
            self.token_index += 1
            self.component_start_token_index = self.token_index
            return 0
        elif self._is_pathname_start(self.token_index) and self.ipv6_depth == 0:
            self.result["hostname"] = self._get_component_string(
                self.component_start_token_index, self.token_index
            )
            self.state = "pathname"
            self.component_start_token_index = self.token_index
            return 0
        elif self._is_search_prefix(self.token_index):
            self.result["hostname"] = self._get_component_string(
                self.component_start_token_index, self.token_index
            )
            self._apply_pathname_search_defaults("search")
            self.state = "search"
            self.token_index += 1
            self.component_start_token_index = self.token_index
            return 0
        elif self._is_hash_prefix(self.token_index):
            self.result["hostname"] = self._get_component_string(
                self.component_start_token_index, self.token_index
            )
            self._apply_pathname_search_defaults("hash")
            self.state = "hash"
            self.token_index += 1
            self.component_start_token_index = self.token_index
            return 0
        return 1

    def _handle_port(self) -> int:
        if self._is_pathname_start(self.token_index):
            self.result["port"] = self._get_component_string(
                self.component_start_token_index, self.token_index
            )
            self.state = "pathname"
            self.component_start_token_index = self.token_index
            return 0
        elif self._is_search_prefix(self.token_index):
            self.result["port"] = self._get_component_string(
                self.component_start_token_index, self.token_index
            )
            self._apply_pathname_search_defaults("search")
            self.state = "search"
            self.token_index += 1
            self.component_start_token_index = self.token_index
            return 0
        elif self._is_hash_prefix(self.token_index):
            self.result["port"] = self._get_component_string(
                self.component_start_token_index, self.token_index
            )
            self._apply_pathname_search_defaults("hash")
            self.state = "hash"
            self.token_index += 1
            self.component_start_token_index = self.token_index
            return 0
        return 1

    def _handle_pathname(self) -> int:
        if self._is_search_prefix(self.token_index):
            self.result["pathname"] = self._get_component_string(
                self.component_start_token_index, self.token_index
            )
            self.state = "search"
            self.token_index += 1
            self.component_start_token_index = self.token_index
            return 0
        elif self._is_hash_prefix(self.token_index):
            self.result["pathname"] = self._get_component_string(
                self.component_start_token_index, self.token_index
            )
            self._apply_pathname_search_defaults("hash")
            self.state = "hash"
            self.token_index += 1
            self.component_start_token_index = self.token_index
            return 0
        return 1

    def _handle_search(self) -> int:
        if self._is_hash_prefix(self.token_index):
            self.result["search"] = self._get_component_string(
                self.component_start_token_index, self.token_index
            )
            self.state = "hash"
            self.token_index += 1
            self.component_start_token_index = self.token_index
            return 0
        return 1


def _parse_pattern_string(pattern: str) -> Dict[str, str]:
    return URLStringParser(pattern).parse()
