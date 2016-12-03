import io

import amqpframe.frames as af


def test_HeaderFrame_can_be_packed_unpacked():
    DATA = b'AMQP\x00\x00\x09\x01'

    stream = io.BytesIO(DATA)
    frame = af.ProtocolHeaderFrame.from_bytestream(stream)

    assert frame.channel_id is None
    assert frame.payload.protocol_major == 0
    assert frame.payload.protocol_minor == 9
    assert frame.payload.protocol_revision == 1

    frame = af.ProtocolHeaderFrame(None, af.ProtocolHeaderPayload(0, 9, 1))
    stream = io.BytesIO()
    frame.to_bytestream(stream)
    assert stream.getvalue() == DATA


def test_HeartbeatFrame_can_be_packed_unpacked():
    DATA = b'\x08\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\xce'

    stream = io.BytesIO(DATA)
    frame = af.Frame.from_bytestream(stream)
    assert frame.channel_id == 0
    assert isinstance(frame, af.HeartbeatFrame)

    frame = af.HeartbeatFrame(0, af.HeartbeatPayload())
    stream = io.BytesIO()
    frame.to_bytestream(stream)
    assert stream.getvalue() == DATA
