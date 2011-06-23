import datetime
import json
import time

from optparse import OptionParser

import alerts
import config
from redis_util import Redis
import aggregator

class Main(object):
    """Main loop."""

    def run(self):
        parser = OptionParser(usage='usage: firetower options args')
        parser.add_option(
                '--conf', action='store', dest='conf_path',
                help='Path to YAML configuration file.')

        (options, args) = parser.parse_args()

        if len(args) > 1:
            parser.error('Please supply some arguments')

        conf = config.Config(options.conf_path)

        alert_time = None
        queue = Redis()
        aggr = aggregator.Aggregator()
        alert = alerts.Alert()
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
                aggr.consume(parsed)
            else:
                time.sleep(1)


def main():
    main = Main()
    main.run()
