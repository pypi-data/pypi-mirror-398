import operator
import subprocess
import sys
import textwrap
import weakref

import pytest

import hyperspec


def test_raw_noargs():
    r = hyperspec.Raw()
    assert bytes(r) == b""
    assert len(r) == 0
    assert not r


@pytest.mark.parametrize("type", [bytes, bytearray, memoryview, str])
def test_raw_constructor(type):
    msg = "test" if type is str else type(b"test")
    r = hyperspec.Raw(msg)
    assert bytes(r) == b"test"
    assert len(r) == 4
    assert r


def test_raw_constructor_errors():
    with pytest.raises(TypeError):
        hyperspec.Raw(1)

    with pytest.raises(TypeError):
        hyperspec.Raw(msg=b"test")

    with pytest.raises(TypeError):
        hyperspec.Raw(b"test", b"extra")


def test_raw_from_view():
    r = hyperspec.Raw(memoryview(b"123456")[:3])
    assert bytes(r) == b"123"
    assert len(r) == 3
    assert r


def test_raw_copy():
    r = hyperspec.Raw(b"test")
    c1 = sys.getrefcount(r)
    r2 = r.copy()
    c2 = sys.getrefcount(r)
    assert c1 + 1 == c2
    assert r2 is r

    r = hyperspec.Raw()
    assert r.copy() is r

    m = memoryview(b"test")
    ref = weakref.ref(m)
    r = hyperspec.Raw(m)
    del m
    # Raw holds a ref
    assert ref() is not None
    r2 = r.copy()
    # Actually copied
    assert r2 is not r
    assert bytes(r2) == b"test"
    # Copy doesn't accidentally release buffer
    assert ref() is not None
    del r
    # Copy doesn't hold a reference to original view
    assert ref() is None


def test_raw_copy_doesnt_leak():
    """See https://github.com/jcrist/hyperspec/pull/709"""
    script = textwrap.dedent(
        """
        import hyperspec
        import tracemalloc

        tracemalloc.start()

        raw = hyperspec.Raw(bytearray(1000))
        for _ in range(10000):
            raw.copy()

        _, peak = tracemalloc.get_traced_memory()
        print(peak)
        """
    )

    output = subprocess.check_output([sys.executable, "-c", script])
    peak = int(output.decode().strip())
    assert peak < 10_000  # should really be ~2000


def test_raw_pickle_bytes():
    orig_buffer = b"test"
    r = hyperspec.Raw(orig_buffer)
    o = r.__reduce__()
    assert o == (hyperspec.Raw, (b"test",))
    assert o[1][0] is orig_buffer


def test_raw_pickle_str():
    orig_buffer = "test"
    r = hyperspec.Raw(orig_buffer)
    o = r.__reduce__()
    assert o == (hyperspec.Raw, ("test",))
    assert o[1][0] is orig_buffer


def test_raw_pickle_view():
    r = hyperspec.Raw(memoryview(b"test")[:3])
    o = r.__reduce__()
    assert o == (hyperspec.Raw, (b"tes",))


def test_raw_comparison():
    r = hyperspec.Raw()
    assert r == r
    assert not r != r
    assert hyperspec.Raw() == hyperspec.Raw()
    assert hyperspec.Raw(b"") == hyperspec.Raw()
    assert not hyperspec.Raw(b"") == hyperspec.Raw(b"other")
    assert hyperspec.Raw(b"test") == hyperspec.Raw(memoryview(b"testy")[:4])
    assert hyperspec.Raw(b"test") != hyperspec.Raw(b"tesp")
    assert hyperspec.Raw(b"test") != hyperspec.Raw(b"")
    assert hyperspec.Raw(b"") != hyperspec.Raw(b"test")
    assert hyperspec.Raw() != 1
    assert 1 != hyperspec.Raw()

    for op in [operator.lt, operator.gt, operator.le, operator.ge]:
        with pytest.raises(TypeError):
            op(hyperspec.Raw(), hyperspec.Raw())
