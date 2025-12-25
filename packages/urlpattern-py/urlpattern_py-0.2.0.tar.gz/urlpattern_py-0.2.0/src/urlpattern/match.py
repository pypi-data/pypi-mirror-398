from typing import Dict, Optional
from urllib.parse import urljoin, urlparse

from .canonicalize import (
    _canonicalize_component_cached as _canonicalize_component,
)
from .canonicalize import (
    _is_ipv6_hostname,
    _port_prefix_starts_with_digit,
)
from .constants import SPECIAL_SCHEMES
from .construct import _parse_base_url, _process_urlpattern_init


def _build_groups(group_names, match):
    """Build the groups dict, de-duplicating names with numeric suffixes."""
    groups_dict = {}
    all_groups = match.groups()
    groupdict = match.groupdict()
    for i, name in enumerate(group_names):
        if i < len(all_groups):
            value = all_groups[i]
            if name in groups_dict:
                suffix = 1
                while f"{name}_{suffix}" in groupdict:
                    suffix_val = groupdict.get(f"{name}_{suffix}")
                    if suffix_val is not None:
                        groups_dict[name] = suffix_val
                        break
                    suffix += 1
            else:
                groups_dict[name] = value
    return groups_dict


def _build_url_components(input_url: Dict[str, str]) -> Optional[Dict[str, str]]:
    """Normalize URLPatternInit input into component dict, or None on failure."""
    try:
        processed = _process_urlpattern_init(
            input_url,
            "url",
            protocol="",
            username="",
            password="",
            hostname="",
            port="",
            pathname="",
            search="",
            hash_value="",
        )
    except Exception:
        return None

    return {
        "protocol": processed.get("protocol", ""),
        "username": processed.get("username", ""),
        "password": processed.get("password", ""),
        "hostname": processed.get("hostname", ""),
        "port": processed.get("port", ""),
        "pathname": processed.get("pathname", ""),
        "search": processed.get("search", ""),
        "hash": processed.get("hash", ""),
    }


def _parse_input_url_string(
    input_url: str, base_url: Optional[str]
) -> Optional[Dict[str, str]]:
    """Parse a URL string into component dict, or None on failure."""
    try:
        if base_url:
            base_parsed = _parse_base_url(base_url, strict=False)
            if base_parsed is None:
                return None

            is_opaque_base = (
                base_parsed.scheme not in SPECIAL_SCHEMES
                and not base_url.startswith(f"{base_parsed.scheme}://")
            )
            if is_opaque_base:
                input_parsed = urlparse(input_url)
                if not input_parsed.scheme:
                    return None

            input_url = urljoin(base_url, input_url)

        temp_parsed = urlparse(input_url)
        if temp_parsed.scheme in SPECIAL_SCHEMES and not input_url.startswith(
            f"{temp_parsed.scheme}://"
        ):
            fixed_url = input_url.replace(
                f"{temp_parsed.scheme}:", f"{temp_parsed.scheme}://", 1
            )
            parsed = urlparse(fixed_url)
        else:
            parsed = urlparse(input_url)

        if not parsed.scheme and not base_url:
            if not input_url.startswith("/"):
                return None
    except Exception:
        return None

    hostname = parsed.hostname or ""
    if hostname and ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"

    pathname = parsed.path
    if not pathname and parsed.scheme in SPECIAL_SCHEMES:
        pathname = "/"

    return {
        "protocol": parsed.scheme,
        "username": parsed.username or "",
        "password": parsed.password or "",
        "hostname": hostname,
        "port": str(parsed.port) if parsed.port is not None else "",
        "pathname": pathname,
        "search": parsed.query or "",
        "hash": parsed.fragment or "",
    }


def _canonicalize_url_components(
    url_components: Dict[str, str],
) -> Optional[Dict[str, str]]:
    """Canonicalize parsed URL components, returning None if invalid."""
    protocol = url_components.get("protocol", "").lower()
    for name, value in url_components.items():
        original_value = value

        if name == "port" and value and not _port_prefix_starts_with_digit(value):
            return None

        try:
            is_ipv6_context = name == "hostname" and _is_ipv6_hostname(value)
            canonicalized = _canonicalize_component(
                value, name, protocol, is_ipv6_context
            )
        except TypeError:
            return None

        if name == "protocol" and original_value and not canonicalized:
            return None

        url_components[name] = canonicalized

    return url_components
