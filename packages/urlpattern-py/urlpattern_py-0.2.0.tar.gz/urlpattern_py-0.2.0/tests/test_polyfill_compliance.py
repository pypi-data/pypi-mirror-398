import copy
import json
import os
from urllib.parse import urlparse

import pytest
from urlpattern import URLPattern

COMPONENTS = [
    "protocol",
    "username",
    "password",
    "hostname",
    "port",
    "pathname",
    "search",
    "hash",
]

EARLIER_COMPONENTS = {
    "protocol": [],
    "hostname": ["protocol"],
    "port": ["protocol", "hostname"],
    "username": [],
    "password": [],
    "pathname": ["protocol", "hostname", "port"],
    "search": ["protocol", "hostname", "port", "pathname"],
    "hash": ["protocol", "hostname", "port", "pathname", "search"],
}


def _load_test_data():
    filepath = os.path.join(
        os.path.dirname(__file__),
        "resources",
        "polyfill",
        "urlpatterntestdata.json",
    )
    with open(filepath, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_wpt_data():
    filepath = os.path.join(
        os.path.dirname(__file__), "resources", "urlpatterntestdata.json"
    )
    with open(filepath, "r", encoding="utf-8") as handle:
        return json.load(handle)


TEST_DATA = _load_test_data()
CASE_IDS = [f"polyfill-case-{i}" for i in range(len(TEST_DATA))]
WPT_DATA = _load_wpt_data()


def _entry_signature(entry):
    payload = {
        "pattern": entry.get("pattern", []),
        "inputs": entry.get("inputs", []),
        "exactly_empty_components": entry.get("exactly_empty_components", []),
    }
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)


WPT_BY_SIGNATURE = {_entry_signature(entry): entry for entry in WPT_DATA}
WPT_BY_PATTERN = {}
for entry in WPT_DATA:
    pattern_key = json.dumps(
        {"pattern": entry.get("pattern", [])}, sort_keys=True, ensure_ascii=False
    )
    WPT_BY_PATTERN.setdefault(pattern_key, []).append(entry)


def _base_url_components(entry):
    pattern = entry.get("pattern", [])
    base_url = None
    if pattern and isinstance(pattern[0], dict) and pattern[0].get("baseURL"):
        base_url = pattern[0]["baseURL"]
    elif len(pattern) > 1 and isinstance(pattern[1], str):
        base_url = pattern[1]

    if not base_url:
        return None

    parsed = urlparse(base_url)
    hostname = parsed.hostname or ""
    if hostname and ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"

    return {
        "protocol": parsed.scheme,
        "username": parsed.username or "",
        "password": parsed.password or "",
        "hostname": hostname,
        "port": str(parsed.port) if parsed.port is not None else "",
        "pathname": parsed.path or "",
        "search": parsed.query or "",
        "hash": parsed.fragment or "",
    }


def _expected_pattern_component(entry, component, base_components):
    expected_obj = entry.get("expected_obj") or {}
    if component in expected_obj:
        return expected_obj[component]

    pattern = entry.get("pattern", [])
    exactly_empty = entry.get("exactly_empty_components") or []
    if component in exactly_empty:
        return ""

    first = pattern[0] if pattern else None
    if isinstance(first, dict) and first.get(component):
        return first[component]

    if isinstance(first, dict) and any(
        earlier in first for earlier in EARLIER_COMPONENTS[component]
    ):
        return "*"

    if base_components and component not in ("username", "password"):
        return base_components.get(component, "")

    return "*"


def _normalize_expected_match(entry):
    expected_match = entry.get("expected_match")
    if expected_match == "error":
        return "error"

    if not isinstance(expected_match, dict):
        return expected_match

    expected = copy.deepcopy(expected_match)
    if "inputs" not in expected:
        expected["inputs"] = entry.get("inputs", [])

    exactly_empty = entry.get("exactly_empty_components") or []
    for component in COMPONENTS:
        component_expected = expected.get(component)
        if not component_expected:
            component_expected = {"input": "", "groups": {}}
            if component not in exactly_empty:
                component_expected["groups"]["0"] = ""
            expected[component] = component_expected

        groups = component_expected.get("groups", {})
        for key, value in list(groups.items()):
            if value is None:
                groups[key] = None
        component_expected["groups"] = groups

    return expected


def _assert_inputs_match(actual, expected):
    assert "inputs" in actual
    assert len(actual["inputs"]) == len(expected)
    for actual_input, expected_input in zip(actual["inputs"], expected):
        if isinstance(actual_input, str):
            assert actual_input == expected_input
            continue
        for component in COMPONENTS:
            assert actual_input.get(component) == expected_input.get(component)


@pytest.mark.parametrize("entry", TEST_DATA, ids=CASE_IDS)
def test_polyfill_compliance(entry):
    signature = _entry_signature(entry)
    wpt_entry = WPT_BY_SIGNATURE.get(signature)
    if wpt_entry is not None:
        entry = wpt_entry
    else:
        pattern_key = json.dumps(
            {"pattern": entry.get("pattern", [])},
            sort_keys=True,
            ensure_ascii=False,
        )
        wpt_candidates = WPT_BY_PATTERN.get(pattern_key, [])
        if wpt_candidates:
            polyfill_expected_obj = entry.get("expected_obj")
            if polyfill_expected_obj == "error":
                if any(
                    candidate.get("expected_obj") != "error"
                    for candidate in wpt_candidates
                ):
                    pytest.skip(
                        "Polyfill expectation diverges from WPT for this pattern."
                    )
    pattern_args = entry.get("pattern", [])
    inputs = entry.get("inputs", [])
    expected_obj = entry.get("expected_obj")

    if expected_obj == "error":
        with pytest.raises((TypeError, ValueError)):
            URLPattern(*pattern_args)
        return

    pattern = URLPattern(*pattern_args)
    base_components = _base_url_components(entry)

    for component in COMPONENTS:
        expected = _expected_pattern_component(entry, component, base_components)
        assert getattr(pattern, component) == expected

    expected_match = _normalize_expected_match(entry)

    if expected_match == "error":
        if inputs:
            with pytest.raises((TypeError, ValueError)):
                pattern.test(*inputs)
            with pytest.raises((TypeError, ValueError)):
                pattern.exec(*inputs)
        else:
            with pytest.raises((TypeError, ValueError)):
                pattern.exec()
            with pytest.raises(TypeError):
                pattern.test()
        return

    if inputs:
        assert pattern.test(*inputs) == bool(expected_match)

    exec_result = pattern.exec(*inputs) if inputs else pattern.exec()

    if not expected_match or not isinstance(expected_match, dict):
        assert exec_result == expected_match
        return

    assert exec_result is not None
    _assert_inputs_match(exec_result, expected_match["inputs"])

    for component in COMPONENTS:
        assert exec_result[component] == expected_match[component]
