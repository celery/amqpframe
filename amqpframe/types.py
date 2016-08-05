import io
import struct
import decimal
import datetime
import itertools

from . import errors


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks"""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)


# Note some types are not present in table, please refer to
# https://www.rabbitmq.com/amqp-0-9-1-errata.html#section_3


class BaseType:
    """Base type for all AMQP type classes.
    Except Bool, python do not allow to subclass bool type.
    """

    TABLE_LABEL = None

    def to_bytestream(self, stream: io.BytesIO):
         stream.write(self.pack())
#        try:
#            stream.write(self.pack())
#        except struct.error as exc:
#            raise errors.InternalError(
#                'Unable to pack {}'.format(self)
#            ) from exc

    @classmethod
    def from_bytestream(cls, stream: io.BytesIO):
        x, _ = cls.unpack(stream)
        #try:
        #    x, _ = cls.unpack(stream)
        #except struct.error as exc:
        #    raise errors.SyntaxError(
        #        'Unable to unpack {} from the stream'.format(cls.__name__)
        #    ) from exc
        return cls(x)

    def pack(self):
        raise NotImplementedError

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        raise NotImplementedError

    def __repr__(self):
        orig = super().__repr__()
        return '<{}: {} at {}>'.format(self.__class__.__name__, orig, id(self))


def _bytes2bits(byte, reminder):
    byte = int.from_bytes(byte, byteorder='big')
    bits = bin(byte)[2:]  # Strip '0b'
    # Unfortunately, int.from_bytes strips leading zeroes, let's get them back
    to_fill = (reminder // 8 + 1) * 8
    bits = bits.zfill(to_fill)
    # Get rid of unnecessary bits
    return bits[:reminder]


class Bool(BaseType):

    TABLE_LABEL = b't'

    def __init__(self, value=False):
        if isinstance(value, Bool):
            value = value.value
        self.value = value

    def __eq__(self, other):
        if isinstance(other, type(self.value)):
            return self.value == other
        try:
            return self.value == other.value
        except AttributeError:
            return NotImplemented

    def __bool__(self):
        return self.value

    @classmethod
    def from_bytestream(cls, stream: io.BytesIO):
        try:
            x, _ = cls.unpack(stream)
        except struct.error:
            raise errors.SyntaxError(
                'Unable to unpack {} from the stream'.format(cls.__name__)
            )
        return cls(x)

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
        bytes_count = number_of_bits // 8 + 1
        bits = _bytes2bits(stream.read(bytes_count), number_of_bits)
        return [cls(b == '1') for b in bits]

    @classmethod
    def many_to_bytestream(cls, bools, stream):
        packed = cls.pack_many(bools)
        stream.write(packed)

    @classmethod
    def many_from_bytestream(cls, stream, number_of_bits):
        return cls.unpack_many(stream, number_of_bits)

    def __repr__(self):
        return '<{}: {} at {}>'.format(self.__class__.__name__, bool(self), id(self))

Bit = Bool


class _Bounded:
    # MIN and MAX should be defined
    MIN = None
    MAX = None

    def __new__(cls, value=0):
        assert cls.MIN <= value <= cls.MAX
        return super().__new__(cls, value)


class SignedByte(BaseType, _Bounded, int):
    TABLE_LABEL = b'b'

    MIN = -(1 << 7)
    MAX = (1 << 7) - 1

    def pack(self):
        return struct.pack('!b', self)

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        return struct.unpack('!b', stream.read(1))[0], 1


class UnsignedByte(BaseType, _Bounded, int):
    TABLE_LABEL = b'B'

    MIN = 0
    MAX = (1 << 8) - 1

    def pack(self):
        return struct.pack('!B', self)

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        return struct.unpack('!B', stream.read(1))[0], 1

Octet = UnsignedByte


class SignedShort(BaseType, _Bounded, int):
    TABLE_LABEL = b's'

    MIN = -(1 << 15)
    MAX = (1 << 15) - 1

    def pack(self):
        return struct.pack('!h', self)

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        return struct.unpack('!h', stream.read(2))[0], 2


class UnsignedShort(BaseType, _Bounded, int):
    TABLE_LABEL = b'u'

    MIN = 0
    MAX = (1 << 16) - 1

    def pack(self):
        return struct.pack('!H', self)

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        return struct.unpack('!H', stream.read(2))[0], 2

Short = UnsignedShort


class SignedLong(BaseType, _Bounded, int):
    TABLE_LABEL = b'I'

    MIN = -(1 << 31)
    MAX = (1 << 31) - 1

    def pack(self):
        return struct.pack('!l', self)

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        return struct.unpack('!l', stream.read(4))[0], 4


class UnsignedLong(BaseType, _Bounded, int):
    TABLE_LABEL = b'i'

    MIN = 0
    MAX = (1 << 32) - 1

    def pack(self):
        return struct.pack('!L', self)

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        return struct.unpack('!L', stream.read(4))[0], 4

Long = UnsignedLong


class SignedLongLong(BaseType, _Bounded, int):
    TABLE_LABEL = b'l'

    MIN = -(1 << 63)
    MAX = (1 << 63) - 1

    def pack(self):
        return struct.pack('!q', self)

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        return struct.unpack('!q', stream.read(8))[0], 8


class UnsignedLongLong(BaseType, _Bounded, int):
    # Missing in rabbitmq/qpid
    # Or not?
    TABLE_LABEL = b'L'

    MIN = 0
    MAX = (1 << 64) - 1

    def pack(self):
        return struct.pack('!Q', self)

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        return struct.unpack('!Q', stream.read(8))[0], 8

Longlong = UnsignedLongLong


class Float(BaseType, float):
    TABLE_LABEL = b'f'

    def pack(self):
        return struct.pack('!f', self)

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        return struct.unpack('!f', stream.read(4))[0], 4


class Double(BaseType, float):
    TABLE_LABEL = b'd'

    def pack(self):
        return struct.pack('!d', self)

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        return struct.unpack('!d', stream.read(8))[0], 8


class Decimal(BaseType, decimal.Decimal):
    TABLE_LABEL = b'D'

    def pack(self):
        sign, digits, exponent = self.as_tuple()
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
        return cls(v) / cls(10 ** exponent), total


class ShortStr(BaseType, str):
    # Missing in rabbitmq/qpid
    TABLE_LABEL = None
    MAX = UnsignedByte.MAX

    def __new__(cls, value: str = ''):
        if isinstance(value, str):
            buffer = value.encode('utf-8')
        else:
            buffer = value
        assert len(buffer) <= cls.MAX
        instance = super().__new__(cls, value)
        instance._buffer = buffer
        return instance

    def pack(self):
        return UnsignedByte(len(self._buffer)).pack() + self._buffer

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        str_len, consumed = UnsignedByte.unpack(stream)
        value = stream.read(str_len).decode('utf-8')
        return cls(value), consumed + str_len

Shortstr = ShortStr


class LongStr(BaseType, str):
    TABLE_LABEL = b'S'
    MAX = UnsignedLong.MAX

    def __new__(cls, value: str = ''):
        if isinstance(value, str):
            buffer = value.encode('utf-8')
        else:
            buffer = value
        assert len(buffer) <= cls.MAX
        instance = super().__new__(cls, value)
        instance._buffer = buffer
        return instance

    def pack(self):
        return UnsignedLong(len(self._buffer)).pack() + self._buffer

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        str_len, consumed = UnsignedLong.unpack(stream)
        value = stream.read(str_len)
        assert len(value) == str_len
        value = value.decode('utf-8')
        return cls(value), consumed + str_len

Longstr = LongStr


class Void(BaseType):
    TABLE_LABEL = b'V'

    def __init__(self, value=None):
        pass

    def pack(self):
        return b''  # Nothing to return - it's Void!

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        return None, 0


class ByteArray(BaseType, bytes):
    # According to https://github.com/alanxz/rabbitmq-c/blob/master/librabbitmq/amqp_table.c#L256-L267
    # bytearrays behave like `LongStr`ings but have different semantics.

    TABLE_LABEL = b'x'

    def pack(self):
        return UnsignedLong(len(self)).pack() + self

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        str_len, consumed = UnsignedLong.unpack(stream)
        value = stream.read(str_len)
        assert len(value) == str_len
        return value, consumed + str_len


class Timestamp(BaseType, datetime.datetime):
    TABLE_LABEL = b'T'

    def __new__(cls, value: datetime.datetime = None):
        if value is None:
            value = datetime.datetime.utcnow()
        return super().__new__(
            cls,
            value.year, value.month, value.day,
            value.hour, value.minute, value.second
        )

    def __eq__(self, other):
        return abs(self - other) < datetime.timedelta(milliseconds=1)

    def pack(self):
        stamp = int(self.timestamp())
        return UnsignedLongLong(stamp).pack()

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        value, consumed = UnsignedLongLong.unpack(stream)
        date = datetime.datetime.fromtimestamp(value)
        return cls(date), consumed


class Table(BaseType, dict):
    TABLE_LABEL = b'F'

    def pack(self):
        stream = io.BytesIO()
        for key, value in self.items():
            key.to_bytestream(stream)
            stream.write(value.TABLE_LABEL)
            value.to_bytestream(stream)
        buffer = stream.getvalue()
        return UnsignedLong(len(buffer)).pack() + buffer

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        result = {}
        table_len, _ = UnsignedLong.unpack(stream)
        consumed = 0

        while consumed < table_len:
            key, x = ShortStr.unpack(stream)
            consumed += x

            label = stream.read(1)
            consumed += 1

            amqptype = TABLE_LABEL_TO_CLS[label]
            value, x = amqptype.unpack(stream)
            consumed += x

            result[key] = amqptype(value)
        return result, consumed


class Array(BaseType, list):
    TABLE_LABEL = b'A'

    def pack(self):
        stream = io.BytesIO()
        for value in self:
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


TABLE_LABEL_TO_CLS = {cls.TABLE_LABEL: cls
                      for cls in BaseType.__subclasses__()
                      if cls.TABLE_LABEL is not None}
