import datetime

from fbnconfig.urlfmt import Urlfmt


def test_base():
    # given a base with a slash in it
    fmt = Urlfmt("http://www.foo.com/path")
    # when it is expanded
    res = fmt.format("{base}/{p1}/p2", **{"p1": "some thing"})
    # then the base path does not get encoded and the slash is literal
    assert res == "http://www.foo.com/path/some%20thing/p2"


def test_dict():
    fmt = Urlfmt("http://www.google.com")
    res = fmt.format("{base}/{p1}/p2", **{"p1": "some thing"})
    assert res == "http://www.google.com/some%20thing/p2"


def test_keywords():
    fmt = Urlfmt("http://www.google.com")
    scope = "scope1"
    code = "a code"
    res = fmt.format("{scope}/{code}", scope=scope, code=code)
    assert res == "scope1/a%20code"


def test_slash():
    fmt = Urlfmt("http://www.google.com")
    res = fmt.format("/{p1}/p2", **{"p1": "some/thing"})
    assert res == "/some%2Fthing/p2"


def test_formatting():
    fmt = Urlfmt("http://www.google.com")
    # given a format which adds a leading +
    # when we format
    res = fmt.format("{number:+d}", **{"number": 100})
    # then the + is added and also encoded
    assert res == "%2B100"


def test_date():
    fmt = Urlfmt("http://www.google.com")
    # given a date
    # when we format
    d = datetime.datetime(2010, 7, 4, 12, 15, 58)
    res = fmt.format("{:%Y-%m-%d}", d)
    # then the date is formatted
    assert res == "2010-07-04"


def test_class():
    class Foo:
        u = Urlfmt("/api/system")

        def __init__(self):
            self.code = "foo"
            self.scope = "banjo"

        def read(self):
            return self.u.format("{base}/{scope}/{code}", scope=self.scope, code=self.code)

    f = Foo()
    res = f.read()
    assert res == "/api/system/banjo/foo"
