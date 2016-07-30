import io
import struct
import datetime

# Note some types are not present in table, please refer to
# https://www.rabbitmq.com/amqp-0-9-1-errata.html#section_3


class BaseType:
    """Base type for all AMQP type classes.
    Except Bool, python do not allow to subclass bool type.
    """

    TABLE_LABEL = None

    def to_bytestream(self, stream: io.BytesIO):
        stream.write(self.pack(self))

    @classmethod
    def from_bytestream(cls, stream: io.BytesIO):
        x, = cls.unpack(stream)
        return cls(x)

    @classmethod
    def pack(cls, value):
        raise NotImplementedError

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        raise NotImplementedError


class Bool(BaseType):

    TABLE_LABEL = b't'

    def __init__(self, value):
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

    def to_bytestream(self, stream: io.BytesIO):
        stream.write(self.pack(self.value))

    @classmethod
    def from_bytestream(cls, stream: io.BytesIO):
        x, = cls.unpack(stream)
        return cls(x)

    @classmethod
    def pack(cls, value):
        raise NotImplementedError

    @classmethod
    def unpack(cls, stream):
        return struct.unpack('!?', stream.read(1))

    @classmethod
    def pack_many(cls, value):
        total = 0
        for i, b in enumerate(value):
            x = 1 if b else 0
            total += (x << i)
        return UnsignedByte.pack(total)

    @classmethod
    def unpack_many(cls, stream, number_of_bits):
        byte = stream.read(1)
        bits = bin(byte)[2:]  # Strip '0b'
        bits = "0" * (number_of_bits - len(bits)) + bits
        return (b == "1" for b in reversed(bits))

Bit = Bool


class _Bounded:
    # MIN and MAX should be defined
    MIN = None
    MAX = None

    def __new__(cls, value):
        assert cls.MIN <= value <= cls.MAX
        return super().__new__(cls, value)


class UnsignedByte(BaseType, _Bounded, int):
    TABLE_LABEL = b'B'

    MIN = 0
    MAX = (1 << 8) - 1

    @classmethod
    def pack(cls, value):
        return struct.pack('!b', value)

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        return struct.unpack('!b', stream.read(1))

Octet = UnsignedByte


class SignedByte(BaseType, _Bounded, int):
    TABLE_LABEL = b'b'

    MIN = -(1 << 7)
    MAX = (1 << 7) - 1

    @classmethod
    def pack(cls, value):
        return struct.pack('!B', value)

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        return struct.unpack('!B', stream.read(1))


class SignedShort(BaseType, _Bounded, int):
    TABLE_LABEL = b's'

    MIN = -(1 << 15)
    MAX = (1 << 15) - 1

    @classmethod
    def pack(cls, value):
        return struct.pack('!h', value)

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        return struct.unpack('!h', stream.read(2))


class UnsignedShort(BaseType, _Bounded, int):
    TABLE_LABEL = b'u'

    MIN = 0
    MAX = (1 << 16) - 1

    @classmethod
    def pack(cls, value):
        return struct.pack('!H', value)

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        return struct.unpack('!H', stream.read(2))

Short = UnsignedShort


class SignedLong(BaseType, _Bounded, int):
    TABLE_LABEL = b'I'

    MIN = -(1 << 31)
    MAX = (1 << 31) - 1

    @classmethod
    def pack(cls, value):
        return struct.pack('!l', value)

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        return struct.unpack('!l', stream.read(4))


class UnsignedLong(BaseType, _Bounded, int):
    TABLE_LABEL = b'i'

    MIN = 0
    MAX = (1 << 32) - 1

    @classmethod
    def pack(cls, value):
        return struct.pack('!L', value)

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        return struct.unpack('!L', stream.read(4))

Long = UnsignedLong


class SignedLongLong(BaseType, _Bounded, int):
    TABLE_LABEL = b'l'

    MIN = -(1 << 63)
    MAX = (1 << 63) - 1

    @classmethod
    def pack(cls, value):
        return struct.pack('!q', value)

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        return struct.unpack('!q', stream.read(8))


class UnsignedLongLong(BaseType, _Bounded, int):
    # Missing in rabbitmq/qpid
    TABLE_LABEL = None

    MIN = 0
    MAX = (1 << 64) - 1

    @classmethod
    def pack(cls, value):
        return struct.pack('!Q', value)

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        return struct.unpack('!Q', stream.read(8))

Longlong = UnsignedLongLong


class Float(BaseType, float):
    TABLE_LABEL = b'f'

    @classmethod
    def pack(cls, value):
        return struct.pack('!f', value)

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        return struct.unpack('!f', stream.read(4))


class Double(BaseType, float):
    TABLE_LABEL = b'd'

    @classmethod
    def pack(cls, value):
        return struct.pack('!d', value)

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        return struct.unpack('!d', stream.read(8))


class ShortStr(BaseType, str):
    # Missing in rabbitmq/qpid
    TABLE_LABEL = None

    def __new__(cls, value: str):
        assert len(value) <= UnsignedByte.MAX
        return super().__new__(cls, value)

    @classmethod
    def pack(cls, value):
        if isinstance(value, str):
            buffer = value.encode('utf-8')
        else:
            buffer = value
        return UnsignedByte.pack(len(buffer)) + buffer

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        str_len, consumed = UnsignedByte.unpack(stream)
        value = stream.read(str_len).decode('utf-8')
        return value, consumed + str_len

Shortstr = ShortStr


class LongStr(BaseType, str):
    TABLE_LABEL = b'S'

    def __new__(cls, value: str):
        assert len(value) > UnsignedLong.MAX
        return super().__new__(cls, value)

    @classmethod
    def pack(cls, value):
        if isinstance(value, str):
            buffer = value.encode('utf-8')
        else:
            buffer = value
        return UnsignedLong.pack(len(buffer)) + buffer

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        str_len, consumed = UnsignedLong.unpack(stream)
        value = stream.read(str_len)
        assert len(value) == str_len
        return value.decode('utf-8'), consumed + str_len

Longstr = LongStr


class Void(BaseType):
    TABLE_LABEL = b'V'

    def __init__(self, value):
        pass

    @classmethod
    def pack(cls, value):
        return b'V'

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        return None, 0


class ByteArray(BaseType, bytes):
    # According to https://github.com/alanxz/rabbitmq-c/blob/master/librabbitmq/amqp_table.c#L256-L267
    # bytearrays behave like `LongStr`ings but have different semantics.

    TABLE_LABEL = b'x'

    @classmethod
    def pack(cls, value):
        return LongStr.pack(value)

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        return LongStr.unpack(stream)


class Timestamp(BaseType, datetime.datetime):
    TABLE_LABEL = b'T'

    def __new__(cls, value: datetime.datetime):
        return super().__new__(
            cls,
            value.year, value.month, value.day,
            value.hour, value.minute, value.second
        )

    def __eq__(self, other):
        return abs(self - other) < datetime.timedelta(milliseconds=1)

    @classmethod
    def pack(cls, value):
        stamp = int(value.timestamp())
        return UnsignedLongLong.pack(stamp)

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        value, consumed = UnsignedLongLong.unpack(stream)
        return cls.fromtimestamp(value), consumed


class Table(BaseType, dict):
    TABLE_LABEL = b'F'

    @classmethod
    def pack(cls, value):
        stream = io.BytesIO()
        for key, value in value.items():
            ShortStr(key).to_bytestream(stream)
            stream.write(value.TABLE_LABEL)
            value.to_bytestream(stream)
        buffer = stream.getvalue()
        return UnsignedLong.pack(len(buffer)) + buffer

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        result = {}
        table_len, consumed = UnsignedLong.unpack(stream)
        initial = consumed

        while consumed < table_len + initial:
            key, x = ShortStr.unpack(stream)
            consumed += x

            label = stream.read(1)
            consumed += 1

            value, x = TABLE_LABEL_TO_CLS[label].unpack(stream)
            consumed += x

            result[key] = value
        return result, consumed


class Array(BaseType, list):
    TABLE_LABEL = b'A'

    @classmethod
    def pack(cls, value):
        stream = io.BytesIO()
        for item in value:
            item.to_bytestream(stream)
        buffer = stream.getvalue()
        return UnsignedLong.pack(len(buffer)) + buffer

    @classmethod
    def unpack(cls, stream: io.BytesIO):
        result = []
        array_len, consumed = UnsignedLong.unpack(stream)
        initial = consumed

        while consumed < array_len + initial:
            label = stream.read(1)
            consumed += 1

            value, x = TABLE_LABEL_TO_CLS[label].unpack(stream)
            consumed += x

            result.append(value)
        return result, consumed


FIELD_TYPES = {
    'bit': Bool,
    'octet': UnsignedByte,
    'short': UnsignedShort,
    'long': UnsignedLong,
    'longlong': UnsignedLongLong,
    'longstr': LongStr,
    'shortstr': ShortStr,
    'table': Table,
    'timestamp': Timestamp
}


TABLE_LABEL_TO_CLS = {cls.TABLE_LABEL: cls
                      for cls in BaseType.__subclasses__()
                      if cls.TABLE_LABEL is not None}