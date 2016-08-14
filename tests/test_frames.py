import io
import functools

import amqpframe
import amqpframe.types as at
import amqpframe.methods as am

import pytest
import hypothesis as h
import hypothesis.strategies as hs
import hypothesis.extra.datetime as hed

utf8encode = functools.partial(str.encode, encoding='utf-8')


def validate(cls):
    def inner(value):
        try:
            cls.validate(value)
            return True
        except ValueError:
            return False
    return inner


def st(strategy, cls):
    return strategy.filter(validate(cls))

bools = hs.booleans()
signed_bytes = st(hs.integers(), at.SignedByte)
unsigned_bytes = st(hs.integers(), at.UnsignedByte)
signed_shorts = st(hs.integers(), at.SignedShort)
unsigned_shorts = st(hs.integers(), at.UnsignedShort)
signed_longs = st(hs.integers(), at.SignedLong)
unsigned_longs = st(hs.integers(), at.UnsignedLong)
signed_long_longs = st(hs.integers(), at.SignedLongLong)
unsigned_long_longs = st(hs.integers(), at.UnsignedLongLong)
floats = st(hs.floats(), at.Float)
doubles = st(hs.floats(), at.Double)
decimals = st(hs.decimals(), at.Decimal)
short_strs = st(hs.text().map(utf8encode), at.ShortStr)
long_strs = st(hs.text().map(utf8encode), at.LongStr)
voids = hs.just(at.Void())
bytearrays = st(hs.binary(), at.ByteArray)
timestamps = st(hed.datetimes(), at.Timestamp)

types = (bools | signed_bytes | unsigned_bytes |
         signed_shorts | unsigned_shorts |
         signed_longs | unsigned_longs |
         signed_long_longs | floats | doubles | decimals | long_strs | voids |
         bytearrays | timestamps)

tables = hs.dictionaries(short_strs, hs.recursive(
    types, lambda c: c | hs.dictionaries(short_strs, c) | hs.lists(c)
))

arrays = hs.lists(hs.recursive(
    types, lambda c: c | hs.dictionaries(short_strs, c) | hs.lists(c)
))


type_to_strategy = {
    at.Bool: bools,
    at.SignedByte: unsigned_bytes,
    at.UnsignedByte: unsigned_bytes,
    at.SignedShort: unsigned_shorts,
    at.UnsignedShort: unsigned_shorts,
    at.SignedLong: unsigned_longs,
    at.UnsignedLong: unsigned_longs,
    at.SignedLongLong: signed_long_longs,
    at.UnsignedLongLong: unsigned_long_longs,
    at.Shortstr: short_strs,
    at.Longstr:  long_strs,
    at.Float: floats,
    at.Double: doubles,
    at.Decimal: decimals,
    at.Void: voids,
    at.Timestamp: timestamps,
    at.ByteArray: bytearrays,
    at.Table: tables,
    at.Array: arrays,
}


class TestHeaderFrame:
    DATA = b'AMQP\x00\x00\x09\x01'

    def test_from_bytestream(self):
        stream = io.BytesIO(self.DATA)
        frame = amqpframe.ProtocolHeaderFrame.from_bytestream(stream)
        assert frame.protocol_major.to_python() == 0
        assert frame.protocol_minor.to_python() == 9
        assert frame.protocol_revision.to_python() == 1

    def test_to_bytestream(self):
        frame = amqpframe.ProtocolHeaderFrame(0, 9, 1)
        stream = io.BytesIO()
        frame.to_bytestream(stream)
        assert stream.getvalue() == self.DATA


@hs.composite
def methods(draw, method_cls):
    kwargs = {}
    for name, amqptype in method_cls.field_info:
        if name.startswith('reserved'):
            continue
        if name == 'global':
            name = 'global_'

        kwargs[name] = draw(type_to_strategy[amqptype])
    return method_cls(**kwargs)


@pytest.mark.parametrize('method_cls', am.Method.__subclasses__())
def test_methods(method_cls):

    @h.given(hs.data())
    @h.settings(perform_health_check=False)
    def test_method(data):
        method = data.draw(methods(method_cls))

        stream = io.BytesIO()
        method.to_bytestream(stream)
        raw = stream.getvalue()

        stream.seek(0)
        unpacked = am.Method.from_bytestream(stream)

        assert method == unpacked
    return test_method()
