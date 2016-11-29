import functools
import amqpframe.types as at

import hypothesis.strategies as hs
import hypothesis.extra.datetime as hed

utf8encode = functools.partial(str.encode, encoding='utf-8')


def validate(cls):
    def inner(value):
        try:
            cls(value)
            return True
        except ValueError:
            return False
    return inner


def st(strategy, cls):
    return strategy.filter(validate(cls))

bools = hs.booleans()
signed_bytes = st(hs.integers(at.SignedByte.MIN, at.SignedByte.MAX), at.SignedByte)
unsigned_bytes = st(hs.integers(at.UnsignedByte.MIN, at.UnsignedByte.MAX), at.UnsignedByte)
signed_shorts = st(hs.integers(at.SignedShort.MIN, at.SignedShort.MAX), at.SignedShort)
unsigned_shorts = st(hs.integers(at.UnsignedShort.MIN, at.UnsignedShort.MAX), at.UnsignedShort)
signed_longs = st(hs.integers(at.SignedLong.MIN, at.SignedLong.MAX), at.SignedLong)
unsigned_longs = st(hs.integers(at.UnsignedLong.MIN, at.UnsignedLong.MAX), at.UnsignedLong)
signed_long_longs = st(hs.integers(at.SignedLongLong.MIN, at.SignedLongLong.MAX), at.SignedLongLong)
unsigned_long_longs = st(hs.integers(at.UnsignedLongLong.MIN, at.UnsignedLongLong.MAX), at.UnsignedLongLong)
floats = st(hs.floats(), at.Float)
doubles = st(hs.floats(), at.Double)
decimals = st(hs.decimals(), at.Decimal)
short_strs = st(hs.text().map(utf8encode), at.ShortStr)
long_strs = st(hs.text().map(utf8encode), at.LongStr)
voids = hs.just(None)
bytearrays = st(hs.binary(), at.ByteArray)
timestamps = st(hed.datetimes(timezones=[]), at.Timestamp)

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
    at.SignedByte: signed_bytes,
    at.UnsignedByte: unsigned_bytes,
    at.SignedShort: signed_shorts,
    at.UnsignedShort: unsigned_shorts,
    at.SignedLong: signed_longs,
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
