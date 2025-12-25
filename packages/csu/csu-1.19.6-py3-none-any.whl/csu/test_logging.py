from csu.logging import fa_append_repr


def test_fa_append_repr():
    a = []
    b = []
    assert fa_append_repr(a, b, "123456", 3) is None
    assert a == ["%s\n   ... %s more characters"]
    assert b == ["'12", 5]
