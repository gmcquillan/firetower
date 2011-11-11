import simplejson as json

from logbook import Logger
from logbook import TimedRotatingFileHandler

from firetower import config
from firetower import redis_util

handler = TimedRotatingFileHandler('firetower-client.log',
        date_format='%Y-%m-%d')
handler.push_application()
log = Logger('Firetower-client')

class Client(object):
    """Basic Firetower Client."""

    def __init__(self, conf):
        self.conf = config.Config(conf)
        self.redis_host = self.conf.redis_host
        self.redis_port = self.conf.redis_port
        self.queue_key = self.conf.queue_key
        self.queue = redis_util.Redis(host=self.redis_host, port=self.redis_port)

    def emit(self, event):
        """Emit a message to firetower.

        Args:
            event: str or dict.

            if we cannot parse as json, we convert it to a simple JSON struct:
            {'sig': <event payload>}.
        """
        try:
            unencoded = json.loads(event)
            if not unencoded.get("sig", None):
                raise ValueError
        except ValueError:
            payload = {"sig": event}
            event = json.dumps(payload)

        self.queue.push(self.queue_key, event)
        log.debug("Pushed event %s to firetower" % (event,))
