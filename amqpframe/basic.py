import enum
import datetime
import collections

from . import types

PROPERTIES = (
    ('content_type', types.Shortstr),
    ('content_encoding', types.Shortstr),
    ('headers', types.Table),
    ('delivery_mode', types.Octet),
    ('priority', types.Octet),
    ('correlation_id', types.Shortstr),
    ('reply_to', types.Shortstr),
    ('expiration', types.Shortstr),
    ('message_id', types.Shortstr),
    ('timestamp', types.Timestamp),
    ('type', types.Shortstr),
    ('user_id', types.Shortstr),
    ('app_id', types.Shortstr),
)


class Message:
    PROPERTIES = PROPERTIES

    class DeliveryMode(enum.Enum):
        NonPersistent = 1
        Persistent = 2

    def __init__(self, body, *,
                 content_type: str='application/octet-stream',
                 content_encoding: str='utf-8',
                 headers: dict=None,
                 delivery_mode: DeliveryMode=None,
                 priority: int=None,
                 correlation_id: str=None,
                 reply_to: str=None,
                 expiration: str=None,
                 message_id: str=None,
                 timestamp: datetime.datetime=None,
                 type: str=None,
                 user_id: str=None,
                 app_id: str=None):
        if isinstance(body, bytes):
            self.body = body
        else:
            self.body = body.encode(content_encoding)

        if timestamp is None:
            timestamp = datetime.datetime.utcnow()

        # Too lazy to manually specify all names :)
        _locals = locals()
        self.properties = collections.OrderedDict()
        for name, amqptype in self.PROPERTIES:
            value = _locals[name]
            if value is not None:
                value = amqptype(value)
            self.properties[name] = value
