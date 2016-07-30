"""
amqpframe.methods
~~~~~~~~~~~~~~~~~

Implementation of AMQP methods.

This file was generated 2016-07-30 07:50:32.235832 from
/spec/amqp0-9-1.extended.xml.

"""

import io
import struct
import collections

from . import types


def select_method(raw: bytes):
    stream = io.BytesIO(raw)
    # Unpacking method type, spec 2.3.5.1 Method Frames
    method_type = struct.unpack('!HH', stream.read(4))
    return METHODS[method_type].from_bytestream(stream)


class BaseMethod:
    """Base class for all AMQP methods."""

    def __init__(self, *values):
        assert len(values) == len(self.field_info)

        self.values = collections.OrderedDict()
        for (name, amqptype), value in zip(self.field_info, values):
            self.values[name] = amqptype(value)

    @classmethod
    def from_bytestream(cls, stream):
        values = []
        number_of_bits = 0
        for amqptype in cls.field_info.values():
            if amqptype is types.Bool:
                number_of_bits += 1
                continue
            elif number_of_bits:
                # We have some bools but this next field is not a bool
                val = ord(stream.read(1))
                values.extend(types.Bool.unpack_many(val, number_of_bits))
                number_of_bits = 0

            values.append(amqptype.from_bytestream(stream))

        if number_of_bits:
            val = ord(stream.read(1))
            values.extend(types.Bool.unpack_many(val, number_of_bits))
        return cls(*values)

    def to_bytestream(self, stream):
        # Packing method type, spec 2.3.5.1 Method Frames
        method_type_bytes = struct.pack('!HH', *self.method_type)
        stream.write(method_type_bytes)
        bits = []
        for value in self.values.values():
            if isinstance(value, types.Bool):
                bits.append(value.value)
            else:
                if bits:
                    stream.write(types.Bool.pack_many(bits))
                    bits = []
                value.to_bytestream(stream)

        if bits:
            stream.write(types.Bool.pack_many(bits))

    def __getattr__(self, name):
        try:
            return self.fields[name]
        except KeyError:
            raise AttributeError('{} object has no attribute {}'.format(
                type(self).__name__, name
            )) from None

    def __eq__(self, other):
        return (self.method_type == other.method_type and
                self.values == other.values)


class ConnectionStart(BaseMethod):
    """This method starts the connection negotiation process by telling the
    client the protocol version that the server proposes, along with a list of
    security mechanisms which the client can use for authentication.

    Arguments:
        version_major: Octet
        version_minor: Octet
        server_properties: Table
        mechanisms: Longstr
        locales: Longstr
    """
    method_type = (10, 10)

    field_info = (
        ("version_major", types.Octet),
        ("version_minor", types.Octet),
        ("server_properties", types.Table),
        ("mechanisms", types.Longstr),
        ("locales", types.Longstr),
    )

    synchronous = True

    def __init__(self,
                 version_major,
                 version_minor,
                 server_properties,
                 mechanisms,
                 locales):
        super().__init__(
             version_major,
             version_minor,
             server_properties,
             mechanisms,
             locales,
        )


class ConnectionStartOK(BaseMethod):
    """This method selects a SASL security mechanism.

    Arguments:
        client_properties: Table
        mechanism: Shortstr
        response: Longstr
        locale: Shortstr
    """
    method_type = (10, 11)

    field_info = (
        ("client_properties", types.Table),
        ("mechanism", types.Shortstr),
        ("response", types.Longstr),
        ("locale", types.Shortstr),
    )

    synchronous = True

    def __init__(self,
                 client_properties,
                 mechanism,
                 response,
                 locale):
        super().__init__(
             client_properties,
             mechanism,
             response,
             locale,
        )


class ConnectionSecure(BaseMethod):
    """The SASL protocol works by exchanging challenges and responses until
    both peers have received sufficient information to authenticate each other.
    This method challenges the client to provide more information.

    Arguments:
        challenge: Longstr
    """
    method_type = (10, 20)

    field_info = (
        ("challenge", types.Longstr),
    )

    synchronous = True

    def __init__(self,
                 challenge):
        super().__init__(
             challenge,
        )


class ConnectionSecureOK(BaseMethod):
    """This method attempts to authenticate, passing a block of SASL data for
    the security mechanism at the server side.

    Arguments:
        response: Longstr
    """
    method_type = (10, 21)

    field_info = (
        ("response", types.Longstr),
    )

    synchronous = True

    def __init__(self,
                 response):
        super().__init__(
             response,
        )


class ConnectionTune(BaseMethod):
    """This method proposes a set of connection configuration values to the
    client. The client can accept and/or adjust these.

    Arguments:
        channel_max: Short
        frame_max: Long
        heartbeat: Short
    """
    method_type = (10, 30)

    field_info = (
        ("channel_max", types.Short),
        ("frame_max", types.Long),
        ("heartbeat", types.Short),
    )

    synchronous = True

    def __init__(self,
                 channel_max,
                 frame_max,
                 heartbeat):
        super().__init__(
             channel_max,
             frame_max,
             heartbeat,
        )


class ConnectionTuneOK(BaseMethod):
    """This method sends the client's connection tuning parameters to the
    server. Certain fields are negotiated, others provide capability
    information.

    Arguments:
        channel_max: Short
        frame_max: Long
        heartbeat: Short
    """
    method_type = (10, 31)

    field_info = (
        ("channel_max", types.Short),
        ("frame_max", types.Long),
        ("heartbeat", types.Short),
    )

    synchronous = True

    def __init__(self,
                 channel_max,
                 frame_max,
                 heartbeat):
        super().__init__(
             channel_max,
             frame_max,
             heartbeat,
        )


class ConnectionOpen(BaseMethod):
    """This method opens a connection to a virtual host, which is a collection
    of resources, and acts to separate multiple application domains within a
    server. The server may apply arbitrary limits per virtual host, such as the
    number of each type of entity that may be used, per connection and/or in
    total.

    Arguments:
        virtual_host: Shortstr
        reserved_1: Shortstr
        reserved_2: Bit
    """
    method_type = (10, 40)

    field_info = (
        ("virtual_host", types.Shortstr),
        ("reserved_1", types.Shortstr),
        ("reserved_2", types.Bit),
    )

    synchronous = True

    def __init__(self,
                 virtual_host,
                 reserved_1,
                 reserved_2):
        super().__init__(
             virtual_host,
             reserved_1,
             reserved_2,
        )


class ConnectionOpenOK(BaseMethod):
    """This method signals to the client that the connection is ready for use.

    Arguments:
        reserved_1: Shortstr
    """
    method_type = (10, 41)

    field_info = (
        ("reserved_1", types.Shortstr),
    )

    synchronous = True

    def __init__(self,
                 reserved_1):
        super().__init__(
             reserved_1,
        )


class ConnectionClose(BaseMethod):
    """This method indicates that the sender wants to close the connection.
    This may be due to internal conditions (e.g. a forced shut-down) or due to
    an error handling a specific method, i.e. an exception. When a close is due
    to an exception, the sender provides the class and method id of the method
    which caused the exception.

    Arguments:
        reply_code: Short
        reply_text: Shortstr
        class_id: Short
        method_id: Short
    """
    method_type = (10, 50)

    field_info = (
        ("reply_code", types.Short),
        ("reply_text", types.Shortstr),
        ("class_id", types.Short),
        ("method_id", types.Short),
    )

    synchronous = True

    def __init__(self,
                 reply_code,
                 reply_text,
                 class_id,
                 method_id):
        super().__init__(
             reply_code,
             reply_text,
             class_id,
             method_id,
        )


class ConnectionCloseOK(BaseMethod):
    """This method confirms a Connection.Close method and tells the recipient
    that it is safe to release resources for the connection and close the
    socket.
    """
    method_type = (10, 51)

    field_info = ()

    synchronous = True


class ChannelOpen(BaseMethod):
    """This method opens a channel to the server.

    Arguments:
        reserved_1: Shortstr
    """
    method_type = (20, 10)

    field_info = (
        ("reserved_1", types.Shortstr),
    )

    synchronous = True

    def __init__(self,
                 reserved_1):
        super().__init__(
             reserved_1,
        )


class ChannelOpenOK(BaseMethod):
    """This method signals to the client that the channel is ready for use.

    Arguments:
        reserved_1: Longstr
    """
    method_type = (20, 11)

    field_info = (
        ("reserved_1", types.Longstr),
    )

    synchronous = True

    def __init__(self,
                 reserved_1):
        super().__init__(
             reserved_1,
        )


class ChannelFlow(BaseMethod):
    """This method asks the peer to pause or restart the flow of content data
    sent by a consumer. This is a simple flow-control mechanism that a peer can
    use to avoid overflowing its queues or otherwise finding itself receiving
    more messages than it can process. Note that this method is not intended
    for window control. It does not affect contents returned by Basic.Get-Ok
    methods.

    Arguments:
        active: Bit
    """
    method_type = (20, 20)

    field_info = (
        ("active", types.Bit),
    )

    synchronous = True

    def __init__(self,
                 active):
        super().__init__(
             active,
        )


class ChannelFlowOK(BaseMethod):
    """Confirms to the peer that a flow command was received and processed.

    Arguments:
        active: Bit
    """
    method_type = (20, 21)

    field_info = (
        ("active", types.Bit),
    )

    synchronous = False

    def __init__(self,
                 active):
        super().__init__(
             active,
        )


class ChannelClose(BaseMethod):
    """This method indicates that the sender wants to close the channel. This
    may be due to internal conditions (e.g. a forced shut-down) or due to an
    error handling a specific method, i.e. an exception. When a close is due to
    an exception, the sender provides the class and method id of the method
    which caused the exception.

    Arguments:
        reply_code: Short
        reply_text: Shortstr
        class_id: Short
        method_id: Short
    """
    method_type = (20, 40)

    field_info = (
        ("reply_code", types.Short),
        ("reply_text", types.Shortstr),
        ("class_id", types.Short),
        ("method_id", types.Short),
    )

    synchronous = True

    def __init__(self,
                 reply_code,
                 reply_text,
                 class_id,
                 method_id):
        super().__init__(
             reply_code,
             reply_text,
             class_id,
             method_id,
        )


class ChannelCloseOK(BaseMethod):
    """This method confirms a Channel.Close method and tells the recipient
    that it is safe to release resources for the channel.
    """
    method_type = (20, 41)

    field_info = ()

    synchronous = True


class ExchangeDeclare(BaseMethod):
    """This method creates an exchange if it does not already exist, and if
    the exchange exists, verifies that it is of the correct and expected class.

    Arguments:
        reserved_1: Short
        exchange: Shortstr
        type: Shortstr
        passive: Bit
        durable: Bit
        auto_delete: Bit
        internal: Bit
        no_wait: Bit
        arguments: Table
    """
    method_type = (40, 10)

    field_info = (
        ("reserved_1", types.Short),
        ("exchange", types.Shortstr),
        ("type", types.Shortstr),
        ("passive", types.Bit),
        ("durable", types.Bit),
        ("auto_delete", types.Bit),
        ("internal", types.Bit),
        ("no_wait", types.Bit),
        ("arguments", types.Table),
    )

    synchronous = True

    def __init__(self,
                 reserved_1,
                 exchange,
                 type,
                 passive,
                 durable,
                 auto_delete,
                 internal,
                 no_wait,
                 arguments):
        super().__init__(
             reserved_1,
             exchange,
             type,
             passive,
             durable,
             auto_delete,
             internal,
             no_wait,
             arguments,
        )


class ExchangeDeclareOK(BaseMethod):
    """This method confirms a Declare method and confirms the name of the
    exchange, essential for automatically-named exchanges.
    """
    method_type = (40, 11)

    field_info = ()

    synchronous = True


class ExchangeDelete(BaseMethod):
    """This method deletes an exchange. When an exchange is deleted all queue
    bindings on the exchange are cancelled.

    Arguments:
        reserved_1: Short
        exchange: Shortstr
        if_unused: Bit
        no_wait: Bit
    """
    method_type = (40, 20)

    field_info = (
        ("reserved_1", types.Short),
        ("exchange", types.Shortstr),
        ("if_unused", types.Bit),
        ("no_wait", types.Bit),
    )

    synchronous = True

    def __init__(self,
                 reserved_1,
                 exchange,
                 if_unused,
                 no_wait):
        super().__init__(
             reserved_1,
             exchange,
             if_unused,
             no_wait,
        )


class ExchangeDeleteOK(BaseMethod):
    """This method confirms the deletion of an exchange.
    """
    method_type = (40, 21)

    field_info = ()

    synchronous = True


class ExchangeBind(BaseMethod):
    """This method binds an exchange to an exchange.

    Arguments:
        reserved_1: Short
        destination: Shortstr
        source: Shortstr
        routing_key: Shortstr
        no_wait: Bit
        arguments: Table
    """
    method_type = (40, 30)

    field_info = (
        ("reserved_1", types.Short),
        ("destination", types.Shortstr),
        ("source", types.Shortstr),
        ("routing_key", types.Shortstr),
        ("no_wait", types.Bit),
        ("arguments", types.Table),
    )

    synchronous = True

    def __init__(self,
                 reserved_1,
                 destination,
                 source,
                 routing_key,
                 no_wait,
                 arguments):
        super().__init__(
             reserved_1,
             destination,
             source,
             routing_key,
             no_wait,
             arguments,
        )


class ExchangeBindOK(BaseMethod):
    """This method confirms that the bind was successful.
    """
    method_type = (40, 31)

    field_info = ()

    synchronous = True


class ExchangeUnbind(BaseMethod):
    """This method unbinds an exchange from an exchange.

    Arguments:
        reserved_1: Short
        destination: Shortstr
        source: Shortstr
        routing_key: Shortstr
        no_wait: Bit
        arguments: Table
    """
    method_type = (40, 40)

    field_info = (
        ("reserved_1", types.Short),
        ("destination", types.Shortstr),
        ("source", types.Shortstr),
        ("routing_key", types.Shortstr),
        ("no_wait", types.Bit),
        ("arguments", types.Table),
    )

    synchronous = True

    def __init__(self,
                 reserved_1,
                 destination,
                 source,
                 routing_key,
                 no_wait,
                 arguments):
        super().__init__(
             reserved_1,
             destination,
             source,
             routing_key,
             no_wait,
             arguments,
        )


class ExchangeUnbindOK(BaseMethod):
    """This method confirms that the unbind was successful.
    """
    method_type = (40, 51)

    field_info = ()

    synchronous = True


class QueueDeclare(BaseMethod):
    """This method creates or checks a queue. When creating a new queue the
    client can specify various properties that control the durability of the
    queue and its contents, and the level of sharing for the queue.

    Arguments:
        reserved_1: Short
        queue: Shortstr
        passive: Bit
        durable: Bit
        exclusive: Bit
        auto_delete: Bit
        no_wait: Bit
        arguments: Table
    """
    method_type = (50, 10)

    field_info = (
        ("reserved_1", types.Short),
        ("queue", types.Shortstr),
        ("passive", types.Bit),
        ("durable", types.Bit),
        ("exclusive", types.Bit),
        ("auto_delete", types.Bit),
        ("no_wait", types.Bit),
        ("arguments", types.Table),
    )

    synchronous = True

    def __init__(self,
                 reserved_1,
                 queue,
                 passive,
                 durable,
                 exclusive,
                 auto_delete,
                 no_wait,
                 arguments):
        super().__init__(
             reserved_1,
             queue,
             passive,
             durable,
             exclusive,
             auto_delete,
             no_wait,
             arguments,
        )


class QueueDeclareOK(BaseMethod):
    """This method confirms a Declare method and confirms the name of the
    queue, essential for automatically-named queues.

    Arguments:
        queue: Shortstr
        message_count: Long
        consumer_count: Long
    """
    method_type = (50, 11)

    field_info = (
        ("queue", types.Shortstr),
        ("message_count", types.Long),
        ("consumer_count", types.Long),
    )

    synchronous = True

    def __init__(self,
                 queue,
                 message_count,
                 consumer_count):
        super().__init__(
             queue,
             message_count,
             consumer_count,
        )


class QueueBind(BaseMethod):
    """This method binds a queue to an exchange. Until a queue is bound it
    will not receive any messages. In a classic messaging model,
    store-and-forward queues are bound to a direct exchange and subscription
    queues are bound to a topic exchange.

    Arguments:
        reserved_1: Short
        queue: Shortstr
        exchange: Shortstr
        routing_key: Shortstr
        no_wait: Bit
        arguments: Table
    """
    method_type = (50, 20)

    field_info = (
        ("reserved_1", types.Short),
        ("queue", types.Shortstr),
        ("exchange", types.Shortstr),
        ("routing_key", types.Shortstr),
        ("no_wait", types.Bit),
        ("arguments", types.Table),
    )

    synchronous = True

    def __init__(self,
                 reserved_1,
                 queue,
                 exchange,
                 routing_key,
                 no_wait,
                 arguments):
        super().__init__(
             reserved_1,
             queue,
             exchange,
             routing_key,
             no_wait,
             arguments,
        )


class QueueBindOK(BaseMethod):
    """This method confirms that the bind was successful.
    """
    method_type = (50, 21)

    field_info = ()

    synchronous = True


class QueueUnbind(BaseMethod):
    """This method unbinds a queue from an exchange.

    Arguments:
        reserved_1: Short
        queue: Shortstr
        exchange: Shortstr
        routing_key: Shortstr
        arguments: Table
    """
    method_type = (50, 50)

    field_info = (
        ("reserved_1", types.Short),
        ("queue", types.Shortstr),
        ("exchange", types.Shortstr),
        ("routing_key", types.Shortstr),
        ("arguments", types.Table),
    )

    synchronous = True

    def __init__(self,
                 reserved_1,
                 queue,
                 exchange,
                 routing_key,
                 arguments):
        super().__init__(
             reserved_1,
             queue,
             exchange,
             routing_key,
             arguments,
        )


class QueueUnbindOK(BaseMethod):
    """This method confirms that the unbind was successful.
    """
    method_type = (50, 51)

    field_info = ()

    synchronous = True


class QueuePurge(BaseMethod):
    """This method removes all messages from a queue which are not awaiting
    acknowledgment.

    Arguments:
        reserved_1: Short
        queue: Shortstr
        no_wait: Bit
    """
    method_type = (50, 30)

    field_info = (
        ("reserved_1", types.Short),
        ("queue", types.Shortstr),
        ("no_wait", types.Bit),
    )

    synchronous = True

    def __init__(self,
                 reserved_1,
                 queue,
                 no_wait):
        super().__init__(
             reserved_1,
             queue,
             no_wait,
        )


class QueuePurgeOK(BaseMethod):
    """This method confirms the purge of a queue.

    Arguments:
        message_count: Long
    """
    method_type = (50, 31)

    field_info = (
        ("message_count", types.Long),
    )

    synchronous = True

    def __init__(self,
                 message_count):
        super().__init__(
             message_count,
        )


class QueueDelete(BaseMethod):
    """This method deletes a queue. When a queue is deleted any pending
    messages are sent to a dead-letter queue if this is defined in the server
    configuration, and all consumers on the queue are cancelled.

    Arguments:
        reserved_1: Short
        queue: Shortstr
        if_unused: Bit
        if_empty: Bit
        no_wait: Bit
    """
    method_type = (50, 40)

    field_info = (
        ("reserved_1", types.Short),
        ("queue", types.Shortstr),
        ("if_unused", types.Bit),
        ("if_empty", types.Bit),
        ("no_wait", types.Bit),
    )

    synchronous = True

    def __init__(self,
                 reserved_1,
                 queue,
                 if_unused,
                 if_empty,
                 no_wait):
        super().__init__(
             reserved_1,
             queue,
             if_unused,
             if_empty,
             no_wait,
        )


class QueueDeleteOK(BaseMethod):
    """This method confirms the deletion of a queue.

    Arguments:
        message_count: Long
    """
    method_type = (50, 41)

    field_info = (
        ("message_count", types.Long),
    )

    synchronous = True

    def __init__(self,
                 message_count):
        super().__init__(
             message_count,
        )


class BasicQos(BaseMethod):
    """This method requests a specific quality of service. The QoS can be
    specified for the current channel or for all channels on the connection.
    The particular properties and semantics of a qos method always depend on
    the content class semantics. Though the qos method could in principle apply
    to both peers, it is currently meaningful only for the server.

    Arguments:
        prefetch_size: Long
        prefetch_count: Short
        global: Bit
    """
    method_type = (60, 10)

    field_info = (
        ("prefetch_size", types.Long),
        ("prefetch_count", types.Short),
        ("global", types.Bit),
    )

    synchronous = True

    def __init__(self,
                 prefetch_size,
                 prefetch_count,
                 global_):
        super().__init__(
             prefetch_size,
             prefetch_count,
             global_,
        )


class BasicQosOK(BaseMethod):
    """This method tells the client that the requested QoS levels could be
    handled by the server. The requested QoS applies to all active consumers
    until a new QoS is defined.
    """
    method_type = (60, 11)

    field_info = ()

    synchronous = True


class BasicConsume(BaseMethod):
    """This method asks the server to start a "consumer", which is a transient
    request for messages from a specific queue. Consumers last as long as the
    channel they were declared on, or until the client cancels them.

    Arguments:
        reserved_1: Short
        queue: Shortstr
        consumer_tag: Shortstr
        no_local: Bit
        no_ack: Bit
        exclusive: Bit
        no_wait: Bit
        arguments: Table
    """
    method_type = (60, 20)

    field_info = (
        ("reserved_1", types.Short),
        ("queue", types.Shortstr),
        ("consumer_tag", types.Shortstr),
        ("no_local", types.Bit),
        ("no_ack", types.Bit),
        ("exclusive", types.Bit),
        ("no_wait", types.Bit),
        ("arguments", types.Table),
    )

    synchronous = True

    def __init__(self,
                 reserved_1,
                 queue,
                 consumer_tag,
                 no_local,
                 no_ack,
                 exclusive,
                 no_wait,
                 arguments):
        super().__init__(
             reserved_1,
             queue,
             consumer_tag,
             no_local,
             no_ack,
             exclusive,
             no_wait,
             arguments,
        )


class BasicConsumeOK(BaseMethod):
    """The server provides the client with a consumer tag, which is used by
    the client for methods called on the consumer at a later stage.

    Arguments:
        consumer_tag: Shortstr
    """
    method_type = (60, 21)

    field_info = (
        ("consumer_tag", types.Shortstr),
    )

    synchronous = True

    def __init__(self,
                 consumer_tag):
        super().__init__(
             consumer_tag,
        )


class BasicCancel(BaseMethod):
    """This method cancels a consumer. This does not affect already delivered
    messages, but it does mean the server will not send any more messages for
    that consumer. The client may receive an arbitrary number of messages in
    between sending the cancel method and receiving the cancel-ok reply. It may
    also be sent from the server to the client in the event of the consumer
    being unexpectedly cancelled (i.e. cancelled for any reason other than the
    server receiving the corresponding basic.cancel from the client). This
    allows clients to be notified of the loss of consumers due to events such
    as queue deletion. Note that as it is not a MUST for clients to accept this
    method from the client, it is advisable for the broker to be able to
    identify those clients that are capable of accepting the method, through
    some means of capability negotiation.

    Arguments:
        consumer_tag: Shortstr
        no_wait: Bit
    """
    method_type = (60, 30)

    field_info = (
        ("consumer_tag", types.Shortstr),
        ("no_wait", types.Bit),
    )

    synchronous = True

    def __init__(self,
                 consumer_tag,
                 no_wait):
        super().__init__(
             consumer_tag,
             no_wait,
        )


class BasicCancelOK(BaseMethod):
    """This method confirms that the cancellation was completed.

    Arguments:
        consumer_tag: Shortstr
    """
    method_type = (60, 31)

    field_info = (
        ("consumer_tag", types.Shortstr),
    )

    synchronous = True

    def __init__(self,
                 consumer_tag):
        super().__init__(
             consumer_tag,
        )


class BasicPublish(BaseMethod):
    """This method publishes a message to a specific exchange. The message
    will be routed to queues as defined by the exchange configuration and
    distributed to any active consumers when the transaction, if any, is
    committed.

    Arguments:
        reserved_1: Short
        exchange: Shortstr
        routing_key: Shortstr
        mandatory: Bit
        immediate: Bit
    """
    method_type = (60, 40)

    field_info = (
        ("reserved_1", types.Short),
        ("exchange", types.Shortstr),
        ("routing_key", types.Shortstr),
        ("mandatory", types.Bit),
        ("immediate", types.Bit),
    )

    synchronous = False

    def __init__(self,
                 reserved_1,
                 exchange,
                 routing_key,
                 mandatory,
                 immediate):
        super().__init__(
             reserved_1,
             exchange,
             routing_key,
             mandatory,
             immediate,
        )


class BasicReturn(BaseMethod):
    """This method returns an undeliverable message that was published with
    the "immediate" flag set, or an unroutable message published with the
    "mandatory" flag set. The reply code and text provide information about the
    reason that the message was undeliverable.

    Arguments:
        reply_code: Short
        reply_text: Shortstr
        exchange: Shortstr
        routing_key: Shortstr
    """
    method_type = (60, 50)

    field_info = (
        ("reply_code", types.Short),
        ("reply_text", types.Shortstr),
        ("exchange", types.Shortstr),
        ("routing_key", types.Shortstr),
    )

    synchronous = False

    def __init__(self,
                 reply_code,
                 reply_text,
                 exchange,
                 routing_key):
        super().__init__(
             reply_code,
             reply_text,
             exchange,
             routing_key,
        )


class BasicDeliver(BaseMethod):
    """This method delivers a message to the client, via a consumer. In the
    asynchronous message delivery model, the client starts a consumer using the
    Consume method, then the server responds with Deliver methods as and when
    messages arrive for that consumer.

    Arguments:
        consumer_tag: Shortstr
        delivery_tag: Longlong
        redelivered: Bit
        exchange: Shortstr
        routing_key: Shortstr
    """
    method_type = (60, 60)

    field_info = (
        ("consumer_tag", types.Shortstr),
        ("delivery_tag", types.Longlong),
        ("redelivered", types.Bit),
        ("exchange", types.Shortstr),
        ("routing_key", types.Shortstr),
    )

    synchronous = False

    def __init__(self,
                 consumer_tag,
                 delivery_tag,
                 redelivered,
                 exchange,
                 routing_key):
        super().__init__(
             consumer_tag,
             delivery_tag,
             redelivered,
             exchange,
             routing_key,
        )


class BasicGet(BaseMethod):
    """This method provides a direct access to the messages in a queue using a
    synchronous dialogue that is designed for specific types of application
    where synchronous functionality is more important than performance.

    Arguments:
        reserved_1: Short
        queue: Shortstr
        no_ack: Bit
    """
    method_type = (60, 70)

    field_info = (
        ("reserved_1", types.Short),
        ("queue", types.Shortstr),
        ("no_ack", types.Bit),
    )

    synchronous = True

    def __init__(self,
                 reserved_1,
                 queue,
                 no_ack):
        super().__init__(
             reserved_1,
             queue,
             no_ack,
        )


class BasicGetOK(BaseMethod):
    """This method delivers a message to the client following a get method. A
    message delivered by 'get-ok' must be acknowledged unless the no-ack option
    was set in the get method.

    Arguments:
        delivery_tag: Longlong
        redelivered: Bit
        exchange: Shortstr
        routing_key: Shortstr
        message_count: Long
    """
    method_type = (60, 71)

    field_info = (
        ("delivery_tag", types.Longlong),
        ("redelivered", types.Bit),
        ("exchange", types.Shortstr),
        ("routing_key", types.Shortstr),
        ("message_count", types.Long),
    )

    synchronous = True

    def __init__(self,
                 delivery_tag,
                 redelivered,
                 exchange,
                 routing_key,
                 message_count):
        super().__init__(
             delivery_tag,
             redelivered,
             exchange,
             routing_key,
             message_count,
        )


class BasicGetEmpty(BaseMethod):
    """This method tells the client that the queue has no messages available
    for the client.

    Arguments:
        reserved_1: Shortstr
    """
    method_type = (60, 72)

    field_info = (
        ("reserved_1", types.Shortstr),
    )

    synchronous = True

    def __init__(self,
                 reserved_1):
        super().__init__(
             reserved_1,
        )


class BasicAck(BaseMethod):
    """When sent by the client, this method acknowledges one or more messages
    delivered via the Deliver or Get-Ok methods. When sent by server, this
    method acknowledges one or more messages published with the Publish method
    on a channel in confirm mode. The acknowledgement can be for a single
    message or a set of messages up to and including a specific message.

    Arguments:
        delivery_tag: Longlong
        multiple: Bit
    """
    method_type = (60, 80)

    field_info = (
        ("delivery_tag", types.Longlong),
        ("multiple", types.Bit),
    )

    synchronous = False

    def __init__(self,
                 delivery_tag,
                 multiple):
        super().__init__(
             delivery_tag,
             multiple,
        )


class BasicReject(BaseMethod):
    """This method allows a client to reject a message. It can be used to
    interrupt and cancel large incoming messages, or return untreatable
    messages to their original queue.

    Arguments:
        delivery_tag: Longlong
        requeue: Bit
    """
    method_type = (60, 90)

    field_info = (
        ("delivery_tag", types.Longlong),
        ("requeue", types.Bit),
    )

    synchronous = False

    def __init__(self,
                 delivery_tag,
                 requeue):
        super().__init__(
             delivery_tag,
             requeue,
        )


class BasicRecoverAsync(BaseMethod):
    """This method asks the server to redeliver all unacknowledged messages on
    a specified channel. Zero or more messages may be redelivered. This method
    is deprecated in favour of the synchronous Recover/Recover-Ok.

    Arguments:
        requeue: Bit
    """
    method_type = (60, 100)

    field_info = (
        ("requeue", types.Bit),
    )

    synchronous = False

    def __init__(self,
                 requeue):
        super().__init__(
             requeue,
        )


class BasicRecover(BaseMethod):
    """This method asks the server to redeliver all unacknowledged messages on
    a specified channel. Zero or more messages may be redelivered. This method
    replaces the asynchronous Recover.

    Arguments:
        requeue: Bit
    """
    method_type = (60, 110)

    field_info = (
        ("requeue", types.Bit),
    )

    synchronous = False

    def __init__(self,
                 requeue):
        super().__init__(
             requeue,
        )


class BasicRecoverOK(BaseMethod):
    """This method acknowledges a Basic.Recover method.
    """
    method_type = (60, 111)

    field_info = ()

    synchronous = True


class BasicNack(BaseMethod):
    """This method allows a client to reject one or more incoming messages. It
    can be used to interrupt and cancel large incoming messages, or return
    untreatable messages to their original queue. This method is also used by
    the server to inform publishers on channels in confirm mode of unhandled
    messages. If a publisher receives this method, it probably needs to
    republish the offending messages.

    Arguments:
        delivery_tag: Longlong
        multiple: Bit
        requeue: Bit
    """
    method_type = (60, 120)

    field_info = (
        ("delivery_tag", types.Longlong),
        ("multiple", types.Bit),
        ("requeue", types.Bit),
    )

    synchronous = False

    def __init__(self,
                 delivery_tag,
                 multiple,
                 requeue):
        super().__init__(
             delivery_tag,
             multiple,
             requeue,
        )


class TxSelect(BaseMethod):
    """This method sets the channel to use standard transactions. The client
    must use this method at least once on a channel before using the Commit or
    Rollback methods.
    """
    method_type = (90, 10)

    field_info = ()

    synchronous = True


class TxSelectOK(BaseMethod):
    """This method confirms to the client that the channel was successfully
    set to use standard transactions.
    """
    method_type = (90, 11)

    field_info = ()

    synchronous = True


class TxCommit(BaseMethod):
    """This method commits all message publications and acknowledgments
    performed in the current transaction. A new transaction starts immediately
    after a commit.
    """
    method_type = (90, 20)

    field_info = ()

    synchronous = True


class TxCommitOK(BaseMethod):
    """This method confirms to the client that the commit succeeded. Note that
    if a commit fails, the server raises a channel exception.
    """
    method_type = (90, 21)

    field_info = ()

    synchronous = True


class TxRollback(BaseMethod):
    """This method abandons all message publications and acknowledgments
    performed in the current transaction. A new transaction starts immediately
    after a rollback. Note that unacked messages will not be automatically
    redelivered by rollback; if that is required an explicit recover call
    should be issued.
    """
    method_type = (90, 30)

    field_info = ()

    synchronous = True


class TxRollbackOK(BaseMethod):
    """This method confirms to the client that the rollback succeeded. Note
    that if an rollback fails, the server raises a channel exception.
    """
    method_type = (90, 31)

    field_info = ()

    synchronous = True


class ConfirmSelect(BaseMethod):
    """This method sets the channel to use publisher acknowledgements. The
    client can only use this method on a non-transactional channel.

    Arguments:
        nowait: Bit
    """
    method_type = (85, 10)

    field_info = (
        ("nowait", types.Bit),
    )

    synchronous = True

    def __init__(self,
                 nowait):
        super().__init__(
             nowait,
        )


class ConfirmSelectOK(BaseMethod):
    """This method confirms to the client that the channel was successfully
    set to use publisher acknowledgements.
    """
    method_type = (85, 11)

    field_info = ()

    synchronous = True


# Method type -> class dispatch table
METHODS = {
    (10, 10): ConnectionStart,
    (10, 11): ConnectionStartOK,
    (10, 20): ConnectionSecure,
    (10, 21): ConnectionSecureOK,
    (10, 30): ConnectionTune,
    (10, 31): ConnectionTuneOK,
    (10, 40): ConnectionOpen,
    (10, 41): ConnectionOpenOK,
    (10, 50): ConnectionClose,
    (10, 51): ConnectionCloseOK,
    (20, 10): ChannelOpen,
    (20, 11): ChannelOpenOK,
    (20, 20): ChannelFlow,
    (20, 21): ChannelFlowOK,
    (20, 40): ChannelClose,
    (20, 41): ChannelCloseOK,
    (40, 10): ExchangeDeclare,
    (40, 11): ExchangeDeclareOK,
    (40, 20): ExchangeDelete,
    (40, 21): ExchangeDeleteOK,
    (40, 30): ExchangeBind,
    (40, 31): ExchangeBindOK,
    (40, 40): ExchangeUnbind,
    (40, 51): ExchangeUnbindOK,
    (50, 10): QueueDeclare,
    (50, 11): QueueDeclareOK,
    (50, 20): QueueBind,
    (50, 21): QueueBindOK,
    (50, 50): QueueUnbind,
    (50, 51): QueueUnbindOK,
    (50, 30): QueuePurge,
    (50, 31): QueuePurgeOK,
    (50, 40): QueueDelete,
    (50, 41): QueueDeleteOK,
    (60, 10): BasicQos,
    (60, 11): BasicQosOK,
    (60, 20): BasicConsume,
    (60, 21): BasicConsumeOK,
    (60, 30): BasicCancel,
    (60, 31): BasicCancelOK,
    (60, 40): BasicPublish,
    (60, 50): BasicReturn,
    (60, 60): BasicDeliver,
    (60, 70): BasicGet,
    (60, 71): BasicGetOK,
    (60, 72): BasicGetEmpty,
    (60, 80): BasicAck,
    (60, 90): BasicReject,
    (60, 100): BasicRecoverAsync,
    (60, 110): BasicRecover,
    (60, 111): BasicRecoverOK,
    (60, 120): BasicNack,
    (90, 10): TxSelect,
    (90, 11): TxSelectOK,
    (90, 20): TxCommit,
    (90, 21): TxCommitOK,
    (90, 30): TxRollback,
    (90, 31): TxRollbackOK,
    (85, 10): ConfirmSelect,
    (85, 11): ConfirmSelectOK,
}


# Constants
FRAME_METHOD = 1
FRAME_HEADER = 2
FRAME_BODY = 3
FRAME_HEARTBEAT = 8
FRAME_MIN_SIZE = 4096
FRAME_END = 206
REPLY_SUCCESS = 200
CONTENT_TOO_LARGE = 311
NO_CONSUMERS = 313
CONNECTION_FORCED = 320
INVALID_PATH = 402
ACCESS_REFUSED = 403
NOT_FOUND = 404
RESOURCE_LOCKED = 405
PRECONDITION_FAILED = 406
FRAME_ERROR = 501
SYNTAX_ERROR = 502
COMMAND_INVALID = 503
CHANNEL_ERROR = 504
UNEXPECTED_FRAME = 505
RESOURCE_ERROR = 506
NOT_ALLOWED = 530
NOT_IMPLEMENTED = 540
INTERNAL_ERROR = 541
