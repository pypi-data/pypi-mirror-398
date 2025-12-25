import re
import urllib.parse
from functools import lru_cache
from urllib.parse import urlparse

from .constants import _CONTROL_WHITESPACE_STRIP, SPECIAL_SCHEMES


def _quote_component(value: str, safe: str, replace_surrogates: bool = False) -> str:
    """Percent-encode a URL component with a configurable safe set."""
    if value == "":
        return value
    if replace_surrogates:
        value = _replace_surrogates(value)
    return urllib.parse.quote(value, safe=safe)


def _encode_component(value: str, safe: str, replace_surrogates: bool = False) -> str:
    """Encode a URL component using consistent percent-encoding rules."""
    return _quote_component(value, safe=safe, replace_surrogates=replace_surrogates)


def _replace_surrogates(value: str) -> str:
    """Replace surrogate code points with the Unicode replacement char."""
    return "".join("\ufffd" if 0xD800 <= ord(ch) <= 0xDFFF else ch for ch in value)


def _strip_control_whitespace(value: str) -> str:
    """Remove ASCII tab/newline/carriage returns per URL parsing rules."""
    return value.translate(_CONTROL_WHITESPACE_STRIP)


def _port_prefix_starts_with_digit(value: str) -> bool:
    """Return True if the port value is empty or starts with a digit."""
    if not value:
        return True
    cleaned = _strip_control_whitespace(value)
    if not cleaned:
        return True
    return cleaned[0].isdigit()


def _validate_protocol_literal(literal: str) -> None:
    """Raise TypeError for invalid literal protocol values."""
    if literal and not re.fullmatch(r"[A-Za-z][A-Za-z0-9+.-]*", literal):
        raise TypeError("Invalid protocol")


def _is_ipv6_hostname(value: str) -> bool:
    """Check if a hostname pattern represents an IPv6 address per spec."""
    return value.startswith("[") or value.startswith("{[") or value.startswith("\\[")


def _has_surrogates(value: str) -> bool:
    """Check whether a string contains surrogate code points."""
    return any(0xD800 <= ord(char) <= 0xDFFF for char in value)


def _remove_dot_segments(path: str) -> str:
    """Remove dot segments per RFC 3986 while preserving empty segments."""
    output = ""
    while path:
        if path.startswith("../"):
            path = path[3:]
            continue
        if path.startswith("./"):
            path = path[2:]
            continue
        if path.startswith("/./"):
            path = "/" + path[3:]
            continue
        if path == "/.":
            path = "/"
            continue
        if path.startswith("/../"):
            path = "/" + path[4:]
            if "/" in output:
                output = output.rsplit("/", 1)[0]
            else:
                output = ""
            continue
        if path == "/..":
            path = "/"
            if "/" in output:
                output = output.rsplit("/", 1)[0]
            else:
                output = ""
            continue
        if path in (".", ".."):
            path = ""
            continue

        if path.startswith("/"):
            idx = path.find("/", 1)
            if idx == -1:
                output += path
                path = ""
            else:
                output += path[:idx]
                path = path[idx:]
            continue

        idx = path.find("/")
        if idx == -1:
            output += path
            path = ""
        else:
            output += path[:idx]
            path = path[idx:]

    return output


def _canonicalize_component(
    value: str,
    component: str,
    protocol: str = None,
    is_ipv6_context: bool = False,
    for_pattern: bool = False,
) -> str:
    """Canonicalize a URL component value according to spec."""
    if not value:
        return value

    if _has_surrogates(value):
        if for_pattern and component == "hostname":
            raise TypeError(f"Invalid character in {component} pattern")
        value = value.encode("utf-8", errors="replace").decode("utf-8")

    if component == "protocol":
        if not value:
            return value
        if for_pattern:
            if not re.fullmatch(r"[-+.A-Za-z0-9]*", value):
                raise TypeError("Invalid protocol")
            return value.lower()
        _validate_protocol_literal(value)
        try:
            test_url = f"{value}://dummy.invalid/"
            parsed = urlparse(test_url)
            if not parsed.scheme or parsed.scheme.lower() != value.lower():
                raise TypeError("Invalid protocol")
            return parsed.scheme
        except Exception:
            raise TypeError("Invalid protocol")

    if component == "hostname":
        value = _strip_control_whitespace(value)

        if is_ipv6_context:
            import string

            valid_chars = string.hexdigits + "[]:"
            result = []
            for char in value:
                if char in valid_chars:
                    result.append(char.lower())
                else:
                    raise TypeError(f"Invalid character in IPv6 hostname: {char!r}")
            return "".join(result)

        for i, char in enumerate(value):
            if char in "/?#\\":
                value = value[:i]
                break

        forbidden_host_chars = set(" #%:@[]<>^|%")
        for char in value:
            if char <= " " or char == "\x7f" or char in forbidden_host_chars:
                raise TypeError(f"Invalid character in hostname: {char!r}")

        try:
            return value.encode("idna").decode("ascii")
        except UnicodeError:
            return value.lower()

    if component == "port":
        if not value:
            return value

        # Deviation: accept leading digit prefix per WPT tests (spec would reject).
        cleaned = _strip_control_whitespace(value)
        port_digits = []
        for char in cleaned:
            if char.isdigit():
                port_digits.append(char)
            else:
                break
        port_str = "".join(port_digits)

        if not port_str:
            return ""

        try:
            port_num = int(port_str)
        except ValueError:
            return ""

        if port_num > 65535:
            raise TypeError("Port number out of range")

        if protocol and protocol in SPECIAL_SCHEMES:
            default = SPECIAL_SCHEMES[protocol]
            if default is not None and port_num == default:
                return ""

        return port_str

    if component in ("username", "password"):
        return urllib.parse.quote(value, safe="!$&'()*+,;=%")

    if component == "pathname":
        if not value:
            return value

        is_opaque = False
        if protocol:
            if protocol.lower() not in SPECIAL_SCHEMES:
                is_opaque = True

        if is_opaque:
            return value

        leading_slash = value.startswith("/")
        modified_value = value if leading_slash else f"/-{value}"
        normalized_path = _remove_dot_segments(modified_value)

        if not leading_slash:
            if normalized_path.startswith("/-"):
                normalized_path = normalized_path[2:]
            elif normalized_path.startswith("-"):
                normalized_path = normalized_path[1:]

        encoded_path = urllib.parse.quote(normalized_path, safe="/:@!$&'()*+,;=%")
        return encoded_path

    if component == "search":
        return urllib.parse.quote(value, safe="!$&'()*+,/:;=?@%{}")

    if component == "hash":
        return urllib.parse.quote(value, safe="!$&'()*+,/:;=?@%{}")

    return value


@lru_cache(maxsize=2048)
def _canonicalize_component_cached(
    value: str,
    component: str,
    protocol: str = None,
    is_ipv6_context: bool = False,
    for_pattern: bool = False,
) -> str:
    return _canonicalize_component(
        value, component, protocol, is_ipv6_context, for_pattern
    )
