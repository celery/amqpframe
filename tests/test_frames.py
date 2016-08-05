import io

import amqpframe
import amqpframe.types as at
import amqpframe.methods as am

import pytest
import hypothesis as h
import hypothesis.strategies as hs
import hypothesis.extra.datetime as hed


bools = hs.booleans().map(at.Bool)
signed_bytes = hs.integers(at.SignedByte.MIN,
                           at.SignedByte.MAX).map(at.SignedByte)
unsigned_bytes = hs.integers(at.UnsignedByte.MIN,
                             at.UnsignedByte.MAX).map(at.UnsignedByte)
signed_shorts = hs.integers(at.SignedShort.MIN,
                            at.SignedShort.MAX).map(at.SignedShort)
unsigned_shorts = hs.integers(at.UnsignedShort.MIN,
                              at.UnsignedShort.MAX).map(at.UnsignedShort)
signed_longs = hs.integers(at.SignedLong.MIN,
                           at.SignedLong.MAX).map(at.SignedLong)
unsigned_longs = hs.integers(at.UnsignedLong.MIN,
                             at.UnsignedLong.MAX).map(at.UnsignedLong)
signed_long_longs = hs.integers(at.SignedLongLong.MIN,
                                at.SignedLongLong.MAX).map(at.SignedLongLong)
unsigned_long_longs = hs.integers(at.UnsignedLongLong.MIN,
                                  at.UnsignedLongLong.MAX).map(at.UnsignedLongLong)
floats = hs.floats().map(at.Float)
# XXX what to use here?
doubles = hs.floats().map(at.Double)


def _good_decimal(x):
    sign, digits, exponent = x.as_tuple()
    return (sign == 1 and
            at.UnsignedByte.MIN <= exponent <= at.UnsignedByte.MAX and
            at.UnsignedLong.MIN <= value <= at.UnsignedLong.MAX)

decimals = hs.decimals().filter(_good_decimal).map(at.Decimal)
short_strs = hs.text(max_size=at.ShortStr.MAX).\
             filter(lambda x: len(x.encode('utf-8')) <= at.ShortStr.MAX).\
             map(at.ShortStr)
long_strs = hs.text(max_size=at.LongStr.MAX). \
            filter(lambda x: len(x.encode('utf-8')) <= at.LongStr.MAX). \
            map(at.LongStr)
voids = hs.just(at.Void())
bytearrays = hs.binary().map(at.ByteArray)
timestamps = hed.datetimes(min_year=1970).map(at.Timestamp)

types = (bools | signed_bytes | unsigned_bytes |
         signed_shorts | unsigned_shorts |
         signed_longs | unsigned_longs |
         signed_long_longs | unsigned_long_longs |
         floats | doubles | decimals | long_strs | voids |
         bytearrays | timestamps)

tables = hs.dictionaries(short_strs, hs.recursive(
    types,
    lambda c: c |
              hs.dictionaries(short_strs, c).map(at.Table) |
              hs.lists(c).map(at.Array)
)).map(at.Table)

arrays = hs.lists(hs.recursive(
    types,
    lambda c: c |
              hs.dictionaries(short_strs, c).map(at.Table) |
              hs.lists(c).map(at.Array)
))


type_to_strategy = {
    at.Bool: bools,
    at.SignedByte: unsigned_bytes,
    at.UnsignedByte: unsigned_bytes,
    at.SignedShort: unsigned_shorts,
    at.UnsignedShort: unsigned_shorts,
    at.SignedLong: unsigned_longs,
    at.UnsignedLong: unsigned_longs,
    at.SignedLongLong: unsigned_long_longs,
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
        assert frame.protocol_major == 0
        assert frame.protocol_minor == 9
        assert frame.protocol_revision == 1

    def test_to_bytestream(self):
        frame = amqpframe.ProtocolHeaderFrame(0, 9, 1)
        stream = io.BytesIO()
        frame.to_bytestream(stream)
        assert stream.getvalue() == self.DATA


@pytest.mark.parametrize('method_cls', am.Method.__subclasses__())
def test_methods(method_cls):

    @hs.composite
    def methods(draw):
        kwargs = {}
        for name, amqptype in method_cls.field_info:
            if name.startswith('reserved'):
                continue
            if name == 'global':
                name = 'global_'

            kwargs[name] = draw(type_to_strategy[amqptype])
        return method_cls(**kwargs)

    @h.given(methods())
    @h.settings(perform_health_check=False)
    def test_method(method):
        stream = io.BytesIO()
        method.to_bytestream(stream)
        raw = stream.getvalue()

        stream.seek(0)
        unpacked = am.Method.from_bytestream(stream)

        assert method == unpacked
    return test_method()


def test_q():
    m = am.QueueDeclare(queue=None, passive=at.Bool(False), durable=at.Bool(False),
                        exclusive=at.Bool(False), auto_delete=at.Bool(False),
                        no_wait=at.Bool(False), arguments=at.Table(
            {at.ShortStr():  at.Table({})}
        ))
    b = io.BytesIO()
    m.to_bytestream(b)
    b.seek(0)
    new = am.Method.from_bytestream(b)
    assert new == m
