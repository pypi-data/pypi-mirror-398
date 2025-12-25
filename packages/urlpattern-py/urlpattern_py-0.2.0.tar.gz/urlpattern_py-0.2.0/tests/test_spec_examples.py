import pytest
from urlpattern import URLPattern


def test_intro_example_1():
    pattern = URLPattern("https://example.com/:category/*")

    assert pattern.protocol == "https"
    assert pattern.username == "*"
    assert pattern.password == "*"
    assert pattern.hostname == "example.com"
    assert pattern.port == ""
    assert pattern.pathname == "/:category/*"
    assert pattern.search == "*"
    assert pattern.hash == "*"

    assert pattern.test("https://example.com/products/") is True
    assert pattern.test("https://example.com/blog/our-greatest-product-ever") is True

    assert pattern.test("https://example.com/") is False
    assert pattern.test("http://example.com/products/") is False
    assert (
        pattern.test("https://example.com:8443/blog/our-greatest-product-ever") is False
    )


def test_intro_example_2():
    pattern = URLPattern(
        "http{s}?://{:subdomain.}?shop.example/products/:id([0-9]+)#reviews"
    )

    assert pattern.protocol == "http{s}?"
    assert pattern.username == "*"
    assert pattern.password == "*"
    assert pattern.hostname == "{:subdomain.}?shop.example"
    assert pattern.port == ""
    assert pattern.pathname == "/products/:id([0-9]+)"
    assert pattern.search == ""
    assert pattern.hash == "reviews"

    assert pattern.test("https://shop.example/products/74205#reviews") is True
    assert (
        pattern.test("https://kathryn@voyager.shop.example/products/74656#reviews")
        is True
    )
    assert pattern.test("http://insecure.shop.example/products/1701#reviews") is True

    assert pattern.test("https://shop.example/products/2000") is False
    assert pattern.test("http://shop.example:8080/products/0#reviews") is False
    assert pattern.test("https://nx.shop.example/products/01?speed=5#reviews") is False
    assert pattern.test("https://shop.example/products/chair#reviews") is False


def test_intro_example_3():
    pattern = URLPattern("../admin/*", "https://discussion.example/forum/?page=2")

    assert pattern.protocol == "https"
    assert pattern.username == "*"
    assert pattern.password == "*"
    assert pattern.hostname == "discussion.example"
    assert pattern.port == ""
    assert pattern.pathname == "/admin/*"
    assert pattern.search == "*"
    assert pattern.hash == "*"

    assert pattern.test("https://discussion.example/admin/") is True
    assert (
        pattern.test("https://edd:librarian@discussion.example/admin/update?id=1")
        is True
    )

    assert pattern.test("https://discussion.example/forum/admin/") is False
    assert pattern.test("http://discussion.example:8080/admin/update?id=1") is False


def test_pattern_strings_examples():
    pattern = URLPattern({"pathname": "/blog/:title"})
    assert pattern.test({"pathname": "/blog/hello-world"}) is True
    assert pattern.test({"pathname": "/blog/2012/02"}) is False

    pattern = URLPattern({"pathname": r"/blog/:year(\d+)/:month(\d+)"})
    assert pattern.test({"pathname": "/blog/2012/02"}) is True

    pattern = URLPattern({"pathname": "/products/:id?"})
    assert pattern.test({"pathname": "/products"}) is True
    assert pattern.test({"pathname": "/products/2"}) is True
    assert pattern.test({"pathname": "/products/"}) is False

    URLPattern({"pathname": "/products/{:id}?"})

    pattern = URLPattern({"pathname": "/products/*"})
    assert pattern.test({"pathname": "/products/2"}) is True


@pytest.mark.parametrize(
    "pattern",
    [
        "/:foo(bar)?",
        "/",
        ":foo",
        "(bar)",
        "/:foo",
        "/(bar)",
        "/:foo?",
        "/(bar)?",
        "{a:foo(bar)b}?",
        "{:foo}?",
        "{(bar)}?",
        "{ab}?",
    ],
)
def test_parsing_examples_are_valid(pattern):
    URLPattern({"pathname": pattern})
