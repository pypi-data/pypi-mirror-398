import re
from collections import OrderedDict
from typing import Any, Dict, Optional, Tuple, Union

from .canonicalize import (
    _canonicalize_component_cached as _canonicalize_component,
)
from .canonicalize import (
    _is_ipv6_hostname,
    _strip_control_whitespace,
    _validate_protocol_literal,
)
from .compiler import compile_tokens_to_regex
from .constants import _COMPONENTS, SPECIAL_SCHEMES
from .construct import (
    _inherit_components,
    _inherit_dict_base_components,
    _parse_base_url,
    _protocol_context,
    _resolve_relative_pathname,
)
from .match import (
    _build_groups,
    _build_url_components,
    _canonicalize_url_components,
    _parse_input_url_string,
)
from .normalizer import merge_adjacent_text
from .parser import tokenize
from .patterns import (
    _literal_from_tokens,
    _normalize_hostname_escapes,
    _parse_options_for_component,
    _parse_pattern_string,
    _parse_pattern_to_parts,
    _parts_to_pattern,
    _validate_no_nested_groups,
    _validate_port_pattern,
)
from .types import Modifier, Part, PartType

_COMPILED_CACHE_MAX_SIZE = 1024
CacheKey = Tuple[object, Optional[str], Tuple[Tuple[str, object], ...]]
_COMPILED_PATTERN_CACHE: "OrderedDict[CacheKey, Dict[str, object]]" = OrderedDict()


def _normalize_pattern_cache_key(
    pattern: Optional[Union[str, Dict[str, str]]],
    base_url: Optional[str],
    options: Optional[Dict[str, object]],
) -> CacheKey:
    if pattern is None or pattern == {}:
        pattern_key = ("empty", None)
        base_url = None
    elif isinstance(pattern, dict):
        pattern_key = ("dict", tuple(sorted(pattern.items())))
    else:
        pattern_key = ("str", pattern)

    options_key: Tuple[Tuple[str, object], ...] = ()
    if options:
        options_key = tuple(sorted(options.items()))

    return (pattern_key, base_url, options_key)


def _get_cached_compiled(cache_key: CacheKey) -> Optional[Dict[str, object]]:
    compiled = _COMPILED_PATTERN_CACHE.get(cache_key)
    if compiled is None:
        return None
    _COMPILED_PATTERN_CACHE.move_to_end(cache_key)
    return compiled


def _store_cached_compiled(cache_key: CacheKey, compiled: Dict[str, object]) -> None:
    _COMPILED_PATTERN_CACHE[cache_key] = compiled
    _COMPILED_PATTERN_CACHE.move_to_end(cache_key)
    if len(_COMPILED_PATTERN_CACHE) > _COMPILED_CACHE_MAX_SIZE:
        _COMPILED_PATTERN_CACHE.popitem(last=False)


class URLPattern:
    """
    URLPattern provides pattern matching for URLs following the WHATWG URL Pattern Standard.

    Examples:
        >>> pattern = URLPattern("/users/:id")
        >>> result = pattern.exec("https://example.com/users/123")
        >>> result['pathname']['groups']['id']
        '123'

        >>> pattern = URLPattern("/posts/*")
        >>> pattern.test("https://example.com/posts/2024/hello")
        True
    """

    def __init__(
        self,
        pattern: Optional[Union[str, Dict[str, str]]] = None,
        base_url: Optional[str] = None,
        options: Optional[Dict[str, object]] = None,
    ) -> None:
        """
        Initialize a URLPattern.

        Args:
            pattern: Pattern string or dict defining the URL pattern.
                    Examples: "/users/:id", "https://*.example.com/*"
                    If None or empty, creates a wildcard pattern matching all URLs.
            base_url: Optional base URL for resolving relative patterns.
                     Example: "https://example.com"
            options: Optional dict with configuration.
                    Supported keys:
                    - ignoreCase (bool): Enable case-insensitive matching

        Raises:
            TypeError: If pattern or base_url have invalid types
        """
        if options is None and isinstance(base_url, dict):
            options = base_url
            base_url = None

        self.pattern = pattern
        self.base_url = base_url
        self.options = options or {}
        self._has_regexp_groups = False

        if pattern is not None and not isinstance(pattern, (str, dict)):
            raise TypeError(
                f"Pattern must be string or dict, got {type(pattern).__name__}"
            )

        if base_url is not None and not isinstance(base_url, str):
            raise TypeError(f"Base URL must be string, got {type(base_url).__name__}")
        if base_url == "":
            raise TypeError("Base URL must not be empty")

        self._compiled_components = {}
        self._pattern_components = set()

        cache_key = _normalize_pattern_cache_key(pattern, base_url, self.options)
        cached = _get_cached_compiled(cache_key)
        if cached is not None:
            self._compiled_components = cached["compiled_components"]
            self._pattern_components = set(cached["pattern_components"])
            self._has_regexp_groups = cached["has_regexp_groups"]
            return

        if pattern is None or pattern == {}:
            self._compile_empty_pattern()
        elif isinstance(pattern, dict):
            self._compile_dict_pattern(pattern, base_url)
        else:
            self._compile_pattern(pattern, base_url)

        _store_cached_compiled(
            cache_key,
            {
                "compiled_components": self._compiled_components,
                "pattern_components": set(self._pattern_components),
                "has_regexp_groups": self._has_regexp_groups,
            },
        )

    def _compile_components(
        self,
        pattern_components: Dict[str, str],
        is_special_protocol: bool,
        protocol: Optional[str],
        opaque_defaults: bool = False,
    ) -> None:
        """Unified compilation logic for components."""
        flags = re.IGNORECASE if self.options.get("ignoreCase") else 0

        for component_name in _COMPONENTS:
            component_pattern = _determine_default_pattern(
                component_name,
                pattern_components.get(component_name),
                opaque_defaults,
            )
            component_pattern = _strip_delimiters(component_name, component_pattern)
            if component_name == "port":
                component_pattern = _normalize_default_port(component_pattern, protocol)
            component_pattern = _apply_empty_defaults(
                component_name, component_pattern, is_special_protocol
            )

            context, delimiter = _get_component_context(
                component_name, is_special_protocol
            )
            is_ipv6_hostname_pattern = (
                component_name == "hostname" and _is_ipv6_hostname(component_pattern)
            )
            normalized_pattern = _normalize_component_pattern(
                component_name, component_pattern
            )

            tokens = tokenize(normalized_pattern)
            _validate_no_nested_groups(tokens)
            if component_name == "port":
                _validate_port_pattern(component_pattern, tokens)
            tokens = merge_adjacent_text(tokens)
            has_regexp_groups = any(token.type == "regexp" for token in tokens)

            if component_name == "protocol":
                literal = _literal_from_tokens(tokens)
                if literal is not None:
                    _validate_protocol_literal(literal)

            for i, token in enumerate(tokens):
                if token.type not in ("char", "escaped-char"):
                    continue
                if component_name == "port":
                    continue

                proto_arg = protocol
                if component_name == "pathname":
                    proto_arg = "http" if is_special_protocol else "data"

                try:
                    canon_val = _canonicalize_component(
                        token.value,
                        component_name,
                        proto_arg,
                        is_ipv6_hostname_pattern,
                        for_pattern=True,
                    )
                    tokens[i] = token._replace(value=canon_val)
                except UnicodeEncodeError:
                    raise TypeError(f"Invalid character in {component_name} pattern")

            regex, groups = compile_tokens_to_regex(
                tokens, context=context, delimiter=delimiter, validate=False
            )

            if has_regexp_groups:
                try:
                    re.compile(f"^{regex}$", flags)
                except re.error as e:
                    raise TypeError(f"Generated invalid regex: {regex}\nError: {e}")

            self._compiled_components[component_name] = {
                "regex": None,
                "regex_source": regex,
                "flags": flags,
                "groups": groups,
                "pattern": component_pattern,
                "has_regexp_groups": has_regexp_groups,
            }
            if has_regexp_groups:
                self._has_regexp_groups = True

    def _compile_dict_pattern(
        self, pattern: Dict[str, str], base_url: Optional[str]
    ) -> None:
        """Compile a dict-based pattern into regex components."""
        input_dict = pattern.copy()

        if "baseURL" in input_dict:
            if base_url is not None:
                raise TypeError(
                    "Cannot provide both a dictionary pattern and a baseURL argument"
                )
            base_url = input_dict.pop("baseURL")
            if base_url == "":
                raise TypeError("Base URL must not be empty")
        elif base_url is not None:
            raise TypeError(
                "Cannot provide baseURL argument when input is a dictionary"
            )

        pattern_components = {}
        for comp_name in _COMPONENTS:
            if comp_name in input_dict:
                val = input_dict[comp_name]
                if val is not None:
                    if not isinstance(val, str):
                        raise TypeError(
                            f"Pattern component '{comp_name}' must be a string, got {type(val).__name__}"
                        )
                    pattern_components[comp_name] = val
                    self._pattern_components.add(comp_name)

        if base_url:
            base_components = _parse_pattern_string(base_url)
            _inherit_dict_base_components(pattern_components, base_components)

            if "pathname" in pattern_components:
                try:
                    parsed_base = _parse_base_url(base_url, strict=False)
                    if parsed_base and not (
                        parsed_base.scheme and parsed_base.scheme not in SPECIAL_SCHEMES
                    ):
                        _resolve_relative_pathname(
                            pattern_components,
                            parsed_base.path or "/",
                            escape_base=False,
                        )
                except Exception:
                    pass

        _, protocol, is_special_protocol = _protocol_context(
            pattern_components, self.options
        )
        opaque_defaults = False

        self._compile_components(
            pattern_components,
            is_special_protocol,
            protocol,
            opaque_defaults=opaque_defaults,
        )

    def _compile_pattern(self, pattern: str, base_url: Optional[str]) -> None:
        """Compile a pattern string into regex components."""
        pattern_components = _parse_pattern_string(pattern)

        for comp_name in pattern_components:
            self._pattern_components.add(comp_name)

        if base_url is None and "protocol" not in pattern_components:
            raise TypeError(
                "Invalid pattern: missing protocol and no base URL provided."
            )

        if base_url:
            base_components = _parse_pattern_string(base_url)

            if pattern.startswith("?"):
                _inherit_components(
                    pattern_components,
                    base_components,
                    [
                        "protocol",
                        "hostname",
                        "port",
                        "pathname",
                        "username",
                        "password",
                    ],
                )
            elif pattern.startswith("#"):
                _inherit_components(
                    pattern_components,
                    base_components,
                    [
                        "protocol",
                        "hostname",
                        "port",
                        "pathname",
                        "username",
                        "password",
                        "search",
                    ],
                )
                if "search" not in pattern_components:
                    pattern_components["search"] = ""
            elif pattern.startswith("/"):
                _inherit_components(
                    pattern_components,
                    base_components,
                    ["protocol", "hostname", "port", "username", "password"],
                )
            else:
                if "protocol" not in pattern_components and base_components.get(
                    "protocol"
                ):
                    _inherit_components(
                        pattern_components,
                        base_components,
                        [
                            "protocol",
                            "hostname",
                            "port",
                            "username",
                            "password",
                        ],
                    )

                    if "pathname" in pattern_components:
                        _resolve_relative_pathname(
                            pattern_components,
                            base_components.get("pathname", "/"),
                            escape_base=True,
                        )

        _, protocol, is_special_protocol = _protocol_context(
            pattern_components, self.options
        )

        opaque_defaults = (
            not is_special_protocol
            and "hostname" not in pattern_components
            and "port" not in pattern_components
            and "username" not in pattern_components
            and "password" not in pattern_components
        )

        self._compile_components(
            pattern_components,
            is_special_protocol,
            protocol,
            opaque_defaults=opaque_defaults,
        )

    def _compile_empty_pattern(self) -> None:
        """
        Compile an empty pattern that matches all URLs with wildcard components.

        Empty pattern (no arguments or empty string/dict) creates a pattern that matches
        any URL, capturing all components as anonymous groups.
        """
        flags = re.IGNORECASE if self.options.get("ignoreCase") else 0
        wildcard_regex = re.compile(r"^(.*)$", flags)
        for component in _COMPONENTS:
            self._compiled_components[component] = {
                "regex": wildcard_regex,
                "regex_source": ".*",
                "flags": flags,
                "groups": ["0"],
                "pattern": "*",
            }

    def _get_component_regex(self, comp: Dict[str, object]) -> re.Pattern:
        regex = comp.get("regex")
        if regex is not None:
            return regex

        regex_source = comp.get("regex_source")
        if regex_source is None:
            raise TypeError("Missing regex source for compiled component")

        flags = comp.get("flags", 0)
        try:
            compiled = re.compile(f"^{regex_source}$", flags)
        except re.error as e:
            raise TypeError(f"Generated invalid regex: {regex_source}\nError: {e}")
        comp["regex"] = compiled
        return compiled

    def test(
        self, input_url: Union[str, Dict[str, str]], base_url: Optional[str] = None
    ) -> bool:
        """
        Test if the pattern matches the input URL.

        Args:
            input_url: URL string or dict to test.
                      Examples: "https://example.com/users/123", {"pathname": "/users/123"}
            base_url: Optional base URL for resolving relative URLs.

        Returns:
            bool: True if the pattern matches, False otherwise.

        Examples:
            >>> pattern = URLPattern("/users/:id")
            >>> pattern.test("https://example.com/users/123")
            True
            >>> pattern.test("https://example.com/posts/123")
            False
        """
        result = self.exec(input_url, base_url)
        return result is not None

    def exec(
        self,
        input_url: Optional[Union[str, Dict[str, str]]] = None,
        base_url: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Execute the pattern against the input URL and return match details.

        Args:
            input_url: URL string or dict to match. If None (no input provided),
                      returns {'inputs': [{}]} for empty patterns.
                      Examples: "https://example.com/users/123"
            base_url: Optional base URL for resolving relative URLs.

        Returns:
            dict: Match result with the following structure:
                {
                    'inputs': [<original input>],
                    'protocol': {'input': '...', 'groups': {...}},
                    'hostname': {'input': '...', 'groups': {...}},
                    'pathname': {'input': '...', 'groups': {...}},
                    'search': {'input': '...', 'groups': {...}},
                    'hash': {'input': '...', 'groups': {...}},
                    ...
                }
                Returns None if no match.

        Examples:
            >>> pattern = URLPattern("/users/:id")
            >>> result = pattern.exec("https://example.com/users/123")
            >>> result['pathname']['groups']['id']
            '123'
        """
        if input_url is None:
            input_url = {}

        original_input = input_url
        original_base_url = base_url

        if isinstance(input_url, dict):
            if base_url is not None:
                raise TypeError(
                    "Cannot provide both a dictionary input and a baseURL argument to exec()"
                )
            url_components = _build_url_components(input_url)
            if url_components is None:
                return None
        else:
            url_components = _parse_input_url_string(input_url, base_url)
            if url_components is None:
                return None

        if not isinstance(input_url, dict):
            url_components = _canonicalize_url_components(url_components)
            if url_components is None:
                return None

        if isinstance(original_input, dict):
            inputs = [original_input]
        elif original_base_url is not None:
            inputs = [original_input, original_base_url]
        else:
            inputs = [original_input]

        result = {"inputs": inputs}

        for component_name in _COMPONENTS:
            comp = self._compiled_components.get(component_name)
            if not comp:
                continue

            url_value = url_components.get(component_name, "")
            match = self._get_component_regex(comp).match(url_value)
            if not match:
                return None

            result[component_name] = {
                "input": url_value,
                "groups": _build_groups(comp["groups"], match),
            }

        return result

    def _raw_component_pattern(self, component: str) -> str:
        comp = self._compiled_components.get(component)
        if not comp:
            return ""
        return comp.get("pattern", "")

    def _component_parts_and_options(self, component: str):
        component_pattern = self._raw_component_pattern(component)
        protocol_pattern = self._raw_component_pattern("protocol")
        options = _parse_options_for_component(
            component, protocol_pattern, component_pattern
        )
        parts = _parse_pattern_to_parts(component_pattern, **options)
        return parts, options

    def _component_pattern(self, component: str) -> str:
        parts, options = self._component_parts_and_options(component)
        return _parts_to_pattern(parts, options)

    @staticmethod
    def compare_component(
        component: str, left: "URLPattern", right: "URLPattern"
    ) -> int:
        """Compare components as a polyfill-only helper (not in WHATWG spec)."""
        if component not in _COMPONENTS:
            raise TypeError(f"Invalid component '{component}'.")

        left_pattern = left._raw_component_pattern(component)
        right_pattern = right._raw_component_pattern(component)

        def compare_part(left_part, right_part):
            for attr in ("type", "modifier", "prefix", "value", "suffix"):
                left_value = getattr(left_part, attr)
                right_value = getattr(right_part, attr)
                if left_value < right_value:
                    return -1
                if left_value > right_value:
                    return 1
            return 0

        empty_fixed = Part(PartType.FIXED, "", "", "", "", Modifier.NONE)
        wildcard_only = Part(PartType.FULL_WILDCARD, "", "", "", "", Modifier.NONE)

        def compare_part_list(left_parts, right_parts):
            for i in range(min(len(left_parts), len(right_parts))):
                result = compare_part(left_parts[i], right_parts[i])
                if result:
                    return result
            if len(left_parts) == len(right_parts):
                return 0
            i = min(len(left_parts), len(right_parts))
            left_next = left_parts[i] if i < len(left_parts) else empty_fixed
            right_next = right_parts[i] if i < len(right_parts) else empty_fixed
            return compare_part(left_next, right_next)

        if not left_pattern and not right_pattern:
            return 0

        left_parts, _ = left._component_parts_and_options(component)
        right_parts, _ = right._component_parts_and_options(component)

        if left_pattern and not right_pattern:
            return compare_part_list(left_parts, [wildcard_only])
        if not left_pattern and right_pattern:
            return compare_part_list([wildcard_only], right_parts)
        return compare_part_list(left_parts, right_parts)

    def generate(self, component: str, groups: Dict[str, object]) -> str:
        if component not in _COMPONENTS:
            raise TypeError(f"Invalid component '{component}'.")
        if not isinstance(groups, dict):
            raise TypeError("Groups must be a dictionary")

        parts, options = self._component_parts_and_options(component)
        delimiter = options["delimiter"]
        encode_part = options["encode_part"]
        result = ""

        for part in parts:
            if part.type == PartType.FIXED:
                if part.modifier != Modifier.NONE:
                    raise TypeError("Cannot generate from modified fixed text")
                result += part.value
                continue

            if part.modifier != Modifier.NONE:
                raise TypeError("Cannot generate from modified groups")

            if part.type in (PartType.REGEX, PartType.FULL_WILDCARD):
                raise TypeError("Cannot generate from regex or wildcard groups")

            name = part.name
            if name not in groups:
                raise TypeError(f"Missing group '{name}'.")

            value = groups[name]
            if not isinstance(value, str):
                value = str(value)

            if (
                part.type == PartType.SEGMENT_WILDCARD
                and delimiter
                and delimiter in value
            ):
                raise TypeError("Segment value contains a delimiter")

            encoded = encode_part(value) if encode_part else value
            result += f"{part.prefix}{encoded}{part.suffix}"

        return result

    @property
    def protocol(self):
        """Get the protocol component pattern string."""
        return self._component_pattern("protocol")

    @property
    def username(self):
        """Get the username component pattern string."""
        return self._component_pattern("username")

    @property
    def password(self):
        """Get the password component pattern string."""
        return self._component_pattern("password")

    @property
    def hostname(self):
        """Get the hostname component pattern string."""
        return self._component_pattern("hostname")

    @property
    def port(self):
        """Get the port component pattern string."""
        return self._component_pattern("port")

    @property
    def pathname(self):
        """Get the pathname component pattern string."""
        return self._component_pattern("pathname")

    @property
    def search(self):
        """Get the search component pattern string."""
        return self._component_pattern("search")

    @property
    def hash(self):
        """Get the hash component pattern string."""
        return self._component_pattern("hash")

    @property
    def hasRegExpGroups(self):
        """Check if pattern contains regexp groups."""
        return self._has_regexp_groups


def _determine_default_pattern(
    component_name: str, component_pattern: Optional[str], opaque_defaults: bool
) -> str:
    """Determine the default pattern for a component."""
    if component_pattern is not None:
        return component_pattern
    if opaque_defaults and component_name in ("hostname", "port", "pathname"):
        return ""
    return "*"


def _strip_delimiters(component_name: str, component_pattern: str) -> str:
    """Strip standard delimiters from component patterns."""
    if component_name == "protocol" and component_pattern.endswith(":"):
        return component_pattern[:-1]
    if component_name == "search" and component_pattern.startswith("?"):
        return component_pattern[1:]
    if component_name == "hash" and component_pattern.startswith("#"):
        return component_pattern[1:]
    return component_pattern


def _normalize_default_port(component_pattern: str, protocol: Optional[str]) -> str:
    """Normalize default ports to empty strings."""
    if not component_pattern or not protocol:
        return component_pattern
    if protocol not in SPECIAL_SCHEMES:
        return component_pattern
    default = SPECIAL_SCHEMES[protocol]
    cleaned = _strip_control_whitespace(component_pattern)
    if cleaned.isdigit() and default is not None:
        try:
            if int(cleaned) == default:
                return ""
        except ValueError:
            pass
    return component_pattern


def _apply_empty_defaults(
    component_name: str, component_pattern: str, is_special_protocol: bool
) -> str:
    """Apply default values for empty components."""
    if component_pattern == "" and component_name == "pathname" and is_special_protocol:
        return "/"
    return component_pattern


def _get_component_context(component_name: str, is_special_protocol: bool):
    """Return component context and delimiter."""
    if component_name == "pathname":
        return component_name, "/" if is_special_protocol else ""
    if component_name == "hostname":
        return component_name, "."
    return component_name, None


def _normalize_component_pattern(component_name: str, component_pattern: str) -> str:
    """Normalize specific component patterns."""
    if component_name == "hostname":
        return _normalize_hostname_escapes(component_pattern)
    return component_pattern
