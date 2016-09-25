"""
amqpframe.errors
~~~~~~~~~~~~~~~~

AMQP errors classes.

This file was generated 2016-08-29 from
/codegen/amqp0-9-1.extended.xml.

"""
# Some exceptions may shadow builtins.
# pylint: disable=redefined-builtin


class Error(Exception):
    """Base class for all AMQP errors."""
    code = None


class SoftError(Error):
    """Soft errors are recoverable which means if such error happens,
    only the channel where the error happened closes, other channels
    can continue to operate.
    """


class HardError(Error):
    """Hard errors are not recoverable which means if such error happens,
    the whole connection must be closed as soon as possible.
    """


class ContentTooLarge(SoftError):
    """The client attempted to transfer content larger than the server could
    accept at the present time. The client may retry at a later time.
    """
    code = 311


class NoConsumers(SoftError):
    """When the exchange cannot deliver to a consumer when the immediate flag
    is set. As a result of pending data on the queue or the absence of any
    consumers of the queue.
    """
    code = 313


class ConnectionForced(HardError):
    """An operator intervened to close the connection for some reason. The
    client may retry at some later date.
    """
    code = 320


class InvalidPath(HardError):
    """The client tried to work with an unknown virtual host.
    """
    code = 402


class AccessRefused(SoftError):
    """The client attempted to work with a server entity to which it has no
    access due to security settings.
    """
    code = 403


class NotFound(SoftError):
    """The client attempted to work with a server entity that does not exist.
    """
    code = 404


class ResourceLocked(SoftError):
    """The client attempted to work with a server entity to which it has no
    access because another client is working with it.
    """
    code = 405


class PreconditionFailed(SoftError):
    """The client requested a method that was not allowed because some
    precondition failed.
    """
    code = 406


class FrameError(HardError):
    """The sender sent a malformed frame that the recipient could not decode.
    This strongly implies a programming error in the sending peer.
    """
    code = 501


class SyntaxError(HardError):
    """The sender sent a frame that contained illegal values for one or more
    fields. This strongly implies a programming error in the sending peer.
    """
    code = 502


class CommandInvalid(HardError):
    """The client sent an invalid sequence of frames, attempting to perform an
    operation that was considered invalid by the server. This usually implies a
    programming error in the client.
    """
    code = 503


class ChannelError(HardError):
    """The client attempted to work with a channel that had not been correctly
    opened. This most likely indicates a fault in the client layer.
    """
    code = 504


class UnexpectedFrame(HardError):
    """The peer sent a frame that was not expected, usually in the context of
    a content header and body. This strongly indicates a fault in the peer's
    content processing.
    """
    code = 505


class ResourceError(HardError):
    """The server could not complete the method because it lacked sufficient
    resources. This may be due to the client creating too many of some type of
    entity.
    """
    code = 506


class NotAllowed(HardError):
    """The client tried to work with some entity in a manner that is
    prohibited by the server, due to security settings or by some other
    criteria.
    """
    code = 530


class NotImplemented(HardError):
    """The client tried to use functionality that is not implemented in the
    server.
    """
    code = 540


class InternalError(HardError):
    """The server could not complete the method because of an internal error.
    The server may require intervention by an operator in order to resume
    normal operations.
    """
    code = 541
