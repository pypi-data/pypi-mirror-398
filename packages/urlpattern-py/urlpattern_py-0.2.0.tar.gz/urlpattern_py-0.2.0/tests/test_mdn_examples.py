import pytest
from urlpattern import URLPattern


def test_fixed_text_and_capture_groups():
    pattern = URLPattern({"pathname": "/books"})
    assert pattern.test("https://example.com/books") is True
    assert pattern.exec("https://example.com/books")["pathname"]["groups"] == {}

    pattern = URLPattern({"pathname": "/books/:id"})
    assert pattern.test("https://example.com/books/123") is True
    assert pattern.exec("https://example.com/books/123")["pathname"]["groups"] == {
        "id": "123"
    }


def test_regex_matchers():
    pattern1 = URLPattern(r"/books/:id(\d+)", "https://example.com")
    assert pattern1.test("https://example.com/books/123") is True
    assert pattern1.test("https://example.com/books/abc") is False
    assert pattern1.test("https://example.com/books/") is False

    pattern2 = URLPattern({"pathname": r"/books/:id(\d+)"})
    assert pattern2.test("https://example.com/books/123") is True
    assert pattern2.test("https://example.com/books/abc") is False
    assert pattern2.test("https://example.com/books/") is False


def test_pathname_matching_requires_leading_slash():
    pattern1 = URLPattern({"pathname": "(b.*)"})
    assert pattern1.test("https://example.com/b") is False
    assert pattern1.test("https://example.com/ba") is False

    pattern2 = URLPattern({"pathname": "(/b)"})
    assert pattern2.test("https://example.com/b") is True
    assert pattern2.test("https://example.com/ba") is False

    pattern3 = URLPattern({"pathname": "(/b.*)"})
    assert pattern3.test("https://example.com/b") is True
    assert pattern3.test("https://example.com/ba") is True


def test_regex_anchors_are_redundant():
    pattern1 = URLPattern({"protocol": "(^https?)"})
    assert pattern1.test("https://example.com/index.html") is True

    pattern2 = URLPattern({"protocol": "(https?)"})
    assert pattern2.test("https://example.com/index.html") is True

    pattern3 = URLPattern({"pathname": "(/path$)"})
    assert pattern3.test("https://example.com/path") is True

    pattern4 = URLPattern({"pathname": "(/path)"})
    assert pattern4.test("https://example.com/path") is True

    # Hash component is matched without a leading '/', unlike pathname.
    pattern5 = URLPattern({"hash": "(hash$)"})
    assert pattern5.test("https://example.com/#hash") is True

    pattern6 = URLPattern({"hash": "(hash)"})
    assert pattern6.test("https://example.com/#hash") is True


def test_lookahead_and_lookbehind_examples():
    pattern = URLPattern({"pathname": "(/a(?=b))"})
    assert pattern.test("https://example.com/ab") is False

    pattern1 = URLPattern({"pathname": "(/a(?=b).*)"})
    assert pattern1.test("https://example.com/ab") is True
    assert pattern1.test("https://example.com/ax") is False

    pattern2 = URLPattern({"pathname": "(/a(?!b).*)"})
    assert pattern2.test("https://example.com/ab") is False
    assert pattern2.test("https://example.com/ax") is True

    pattern3 = URLPattern({"pathname": "(/.(?<=b)a)"})
    assert pattern3.test("https://example.com/ba") is True
    assert pattern3.test("https://example.com/xa") is False

    pattern4 = URLPattern({"pathname": "(/.*(?<!b)a)"})
    assert pattern4.test("https://example.com/ba") is False
    assert pattern4.test("https://example.com/xa") is True


def test_regex_matcher_limitations():
    with pytest.raises(TypeError):
        URLPattern({"pathname": "([()])"})

    URLPattern({"pathname": r"([\(\)])"})


def test_unnamed_and_named_groups():
    pattern = URLPattern(r"/books/:id(\d+)", "https://example.com")
    assert pattern.exec("https://example.com/books/123")["pathname"]["groups"] == {
        "id": "123"
    }

    pattern = URLPattern(r"/books/(\d+)", "https://example.com")
    assert pattern.exec("https://example.com/books/123")["pathname"]["groups"] == {
        "0": "123"
    }


def test_group_modifiers():
    pattern = URLPattern("/books/:id?", "https://example.com")
    assert pattern.test("https://example.com/books/123") is True
    assert pattern.test("https://example.com/books") is True
    assert pattern.test("https://example.com/books/") is False
    assert pattern.test("https://example.com/books/123/456") is False
    assert pattern.test("https://example.com/books/123/456/789") is False

    pattern = URLPattern("/books/:id+", "https://example.com")
    assert pattern.test("https://example.com/books/123") is True
    assert pattern.test("https://example.com/books") is False
    assert pattern.test("https://example.com/books/") is False
    assert pattern.test("https://example.com/books/123/456") is True
    assert pattern.test("https://example.com/books/123/456/789") is True

    pattern = URLPattern("/books/:id*", "https://example.com")
    assert pattern.test("https://example.com/books/123") is True
    assert pattern.test("https://example.com/books") is True
    assert pattern.test("https://example.com/books/") is False
    assert pattern.test("https://example.com/books/123/456") is True
    assert pattern.test("https://example.com/books/123/456/789") is True


def test_group_delimiters():
    pattern = URLPattern("/book{s}?", "https://example.com")
    assert pattern.test("https://example.com/books") is True
    assert pattern.test("https://example.com/book") is True
    assert pattern.exec("https://example.com/books")["pathname"]["groups"] == {}

    pattern = URLPattern("/book{s}", "https://example.com")
    assert pattern.pathname == "/books"
    assert pattern.test("https://example.com/books") is True
    assert pattern.test("https://example.com/book") is False

    pattern = URLPattern({"pathname": r"/blog/:id(\d+){-:title}?"})
    assert pattern.test("https://example.com/blog/123-my-blog") is True
    assert pattern.test("https://example.com/blog/123") is True
    assert pattern.test("https://example.com/blog/my-blog") is False


def test_automatic_group_prefixing():
    pattern = URLPattern("/books/:id?", "https://example.com")
    assert pattern.test("https://example.com/books/123") is True
    assert pattern.test("https://example.com/books") is True
    assert pattern.test("https://example.com/books/") is False

    pattern = URLPattern("/books/:id+", "https://example.com")
    assert pattern.test("https://example.com/books/123") is True
    assert pattern.test("https://example.com/books/123/456") is True
    assert pattern.test("https://example.com/books/123/") is False
    assert pattern.test("https://example.com/books/123/456/") is False

    pattern = URLPattern({"hash": "/books/:id?"})
    assert pattern.test("https://example.com#/books/123") is True
    assert pattern.test("https://example.com#/books") is False
    assert pattern.test("https://example.com#/books/") is True

    pattern = URLPattern({"pathname": "/books/{:id}?"})
    assert pattern.test("https://example.com/books/123") is True
    assert pattern.test("https://example.com/books") is False
    assert pattern.test("https://example.com/books/") is True


def test_wildcard_tokens():
    pattern = URLPattern("/books/*", "https://example.com")
    assert pattern.test("https://example.com/books/123") is True
    assert pattern.test("https://example.com/books") is False
    assert pattern.test("https://example.com/books/") is True
    assert pattern.test("https://example.com/books/123/456") is True

    pattern = URLPattern("/*.png", "https://example.com")
    assert pattern.test("https://example.com/image.png") is True
    assert pattern.test("https://example.com/image.png/123") is False
    assert pattern.test("https://example.com/folder/image.png") is True
    assert pattern.test("https://example.com/.png") is True


def test_trailing_slashes_not_matched_by_default():
    pattern_slash = URLPattern({"pathname": "/books/"})
    assert pattern_slash.test("https://example.com/books") is False
    assert pattern_slash.test("https://example.com/books/") is True

    pattern_no_slash = URLPattern({"pathname": "/books"})
    assert pattern_no_slash.test("https://example.com/books") is True
    assert pattern_no_slash.test("https://example.com/books/") is False

    pattern_optional_slash = URLPattern({"pathname": "/books{/}?"})
    assert pattern_optional_slash.test("https://example.com/books") is True
    assert pattern_optional_slash.test("https://example.com/books/") is True


def test_case_sensitivity():
    pattern = URLPattern("https://example.com/2022/feb/*")
    assert pattern.test("https://example.com/2022/feb/xc44rsz") is True
    assert pattern.test("https://example.com/2022/Feb/xc44rsz") is False

    pattern = URLPattern("https://example.com/2022/feb/*", {"ignoreCase": True})
    assert pattern.test("https://example.com/2022/feb/xc44rsz") is True
    assert pattern.test("https://example.com/2022/Feb/xc44rsz") is True


def test_filter_on_specific_url_component():
    pattern = URLPattern({"hostname": "{*.}?example.com"})

    assert pattern.hostname == "{*.}?example.com"
    assert pattern.protocol == "*"
    assert pattern.port == "*"
    assert pattern.username == "*"
    assert pattern.password == "*"
    assert pattern.pathname == "*"
    assert pattern.search == "*"
    assert pattern.hash == "*"

    assert pattern.test("https://example.com/foo/bar") is True
    assert pattern.test({"hostname": "cdn.example.com"}) is True
    assert pattern.test("custom-protocol://example.com/other/path?q=1") is True
    assert pattern.test("https://cdn-example.com/foo/bar") is False


def test_construct_from_full_url_string():
    pattern = URLPattern("https://cdn-*.example.com/*.jpg")
    assert pattern.protocol == "https"
    assert pattern.hostname == "cdn-*.example.com"
    assert pattern.pathname == "/*.jpg"

    assert pattern.username == "*"
    assert pattern.password == "*"
    assert pattern.search == "*"
    assert pattern.hash == "*"

    assert pattern.test("https://cdn-1234.example.com/product/assets/hero.jpg") is True
    assert (
        pattern.test("https://cdn-1234.example.com/product/assets/hero.jpg?q=1") is True
    )


def test_ambiguous_url_string_throws():
    with pytest.raises(TypeError):
        URLPattern("data:foo*")


def test_escape_characters_to_disambiguate():
    pattern = URLPattern(r"data\:foo*")
    assert pattern.protocol == "data"
    assert pattern.pathname == "foo*"
    assert pattern.username == "*"
    assert pattern.password == "*"
    assert pattern.hostname == ""
    assert pattern.port == ""
    assert pattern.search == "*"
    assert pattern.hash == "*"

    assert pattern.test("data:foobar") is True


def test_base_urls_for_test_and_exec():
    pattern = URLPattern({"hostname": "example.com", "pathname": "/foo/*"})
    assert pattern.protocol == "*"
    assert pattern.pathname == "/foo/*"
    assert pattern.username == "*"
    assert pattern.password == "*"
    assert pattern.hostname == "example.com"
    assert pattern.port == "*"
    assert pattern.search == "*"
    assert pattern.hash == "*"

    assert (
        pattern.test({"pathname": "/foo/bar", "baseURL": "https://example.com/baz"})
        is True
    )
    assert pattern.test("/foo/bar", "https://example.com/baz") is True

    with pytest.raises(TypeError):
        pattern.test({"pathname": "/foo/bar"}, "https://example.com/baz")

    result = pattern.exec("/foo/bar", "https://example.com/baz")
    assert result["pathname"]["input"] == "/foo/bar"
    assert result["pathname"]["groups"]["0"] == "bar"
    assert result["hostname"]["input"] == "example.com"


def test_base_urls_in_constructor():
    pattern1 = URLPattern({"pathname": "/foo/*", "baseURL": "https://example.com"})
    assert pattern1.protocol == "https"
    assert pattern1.hostname == "example.com"
    assert pattern1.pathname == "/foo/*"
    assert pattern1.username == "*"
    assert pattern1.password == "*"
    assert pattern1.port == ""
    assert pattern1.search == "*"
    assert pattern1.hash == "*"

    pattern2 = URLPattern("/foo/*", "https://example.com")
    assert pattern2.protocol == pattern1.protocol
    assert pattern2.hostname == pattern1.hostname
    assert pattern2.pathname == pattern1.pathname

    with pytest.raises(TypeError):
        URLPattern("/foo/*")


def test_accessing_matched_group_values():
    pattern = URLPattern({"hostname": "*.example.com"})
    result = pattern.exec({"hostname": "cdn.example.com"})
    assert result["hostname"] == {
        "groups": {"0": "cdn"},
        "input": "cdn.example.com",
    }


def test_accessing_matched_named_group_values():
    pattern = URLPattern({"pathname": "/:product/:user/:action"})
    result = pattern.exec({"pathname": "/store/wanderview/view"})

    assert result["pathname"] == {
        "groups": {"product": "store", "user": "wanderview", "action": "view"},
        "input": "/store/wanderview/view",
    }
    assert result["pathname"]["groups"]["user"] == "wanderview"


def test_regular_expression_with_unnamed_group():
    pattern = URLPattern({"pathname": "/(foo|bar)"})
    assert pattern.test({"pathname": "/foo"}) is True
    assert pattern.test({"pathname": "/bar"}) is True
    assert pattern.test({"pathname": "/baz"}) is False

    result = pattern.exec({"pathname": "/foo"})
    assert result["pathname"]["groups"]["0"] == "foo"


def test_regular_expression_with_named_group():
    pattern = URLPattern({"pathname": "/:type(foo|bar)"})
    result = pattern.exec({"pathname": "/foo"})
    assert result["pathname"]["groups"]["type"] == "foo"


def test_optional_matching_groups():
    pattern = URLPattern({"pathname": "/product/(index.html)?"})
    assert pattern.test({"pathname": "/product/index.html"}) is True
    assert pattern.test({"pathname": "/product"}) is True

    pattern2 = URLPattern({"pathname": "/product/:action?"})
    assert pattern2.test({"pathname": "/product/view"}) is True
    assert pattern2.test({"pathname": "/product"}) is True

    pattern3 = URLPattern({"pathname": "/product/*?"})
    assert pattern3.test({"pathname": "/product/wanderview/view"}) is True
    assert pattern3.test({"pathname": "/product"}) is True
    assert pattern3.test({"pathname": "/product/"}) is True


def test_repeated_matching_groups():
    pattern = URLPattern({"pathname": "/product/:action+"})
    result = pattern.exec({"pathname": "/product/do/some/thing/cool"})
    assert result["pathname"] == {
        "groups": {"action": "do/some/thing/cool"},
        "input": "/product/do/some/thing/cool",
    }

    assert pattern.test({"pathname": "/product"}) is False
    assert pattern.test({"pathname": "/product/"}) is False
    assert pattern.test({"pathname": "/product/do"}) is True
    assert pattern.test({"pathname": "/product/do/"}) is False


def test_optional_and_repeated_matching_groups():
    pattern = URLPattern({"pathname": "/product/:action*"})
    result = pattern.exec({"pathname": "/product/do/some/thing/cool"})
    assert result["pathname"] == {
        "groups": {"action": "do/some/thing/cool"},
        "input": "/product/do/some/thing/cool",
    }

    assert pattern.test({"pathname": "/product"}) is True
    assert pattern.test({"pathname": "/product/"}) is False
    assert pattern.test({"pathname": "/product/do"}) is True
    assert pattern.test({"pathname": "/product/do/"}) is False


def test_custom_prefix_or_suffix_for_modifier():
    pattern = URLPattern({"hostname": "{:subdomain.}*example.com"})
    result = pattern.exec({"hostname": "foo.bar.example.com"})

    assert pattern.test({"hostname": "example.com"}) is True
    assert pattern.test({"hostname": "foo.bar.example.com"}) is True
    assert pattern.test({"hostname": ".example.com"}) is False

    assert result["hostname"] == {
        "groups": {"subdomain": "foo.bar"},
        "input": "foo.bar.example.com",
    }


def test_optional_or_repeated_text_without_matching_group():
    pattern = URLPattern({"pathname": "/product{/}?"})
    assert pattern.test({"pathname": "/product"}) is True
    assert pattern.test({"pathname": "/product/"}) is True

    result = pattern.exec({"pathname": "/product/"})
    assert result["pathname"]["groups"] == {}


def test_multiple_components_and_features():
    pattern = URLPattern(
        {
            "protocol": "http{s}?",
            "username": ":user?",
            "password": ":pass?",
            "hostname": "{:subdomain.}*example.com",
            "pathname": "/product/:action*",
        }
    )

    result = pattern.exec("http://foo:bar@sub.example.com/product/view?q=12345")
    assert result["username"]["groups"]["user"] == "foo"
    assert result["password"]["groups"]["pass"] == "bar"
    assert result["hostname"]["groups"]["subdomain"] == "sub"
    assert result["pathname"]["groups"]["action"] == "view"
