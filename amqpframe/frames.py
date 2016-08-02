"""
amqpframe.frames
~~~~~~~~~~~~~~~~

AMQP frames implementation.

"""

import io

from . import basic
from . import types
from . import errors
from . import methods
from . import constants


class Frame:

    frame_type = None

    def __init__(self, channel_id, payload):
        self.channel_id = channel_id
        self.payload = payload

    @classmethod
    def from_bytestream(cls, stream: io.BytesIO):
        # Spec 2.3.5 Frame Details
        frame_type = types.UnsignedByte.from_bytestream(stream)
        channel_id = types.UnsignedShort.from_bytestream(stream)
        # UnsignedLong payload size + 'size' of octets makes ByteArray useful
        payload_bytes = types.ByteArray.from_bytestream(stream)
        end = types.UnsignedByte.from_bytestream(stream)
        # Fail fast if `end` is not what we expect
        assert end == constants.FRAME_END

        payload_stream = io.BytesIO(payload_bytes)
        return FRAMES[frame_type], channel_id, payload_stream

    def to_bytestream(self, stream: io.BytesIO):
        # Spec 2.3.5 Frame Details
        types.UnsignedByte(self.frame_type).to_bytestream(stream)
        types.UnsignedShort(self.channel_id).to_bytestream(stream)
        self.payload.to_bytestream(stream)
        types.UnsignedByte(constants.FRAME_END).to_bytestream(stream)

    def __eq__(self, other):
        return (self.frame_type == other.frame_type and
                self.channel_id == other.channel_id and
                self.payload == other.payload)


class MethodFrame(Frame):
    frame_type = constants.FRAME_METHOD

    @classmethod
    def from_bytestream(cls, stream: io.BytesIO, channel_id):
        payload = methods.Method.from_bytestream(stream)
        return cls(channel_id, payload)


class ContentHeaderFrame(Frame):
    frame_type = constants.FRAME_HEADER

    @classmethod
    def from_payload_bytestream(cls, payload_stream: io.BytesIO, channel_id):
        payload = ContentHeaderPayload.from_bytestream(payload_stream)
        return cls(channel_id, payload)


class ContentBodyFrame(Frame):
    frame_type = constants.FRAME_BODY

    @classmethod
    def from_payload_bytestream(cls, payload_stream: io.BytesIO,
                                channel_id, body_chunk_size):
        payload = ContentBodyPayload.from_bytestream(payload_stream,
                                                     body_chunk_size)
        return cls(channel_id, payload)


class HeartbeatFrame(Frame):
    frame_type = constants.FRAME_HEARTBEAT
    channel_id = 0

    def __init__(self, channel_id, payload):
        assert channel_id == self.channel_id
        super().__init__(channel_id, payload)

    @classmethod
    def from_payload_bytestream(cls, payload_stream: io.BytesIO, channel_id):
        payload = HeartbeatPayload()
        return cls(channel_id, payload)


class ProtocolHeaderFrame:
    """This is actually not a frame - just bytes, but it's quite handy
    to pretend it is a frame to unify `input bytes -> frames -> output bytes`
    sequence.
    """

    def __init__(self, protocol_major=0, protocol_minor=9, protocol_revision=1):
        self.protocol_major = protocol_major
        self.protocol_minor = protocol_minor
        self.protocol_revision = protocol_revision

    def to_bytestream(self, stream: io.BytesIO):
        # Spec 4.2.2 Protocol Header
        stream.write(b'AMQP\x00')
        stream.write(self.protocol_major)
        stream.write(self.protocol_minor)
        stream.write(self.protocol_revision)

    @classmethod
    def from_bytestream(cls, stream: io.BytesIO):
        protocol = stream.read(5)
        assert protocol == b'AMQP\x00'
        protocol_major = stream.read(1)
        protocol_minor = stream.read(1)
        protocol_revision = stream.read(1)
        return cls(protocol_major, protocol_minor, protocol_revision)


class ContentHeaderPayload:

    def __init__(self, class_id, body_length, properties):
        self.class_id = class_id
        self.body_length = body_length
        self.properties = properties
        self.weight = 0

    def __eq__(self, other):
        return (self.class_id == other.class_id and
                self.body_length == other.body_length and
                self.properties == other.properties)

    def to_bytestream(self, stream: io.BytesIO):
        # Spec 2.3.5.2 Content Frames
        types.UnsignedShort(self.class_id).to_bytestream(stream)
        types.UnsignedShort(self.weight).to_bytestream(stream)
        types.UnsignedLongLong(self.body_length).to_bytestream(stream)

        # TODO implement support for more than 14 properties
        properties = bytearray()
        property_flags = 0
        bitshift = 15

        for val in self.properties:
            if val is not None:
                property_flags |= (1 << bitshift)
                properties.append(val.pack(val))
            bitshift -= 1

        types.UnsignedShort(property_flags).to_bytestream(stream)
        stream.write(properties)

    @classmethod
    def from_bytestream(cls, stream: io.BytesIO):
        class_id = types.UnsignedShort.from_bytestream(stream)
        weight = types.UnsignedShort.from_bytestream(stream)
        assert weight == 0
        body_length = types.UnsignedLongLong.from_bytestream(stream)
        property_flags = types.UnsignedShort.from_bytestream(stream)

        PROPERTIES = PROPERTIES_BY_CLASS_ID[class_id]

        props = []

        # TODO implement support for more than 14 properties
        for i, (_, amqptype) in enumerate(PROPERTIES):
            pos = 15 - i  # We started from `content_type` witch has pos==15
            if property_flags & (1 << pos):
                props.append(amqptype.from_bytestream(stream))
            else:
                props.append(None)

        return cls(class_id, body_length, props)


class ContentBodyPayload:

    def __init__(self, data):
        self.data = data

    def to_bytestream(self, stream):
        stream.write(self.data)

    @classmethod
    def from_bytestream(cls, stream, body_chunk_size):
        return cls(stream.read(body_chunk_size))

    def __len__(self):
        return len(self.data)


class HeartbeatPayload:

    def to_bytestream(self, stream):
        stream.write(0)


FRAMES = {
    MethodFrame.frame_type: MethodFrame,
    ContentHeaderFrame.frame_type: ContentHeaderFrame,
    ContentBodyFrame.frame_type: ContentBodyFrame,
    HeartbeatFrame.frame_type: HeartbeatFrame,
}


# Just in case somebody will want to add non-basic stuff...
PROPERTIES_BY_CLASS_ID = {
    60: basic.PROPERTIES,
}
