import datetime
import json
import sys
import time

from optparse import OptionParser

import alerts
import config
import classifier
from redis_util import Redis

class Main(object):
    """Main loop."""

    def run(self):
        parser = OptionParser(usage='usage: firetower options args')
        parser.add_option(
                '-c', '--conf', action='store', dest='conf_path',
                help='Path to YAML configuration file.')

        (options, args) = parser.parse_args()

        conf = config.Config(options.conf_path)

        alert_time = None
        queue = Redis(host=conf.redis_host, port=conf.redis_port)
        cls = classifier.Levenshtein(queue)
        alert = alerts.Alert(queue)
        while 1:
            now = datetime.datetime.now()
            err = queue.pop(conf.queue_key)
            if not alert_time:
                alert_time = datetime.timedelta(minutes=conf.alert_time) + now
            elif alert_time < now:
                alert.check(conf.error_signatures, conf.timeslices)
                alert_time = datetime.timedelta(minutes=conf.alert_time) + now
            if err:
                parsed = json.loads(err)
                cls.classify(parsed)
            else:
                time.sleep(1)


def main():
    main = Main()
    main.run()
