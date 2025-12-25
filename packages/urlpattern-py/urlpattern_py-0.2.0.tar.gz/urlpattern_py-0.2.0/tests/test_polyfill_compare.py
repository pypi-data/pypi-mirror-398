import json
import os

import pytest
from urlpattern import URLPattern


def _load_json(filename):
    filepath = os.path.join(
        os.path.dirname(__file__), "resources", "polyfill", filename
    )
    with open(filepath, "r", encoding="utf-8") as handle:
        return json.load(handle)


COMPARE_DATA = _load_json("urlpattern-compare-test-data.json")


@pytest.mark.parametrize("entry", COMPARE_DATA)
def test_polyfill_compare_component(entry):
    left = URLPattern(entry["left"])
    right = URLPattern(entry["right"])

    expected = entry["expected"]
    assert URLPattern.compare_component(entry["component"], left, right) == expected

    reverse_expected = int(expected * -1)
    assert (
        URLPattern.compare_component(entry["component"], right, left)
        == reverse_expected
    )
    assert URLPattern.compare_component(entry["component"], left, left) == 0
    assert URLPattern.compare_component(entry["component"], right, right) == 0
