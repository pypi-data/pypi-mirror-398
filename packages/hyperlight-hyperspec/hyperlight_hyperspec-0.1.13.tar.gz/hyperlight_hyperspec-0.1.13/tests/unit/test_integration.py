import datetime
import sys

import pytest

import hyperspec


@pytest.fixture(params=["json", "msgpack"])
def proto(request):
    if request.param == "json":
        return hyperspec.json
    elif request.param == "msgpack":
        return hyperspec.msgpack


def test_decode_naive_datetime(proto):
    """See https://github.com/jcrist/hyperspec/issues/408"""
    dt = datetime.datetime(2001, 2, 3, 4, 5, 6, 7)
    msg = proto.encode(dt)

    start = sys.getrefcount(None)
    for _ in range(1000):
        proto.decode(msg, type=datetime.datetime)
    end = sys.getrefcount(None)
    assert start == end


def test_decode_naive_time(proto):
    """See https://github.com/jcrist/hyperspec/issues/408"""
    dt = datetime.time(12, 20)
    msg = proto.encode(dt)

    start = sys.getrefcount(None)
    for _ in range(1000):
        proto.decode(msg, type=datetime.time)
    end = sys.getrefcount(None)
    assert start == end
