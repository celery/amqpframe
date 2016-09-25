import io
import operator
import collections

import pytest
import hypothesis as h
import hypothesis.strategies as hs

import amqpframe.types as at

from . import strategies

ALL_TYPES = at.BaseType.__subclasses__()
NUMERIC_TYPES = (
    at.SignedByte,
    at.UnsignedByte,
    at.SignedShort,
    at.UnsignedShort,
    at.SignedLong,
    at.UnsignedLong,
    at.SignedLongLong,
    at.UnsignedLongLong,
    at.Decimal,
)
ITERABLE_TYPES = [at.Array, at.Table, at.ShortStr, at.LongStr]


def deep_equals(first, second):
    first_type = type(first)
    second_type = type(second)

    valid_iterable_types = (
        collections.OrderedDict, at.Array, at.Table, at.ShortStr, at.LongStr
    )
    if (first_type not in valid_iterable_types and
            second_type not in valid_iterable_types):
        return first == second

    # If values are strings
    valid_str_types = at.ShortStr, at.LongStr
    if first_type in valid_str_types and second_type in valid_str_types:
        return first == second

    # At this point both first and second types are Array/Table
    if first_type != second_type:
        return False
    if len(first) != len(second):
        return False

    if first_type is at.Array:
        for val_first, val_second in zip(first._value, second._value):
            if not deep_equals(val_first, val_second):
                return False
        return True

    # first_type is types.Table
    return deep_equals(
        sorted(first._value.items(), key=operator.itemgetter(0)),
        sorted(second._value.items(), key=operator.itemgetter(0)),
    )


@h.given(hs.data())
@pytest.mark.parametrize('type_cls', ALL_TYPES)
def test_type_instances_can_be_packed_unpacked(type_cls, data):

    strategy = strategies.type_to_strategy[type_cls]
    value = type_cls(data.draw(strategy))

    stream = io.BytesIO()
    value.to_bytestream(stream)
    stream.seek(0)
    new = type_cls.from_bytestream(stream)

    assert deep_equals(value, new)


@h.given(hs.data())
def test_continious_bools_can_be_packed_unpacked(data):
    bools = data.draw(hs.lists(strategies.bools))
    stream = io.BytesIO()

    at.Bool.many_to_bytestream(bools, stream)
    stream.seek(0)
    new = at.Bool.many_from_bytestream(stream, len(bools))

    assert deep_equals(bools, new)


@h.given(hs.data())
def test_numeric_type_instances_can_be_compared(data):
    first = data.draw(hs.sampled_from(NUMERIC_TYPES))()
    second = data.draw(hs.sampled_from(NUMERIC_TYPES))()
    # We don't actually care if it's True or False
    assert (first < second) in (True, False)


def test_strings_can_be_compared():
    first = at.ShortStr('first')
    second = at.LongStr('second')

    assert first < second


def test_tables_can_be_recursively_compared():
    first_table = at.Table({'key': ['value']})
    second_table = at.Table({'key': ['value']})

    assert first_table == second_table


def test_arrays_can_be_recursively_compared():
    first_array = at.Array([{'key': 'value'}])
    second_array = at.Array([{'key': 'value'}])

    assert first_array == second_array


def test_iterable_type_instances_are_unordered():
    first = at.Table({'key': ['value']})
    second = at.Array([{'key': 'value'}])

    with pytest.raises(TypeError):
        first < second


def test_voids_are_unordered():
    first = at.Void()
    second = at.Void()

    assert first == second

    with pytest.raises(TypeError):
        first < second


@h.given(hs.data())
def test_timestamps_are_ordered(data):
    first = at.Timestamp(data.draw(strategies.timestamps))
    second = at.Timestamp(data.draw(strategies.timestamps))

    assert (first < second) in (True, False)


@h.given(hs.data())
def test_timestamps_can_be_compared(data):
    first = at.Timestamp(data.draw(strategies.timestamps))
    second = at.Timestamp(data.draw(strategies.timestamps))

    assert (first == second) in (True, False)


def test_bools_can_be_used_as_booleans():
    value = at.Bool(True)
    assert value


def test_bools_can_be_compared():
    first = at.Bool(False)
    second = at.Bool(True)

    assert first != second
