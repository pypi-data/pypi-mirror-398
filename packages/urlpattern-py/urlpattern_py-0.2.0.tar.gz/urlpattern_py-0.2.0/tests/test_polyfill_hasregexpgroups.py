from urlpattern import URLPattern


def test_polyfill_has_regexp_groups():
    assert URLPattern({}).hasRegExpGroups is False

    components = [
        "protocol",
        "username",
        "password",
        "hostname",
        "port",
        "pathname",
        "search",
        "hash",
    ]

    for component in components:
        assert URLPattern({component: "*"}).hasRegExpGroups is False
        assert URLPattern({component: ":foo"}).hasRegExpGroups is False
        assert URLPattern({component: ":foo?"}).hasRegExpGroups is False
        assert URLPattern({component: ":foo(hi)"}).hasRegExpGroups is True
        assert URLPattern({component: "(hi)"}).hasRegExpGroups is True
        if component not in ("protocol", "port"):
            assert URLPattern({component: "a-{:hello}-z-*-a"}).hasRegExpGroups is False
            assert URLPattern({component: "a-(hi)-z-(lo)-a"}).hasRegExpGroups is True

    assert URLPattern({"pathname": "/a/:foo/:baz?/b/*"}).hasRegExpGroups is False
    assert URLPattern({"pathname": "/a/:foo/:baz([a-z]+)?/b/*"}).hasRegExpGroups is True
