import io
import math
import struct
import decimal
import datetime
import operator
import itertools
import functools
import collections
import collections.abc


def _recursive_equals(first, second):
    first_type = type(first)
    second_type = type(second)

    valid_iterable_types = (
        collections.OrderedDict, Array, Table, ShortStr, LongStr
    )
    if (first_type not in valid_iterable_types and
                second_type not in valid_iterable_types):
        return first == second

    # If values are strings
    if first_type in (ShortStr, LongStr) and second_type in (ShortStr, LongStr):
        return first == second

    # At this point both first and second types are Array/Table
    if first_type != second_type:
        return False
    if len(first) != len(second):
        return False

    if first_type is Array:
        for v1, v2 in zip(first, second):
            if not _recursive_equals(v1, v2):
                return False

    # first_type is types.Table
    return _recursive_equals(
        sorted(first.items(), key=operator.itemgetter(0)),
        sorted(first.items(), key=operator.itemgetter(0)),
    )


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks"""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)


# Note some types are not present in table, please refer to
# https://www.rabbitmq.com/amqp-0-9-1-errata.html#section_3


@functools.total_ordering
class BaseType:
    """Base type for all AMQP type classes.
    Except Bool, python do not allow to subclass bool type.
    """

    TABLE_LABEL = None

    _STRUCT_FMT = None
    _STRUCT_SIZE = None

    def __init__(self, value):
        if isinstance(value, BaseType):
            value = value.value
        self.value = self.validate(value)

    @classmethod
    def validate(cls, value):
        raise NotImplementedError

    def pack(self):
        return struct.pack('!' + self._STRUCT_FMT, self.value)

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        raw = stream.read(cls._STRUCT_SIZE)
        return struct.unpack('!' + cls._STRUCT_FMT, raw)[0], cls._STRUCT_SIZE

    def to_bytestream(self, stream: io.BytesIO):
        stream.write(self.pack())

    @classmethod
    def from_bytestream(cls, stream: io.BytesIO):
        x, _ = cls.unpack(stream)
        return cls(x)

    def __eq__(self, other):
        if isinstance(other, BaseType):
            other = other.value
        return self.value == other

    def __lt__(self, other):
        if isinstance(other, BaseType):
            other = other.value
        return self.value < other

    def __hash__(self):
        return hash(self.value)

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.value)


def _bytes2bits(byte, reminder):
    byte = int.from_bytes(byte, byteorder='big')
    bits = bin(byte)[2:]  # Strip '0b'
    # Unfortunately, int.from_bytes strips leading zeroes, let's get them back
    to_fill = reminder // 8
    if reminder % 8 != 0:
        to_fill += 1
    to_fill *= 8
    bits = bits.zfill(to_fill)
    # Get rid of unnecessary bits
    return bits[:reminder]


class Bool(BaseType):

    TABLE_LABEL = b't'

    def __init__(self, value=False):
        super().__init__(value)

    @classmethod
    def validate(cls, value):
        return bool(value)

    def __bool__(self):
        return bool(self.value)

    # pack and unpack used when packing/unpacking happens within tables/arrays
    # pack_many/many_to_bytestream and unpack_many/many_from_bytestream
    # used when packing/unpacking happens elsewhere
    # damn you AMQP creators who decided to save a couple of bytes ;(
    def pack(self):
        return struct.pack('!?', self.value)

    @classmethod
    def unpack(cls, stream):
        return struct.unpack('!?', stream.read(1))[0], 1

    @classmethod
    def pack_many(cls, value):
        result = []
        for values in grouper(value, 8, False):
            total = ''.join('1' if v else '0' for v in values)
            result.append(UnsignedByte(int(total, 2)).pack())
        return b''.join(result)

    @classmethod
    def unpack_many(cls, stream, number_of_bits):
        bytes_count = number_of_bits // 8
        if number_of_bits % 8 != 0:
            bytes_count += 1
        bits = _bytes2bits(stream.read(bytes_count), number_of_bits)
        return [cls(b == '1') for b in bits]

    @classmethod
    def many_to_bytestream(cls, bools, stream):
        packed = cls.pack_many(bools)
        stream.write(packed)

    @classmethod
    def many_from_bytestream(cls, stream, number_of_bits):
        return cls.unpack_many(stream, number_of_bits)

Bit = Bool


class SignedByte(BaseType):
    TABLE_LABEL = b'b'

    MIN = -(1 << 7)
    MAX = (1 << 7) - 1

    _STRUCT_FMT = 'b'
    _STRUCT_SIZE = 1

    def __init__(self, value=0):
        super().__init__(value)

    @classmethod
    def validate(cls, value):
        value = int(value)
        if not (cls.MIN <= value <= cls.MAX):
            raise ValueError('value {} must be in range: {}, {}'.format(
                value, cls.MIN, cls.MAX
            ))
        return value


class UnsignedByte(BaseType):
    TABLE_LABEL = b'B'

    MIN = 0
    MAX = (1 << 8) - 1

    _STRUCT_FMT = 'B'
    _STRUCT_SIZE = 1

    def __init__(self, value=0):
        super().__init__(value)

    @classmethod
    def validate(cls, value):
        value = int(value)
        if not (cls.MIN <= value <= cls.MAX):
            raise ValueError('value {} must be in range: {}, {}'.format(
                value, cls.MIN, cls.MAX
            ))
        return value

Octet = UnsignedByte


class SignedShort(BaseType):
    TABLE_LABEL = b's'

    MIN = -(1 << 15)
    MAX = (1 << 15) - 1

    _STRUCT_FMT = 'h'
    _STRUCT_SIZE = 2

    def __init__(self, value=0):
        super().__init__(value)

    @classmethod
    def validate(cls, value):
        value = int(value)
        if not (cls.MIN <= value <= cls.MAX):
            raise ValueError('value {} must be in range: {}, {}'.format(
                value, cls.MIN, cls.MAX
            ))
        return value


class UnsignedShort(BaseType):
    TABLE_LABEL = b'u'

    MIN = 0
    MAX = (1 << 16) - 1

    _STRUCT_FMT = 'H'
    _STRUCT_SIZE = 2

    def __init__(self, value=0):
        super().__init__(value)

    @classmethod
    def validate(cls, value):
        value = int(value)
        if not (cls.MIN <= value <= cls.MAX):
            raise ValueError('value {} must be in range: {}, {}'.format(
                value, cls.MIN, cls.MAX
            ))
        return value

Short = UnsignedShort


class SignedLong(BaseType):
    TABLE_LABEL = b'I'

    MIN = -(1 << 31)
    MAX = (1 << 31) - 1

    _STRUCT_FMT = 'l'
    _STRUCT_SIZE = 4

    def __init__(self, value=0):
        super().__init__(value)

    @classmethod
    def validate(cls, value):
        value = int(value)
        if not (cls.MIN <= value <= cls.MAX):
            raise ValueError('value {} must be in range: {}, {}'.format(
                value, cls.MIN, cls.MAX
            ))
        return value


class UnsignedLong(BaseType):
    TABLE_LABEL = b'i'

    MIN = 0
    MAX = (1 << 32) - 1

    _STRUCT_FMT = 'L'
    _STRUCT_SIZE = 4

    def __init__(self, value=0):
        super().__init__(value)

    @classmethod
    def validate(cls, value):
        value = int(value)
        if not (cls.MIN <= value <= cls.MAX):
            raise ValueError('value {} must be in range: {}, {}'.format(
                value, cls.MIN, cls.MAX
            ))
        return value

Long = UnsignedLong


class SignedLongLong(BaseType):
    TABLE_LABEL = b'l'

    MIN = -(1 << 63)
    MAX = (1 << 63) - 1

    _STRUCT_FMT = 'q'
    _STRUCT_SIZE = 8

    def __init__(self, value=0):
        super().__init__(value)

    @classmethod
    def validate(cls, value):
        value = int(value)
        if not (cls.MIN <= value <= cls.MAX):
            raise ValueError('value {} must be in range: {}, {}'.format(
                value, cls.MIN, cls.MAX
            ))
        return value


class UnsignedLongLong(BaseType):
    # Missing in rabbitmq/qpid table types
    TABLE_LABEL = None

    MIN = 0
    MAX = (1 << 64) - 1

    _STRUCT_FMT = 'Q'
    _STRUCT_SIZE = 8

    def __init__(self, value=0):
        super().__init__(value)

    @classmethod
    def validate(cls, value):
        value = int(value)
        if not (cls.MIN <= value <= cls.MAX):
            raise ValueError('value {} must be in range: {}, {}'.format(
                value, cls.MIN, cls.MAX
            ))
        return value

Longlong = UnsignedLongLong


class Float(BaseType):
    TABLE_LABEL = b'f'

    _STRUCT_FMT = 'f'
    _STRUCT_SIZE = 4

    def __init__(self, value=0.0):
        super().__init__(value)

    @classmethod
    def validate(cls, value):
        value = float(value)
        if math.isnan(value):
            raise ValueError
        try:
            return struct.unpack('!f', struct.pack('!f', value))[0]
        except OverflowError:
            raise ValueError


class Double(BaseType):
    TABLE_LABEL = b'd'

    _STRUCT_FMT = 'd'
    _STRUCT_SIZE = 8

    def __init__(self, value=0.0):
        super().__init__(value)

    @classmethod
    def validate(cls, value):
        value = float(value)
        if math.isnan(value):
            raise ValueError
        try:
            return struct.unpack('!d', struct.pack('!d', value))[0]
        except OverflowError:
            raise ValueError


class Decimal(BaseType):
    TABLE_LABEL = b'D'

    MIN_EXP = UnsignedByte.MIN
    MAX_EXP = UnsignedByte.MAX
    MIN_VALUE = UnsignedLong.MIN
    MAX_VALUE = UnsignedLong.MAX

    def __init__(self, value=None):
        if value is None:
            value = decimal.Decimal(0)
        super().__init__(value)

    @classmethod
    def validate(cls, value):
        if not isinstance(value, decimal.Decimal):
            raise ValueError('value must be of type `decimal.Decimal`, '
                             'got {} instead'.format(type(value)))
        sign, digits, exponent = value.as_tuple()
        if (sign == 0 and
                exponent != 'F' and  # Decimal('Infinity')
                exponent != 'n' and  # Decimal('NaN')
                cls.MIN_EXP <= exponent <= cls.MAX_EXP and
                cls.MIN_VALUE <= value <= cls.MAX_VALUE):
            return value
        raise ValueError('bad decimal value: {!r}'.format(value))

    def pack(self):
        sign, digits, exponent = self.value.as_tuple()
        v = 0
        for d in digits:
            v = v * 10 + d
        if sign:
            v = -v
        return UnsignedByte(-exponent).pack() + UnsignedLong(v).pack()

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        total = 0
        exponent, consumed = UnsignedByte.unpack(stream)
        total += consumed
        v, consumed = UnsignedLong.unpack(stream)
        total += consumed
        value = decimal.Decimal(v) / decimal.Decimal(10 ** exponent)
        return cls(value), total


class ShortStr(BaseType):
    # Missing in rabbitmq/qpid
    TABLE_LABEL = None
    MAX = UnsignedByte.MAX

    def __init__(self, value=b''):
        if isinstance(value, str):
            value = value.encode('utf-8')
        super().__init__(value)

    @classmethod
    def validate(cls, value):
        try:
            value.decode('utf-8')
        except UnicodeDecodeError:
            raise ValueError('value must be utf-8 encoded bytes')
        if len(value) > cls.MAX:
            raise ValueError(
                'value {!r} is too long for ShortStr'.format(value)
            )
        return value

    def pack(self):
        return UnsignedByte(len(self.value)).pack() + self.value

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        str_len, consumed = UnsignedByte.unpack(stream)
        value = stream.read(str_len)
        return cls(value), consumed + str_len

Shortstr = ShortStr


class LongStr(BaseType):
    TABLE_LABEL = b'S'
    MAX = UnsignedLong.MAX

    def __init__(self, value=b''):
        if isinstance(value, str):
            value = value.encode('utf-8')
        super().__init__(value)

    @classmethod
    def validate(cls, value):
        try:
            value.decode('utf-8')
        except UnicodeDecodeError:
            raise ValueError('value must be utf-8 encoded bytes')
        if len(value) > cls.MAX:
            raise ValueError('value {!r} is too long for LongStr'.format(value))
        return value

    def pack(self):
        return UnsignedLong(len(self.value)).pack() + self.value

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        str_len, consumed = UnsignedLong.unpack(stream)
        value = stream.read(str_len)
        assert len(value) == str_len
        return cls(value), consumed + str_len

Longstr = LongStr


class Void(BaseType):
    TABLE_LABEL = b'V'

    def __init__(self, value=None):
        self.value = self.validate(value)

    @classmethod
    def validate(cls, value):
        if value is not None:
            raise TypeError(
                'void value must be None, got {!r} instead'.format(value)
            )
        return value

    def pack(self):
        return b''  # Nothing to return - it's Void!

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        return None, 0


class ByteArray(BaseType):
    # According to https://github.com/alanxz/rabbitmq-c/blob/master/librabbitmq/amqp_table.c#L256-L267
    # bytearrays behave like `LongStr`ings but have different semantics.

    TABLE_LABEL = b'x'
    MAX = UnsignedLong.MAX

    def __init__(self, value=b''):
        super().__init__(value)

    @classmethod
    def validate(cls, value):
        if not isinstance(value, bytes):
            raise ValueError(
                'ByteArray value must be bytes, got {!r} instead'.format(value)
            )
        if len(value) > cls.MAX:
            raise ValueError('value {!r} is too long for ByteArray'.format(
                value
            ))
        return value

    def pack(self):
        return UnsignedLong(len(self.value)).pack() + self.value

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        str_len, consumed = UnsignedLong.unpack(stream)
        value = stream.read(str_len)
        assert len(value) == str_len
        return cls(value), consumed + str_len


class Timestamp(BaseType):
    TABLE_LABEL = b'T'

    def __init__(self, value=None):
        if value is None:
            value = datetime.datetime.utcnow()
        super().__init__(value)

    @classmethod
    def validate(cls, value):
        if not isinstance(value, datetime.datetime):
            raise ValueError('value must be of type `datetime.datetime`, '
                             'got {} instead'.format(type(value)))
        if value.year < 1970:
            raise ValueError('timestamps must be after 1970')
        return value

    def pack(self):
        stamp = self.value.timestamp()
        return UnsignedLongLong(stamp).pack()

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        value, consumed = UnsignedLongLong.unpack(stream)
        date = datetime.datetime.fromtimestamp(value)
        return cls(date), consumed

    def __eq__(self, other):
        if isinstance(other, BaseType):
            other = other.value
        diff = abs(self.value - other)
        # Spec 4.2.5.4 Timestamps, accuracy: 1 second
        return diff < datetime.timedelta(seconds=1)


class Table(BaseType, collections.abc.MutableMapping):
    TABLE_LABEL = b'F'

    def __init__(self, value=None):
        if value is None:
            value = {}
        self._value = self.validate(value)

    @property
    def value(self):
        return {k.value: v.value for k, v in self._value.items()}

    @classmethod
    def validate(cls, value):
        validated = {}
        for key, value in value.items():
            if not isinstance(key, ShortStr):
                key = ShortStr(key)
            if not isinstance(value, BaseType):
                value = _py_type_to_amqp_type(value)
            validated[key] = value
        return validated

    def pack(self):
        stream = io.BytesIO()
        for key, value in self._value.items():
            key.to_bytestream(stream)
            stream.write(value.TABLE_LABEL)
            value.to_bytestream(stream)
        buffer = stream.getvalue()
        return UnsignedLong(len(buffer)).pack() + buffer

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        result = {}
        table_len, initial = UnsignedLong.unpack(stream)
        consumed = initial

        while consumed < initial + table_len:
            key, x = ShortStr.unpack(stream)
            consumed += x

            label = stream.read(1)
            consumed += 1

            amqptype = TABLE_LABEL_TO_CLS[label]
            value, x = amqptype.unpack(stream)
            consumed += x

            result[key] = amqptype(value)
        return result, consumed

    def __getitem__(self, key):
        if isinstance(key, (str, bytes)):
            key = ShortStr(key)
        return self._value[key]

    def __setitem__(self, key, value):
        if isinstance(key, (str, bytes)):
            key = ShortStr(key)
        if not isinstance(value, BaseType):
            value = _py_type_to_amqp_type(value)
        self._value[key] = value

    def __delitem__(self, key):
        if isinstance(key, (str, bytes)):
            key = ShortStr(key)
        del self._value[key]

    def __iter__(self):
        return iter(self._value)

    def __len__(self):
        return len(self._value)

    def __eq__(self, other):
        if isinstance(other, BaseType):
            other = other.value
        return _recursive_equals(self._value, other)

    def __lt__(self, other):
        return NotImplemented

    def __hash__(self):
        raise NotImplementedError


class Array(BaseType, collections.abc.MutableSequence):
    TABLE_LABEL = b'A'

    def __init__(self, value=None):
        if value is None:
            value = []
        self._value = self.validate(value)

    @property
    def value(self):
        return [v.value for v in self._value]

    @classmethod
    def validate(cls, value):
        validated = []
        for item in value:
            if not isinstance(item, BaseType):
                item = _py_type_to_amqp_type(item)
            validated.append(item)
        return validated

    def pack(self):
        stream = io.BytesIO()
        for value in self._value:
            stream.write(value.TABLE_LABEL)
            value.to_bytestream(stream)
        buffer = stream.getvalue()
        return UnsignedLong(len(buffer)).pack() + buffer

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        result = []
        array_len, consumed = UnsignedLong.unpack(stream)
        initial = consumed

        while consumed < (array_len + initial):
            label = stream.read(1)
            consumed += 1

            amqptype = TABLE_LABEL_TO_CLS[label]
            value, x = amqptype.unpack(stream)
            consumed += x

            result.append(amqptype(value))
        return result, consumed

    def __getitem__(self, key):
        return self._value[key]

    def __setitem__(self, key, value):
        if not isinstance(value, BaseType):
            value = _py_type_to_amqp_type(value)
        self._value[key] = value

    def __delitem__(self, key):
        del self._value[key]

    def __len__(self):
        return len(self._value)

    def insert(self, index, value):
        if not isinstance(value, BaseType):
            value = _py_type_to_amqp_type(value)
        self._value.insert(index, value)

    def __hash__(self):
        raise NotImplementedError

    def __eq__(self, other):
        if isinstance(other, BaseType):
            other = other.value
        return _recursive_equals(self._value, other)


def _py_type_to_amqp_type(value):
    if isinstance(value, bool):
        value = Bool(value)
    elif isinstance(value, (str, bytes)):
        if isinstance(value, bytes):
            try:
                # If we can decode UTF-8, it's LongStr
                # No ShortStr support in rabbitmq/qpid
                value.decode('utf-8')
                cls = LongStr
            except UnicodeDecodeError:
                # If we can't decode UTF-8, it's ByteArray
                cls = ByteArray
        else:
            cls = LongStr
        value = cls(value)
    elif isinstance(value, float):
        try:
            value = Float(value)
        except ValueError:
            value = Double(value)
    elif isinstance(value, int):
        last_error = None
        for cls in (SignedByte, UnsignedByte,
                    SignedShort, UnsignedShort,
                    SignedLong, UnsignedLong,
                    SignedLongLong):
            try:
                value = cls(value)
                last_error = None
                break
            except ValueError as exc:
                last_error = exc
        if last_error is not None:  # pragma: no cover
            raise last_error
    elif isinstance(value, decimal.Decimal):
        value = Decimal(value)
    elif isinstance(value, datetime.datetime):
        value = Timestamp(value)
    elif isinstance(value, dict):
        value = Table(value)
    elif isinstance(value, (list, tuple)):
        value = Array(value)
    elif value is None:
        value = Void()
    else:
        raise ValueError()
    return value


TABLE_LABEL_TO_CLS = {cls.TABLE_LABEL: cls
                      for cls in BaseType.__subclasses__()
                      if cls.TABLE_LABEL is not None}
