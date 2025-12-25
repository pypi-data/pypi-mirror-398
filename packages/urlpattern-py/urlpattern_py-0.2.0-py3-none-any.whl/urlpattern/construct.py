from typing import Dict, Optional
from urllib.parse import urlparse

from .canonicalize import (
    _canonicalize_component_cached as _canonicalize_component,
)
from .canonicalize import (
    _is_ipv6_hostname,
    _port_prefix_starts_with_digit,
)
from .constants import SPECIAL_SCHEMES
from .normalizer import escape_pattern_syntax
from .patterns import (
    _is_special_scheme_pattern,
    _literal_protocol,
)


def _is_absolute_pathname_base(value: str, allow_non_url: bool) -> bool:
    """Return True if pathname is absolute, with optional non-URL rules."""
    if not value:
        return False
    if value.startswith("/"):
        return True
    if not allow_non_url:
        return False
    if len(value) < 2:
        return False
    if value[0] == "\\" and value[1] == "/":
        return True
    if value[0] == "{" and value[1] == "/":
        return True
    return False


def _is_absolute_pathname(value: str) -> bool:
    """Check if a pathname pattern is absolute per spec."""
    return _is_absolute_pathname_base(value, allow_non_url=True)


def _is_absolute_pathname_for_type(value: str, type_: str) -> bool:
    """Check if a pathname is absolute per spec, with type awareness."""
    return _is_absolute_pathname_base(value, allow_non_url=type_ != "url")


def _process_base_url_string(value: str, type_: str) -> str:
    """Return escaped base URL fields when building patterns."""
    if type_ != "pattern":
        return value
    return escape_pattern_syntax(value)


def _serialize_base_hostname(parsed_base) -> str:
    """Serialize base hostname, preserving IPv6 brackets."""
    hostname = parsed_base.hostname or ""
    if hostname and ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"
    return hostname


def _serialize_base_path(parsed_base) -> str:
    """Serialize base path, defaulting to a root slash."""
    return parsed_base.path or "/"


def _parse_base_url(base_url: Optional[str], *, strict: bool):
    """Parse a base URL with optional strict error handling."""
    if base_url is None:
        return None
    if base_url == "":
        if strict:
            raise TypeError("Base URL must not be empty")
        return None
    parsed = urlparse(base_url)
    if not parsed.scheme:
        if strict:
            raise TypeError("Invalid base URL")
        return None
    return parsed


def _inherit_components(
    pattern_components: Dict[str, str],
    base_components: Dict[str, str],
    components: list[str],
) -> None:
    """Fill missing pattern components from base components."""
    for component in components:
        if component not in pattern_components and component in base_components:
            pattern_components[component] = escape_pattern_syntax(
                base_components[component]
            )


def _inherit_dict_base_components(
    pattern_components: Dict[str, str],
    base_components: Dict[str, str],
) -> None:
    """Apply base URL inheritance rules for dict patterns."""
    for component in (
        "protocol",
        "hostname",
        "port",
        "pathname",
        "search",
        "hash",
    ):
        if component in pattern_components:
            return
        _inherit_components(pattern_components, base_components, [component])


def _resolve_relative_pathname(
    pattern_components: Dict[str, str],
    base_path: str,
    *,
    escape_base: bool,
) -> None:
    """Resolve relative pathname against a base path."""
    pathname_pattern = pattern_components.get("pathname")
    if pathname_pattern is None:
        return
    if _is_absolute_pathname(pathname_pattern):
        return
    slash_index = base_path.rfind("/")
    if slash_index == -1:
        return
    prefix = base_path[: slash_index + 1]
    if escape_base:
        prefix = escape_pattern_syntax(prefix)
    pattern_components["pathname"] = prefix + pathname_pattern


def _protocol_context(
    pattern_components: Dict[str, str], options: Dict[str, object]
) -> tuple[str, Optional[str], bool]:
    """Return raw protocol, canonical literal protocol, and special-scheme flag."""
    raw_protocol = pattern_components.get("protocol")
    literal_protocol = _literal_protocol(raw_protocol)
    if literal_protocol:
        protocol = _canonicalize_component(literal_protocol, "protocol")
    else:
        protocol = None
    is_special_protocol = _is_special_scheme_pattern(raw_protocol, options)
    return raw_protocol, protocol, is_special_protocol


def _process_init_protocol(value: str, type_: str) -> str:
    stripped = value[:-1] if value.endswith(":") else value
    if type_ == "pattern":
        return stripped
    canonicalized = _canonicalize_component(stripped, "protocol")
    if stripped and not canonicalized:
        raise TypeError("Invalid protocol")
    return canonicalized


def _process_init_component(value: str, component: str, type_: str) -> str:
    if type_ == "pattern":
        return value
    if component == "hostname" and _is_ipv6_hostname(value):
        return _canonicalize_component(value, component, is_ipv6_context=True)
    return _canonicalize_component(value, component)


def _process_init_port(value: str, protocol_value: str, type_: str) -> str:
    if type_ == "pattern":
        return value
    if value and not _port_prefix_starts_with_digit(value):
        raise TypeError("Invalid port")
    return _canonicalize_component(value, "port", protocol_value)


def _process_init_pathname(value: str, protocol_value: str, type_: str) -> str:
    if type_ == "pattern":
        return value
    if protocol_value in SPECIAL_SCHEMES or protocol_value == "":
        return _canonicalize_component(value, "pathname", protocol_value)
    return _canonicalize_component(value, "pathname", protocol_value)


def _process_init_search(value: str, type_: str) -> str:
    stripped = value[1:] if value.startswith("?") else value
    if type_ == "pattern":
        return stripped
    return _canonicalize_component(stripped, "search")


def _process_init_hash(value: str, type_: str) -> str:
    stripped = value[1:] if value.startswith("#") else value
    if type_ == "pattern":
        return stripped
    return _canonicalize_component(stripped, "hash")


def _process_urlpattern_init(
    init: Dict[str, str],
    type_: str,
    protocol: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    hostname: Optional[str] = None,
    port: Optional[str] = None,
    pathname: Optional[str] = None,
    search: Optional[str] = None,
    hash_value: Optional[str] = None,
) -> Dict[str, str]:
    """Normalize URLPatternInit fields against a base URL and type."""
    result: Dict[str, str] = {}

    for key, value in (
        ("protocol", protocol),
        ("username", username),
        ("password", password),
        ("hostname", hostname),
        ("port", port),
        ("pathname", pathname),
        ("search", search),
        ("hash", hash_value),
    ):
        if value is not None:
            result[key] = value

    base_url = init.get("baseURL") if isinstance(init, dict) else None
    parsed_base = _parse_base_url(base_url, strict=True)

    contains = {key for key, value in init.items() if value is not None}

    if parsed_base:
        if "protocol" not in contains:
            result["protocol"] = _process_base_url_string(parsed_base.scheme, type_)

        if (
            type_ != "pattern"
            and not {"protocol", "hostname", "port", "username"} & contains
        ):
            if parsed_base.username:
                result["username"] = _process_base_url_string(
                    parsed_base.username, type_
                )

        if (
            type_ != "pattern"
            and not {"protocol", "hostname", "port", "username", "password"} & contains
        ):
            if parsed_base.password:
                result["password"] = _process_base_url_string(
                    parsed_base.password, type_
                )

        if not {"protocol", "hostname"} & contains:
            result["hostname"] = _process_base_url_string(
                _serialize_base_hostname(parsed_base), type_
            )

        if not {"protocol", "hostname", "port"} & contains:
            if parsed_base.port is None:
                result["port"] = ""
            else:
                result["port"] = str(parsed_base.port)

        if not {"protocol", "hostname", "port", "pathname"} & contains:
            result["pathname"] = _process_base_url_string(
                _serialize_base_path(parsed_base), type_
            )

        if not {"protocol", "hostname", "port", "pathname", "search"} & contains:
            if parsed_base.query:
                result["search"] = _process_base_url_string(parsed_base.query, type_)

        if (
            not {
                "protocol",
                "hostname",
                "port",
                "pathname",
                "search",
                "hash",
            }
            & contains
        ):
            if parsed_base.fragment:
                result["hash"] = _process_base_url_string(parsed_base.fragment, type_)

    if "protocol" in contains:
        result["protocol"] = _process_init_protocol(init["protocol"], type_)

    if "username" in contains:
        result["username"] = _process_init_component(
            init["username"], "username", type_
        )

    if "password" in contains:
        result["password"] = _process_init_component(
            init["password"], "password", type_
        )

    if "hostname" in contains:
        result["hostname"] = _process_init_component(
            init["hostname"], "hostname", type_
        )

    result_protocol = result.get("protocol", "")

    if "port" in contains:
        result["port"] = _process_init_port(init["port"], result_protocol, type_)

    if "pathname" in contains:
        result["pathname"] = init["pathname"]
        if parsed_base and not {"protocol", "hostname", "port"} & contains:
            if not _is_absolute_pathname_for_type(result["pathname"], type_):
                base_path = _serialize_base_path(parsed_base)
                slash_index = base_path.rfind("/")
                if slash_index != -1:
                    result["pathname"] = (
                        base_path[: slash_index + 1] + result["pathname"]
                    )
        result["pathname"] = _process_init_pathname(
            result["pathname"], result_protocol, type_
        )

    if "search" in contains:
        result["search"] = _process_init_search(init["search"], type_)

    if "hash" in contains:
        result["hash"] = _process_init_hash(init["hash"], type_)

    return result
