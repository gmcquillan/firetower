import datetime
import json
import sys
import time

from logbook import Logger
from logbook import TimedRotatingFileHandler
from optparse import OptionParser

import alerts
import config
import classifier
import category
import redis_util


class Main(object):
    """Main loop."""

    def run(self):
        parser = OptionParser(usage='usage: firetower options args')
        parser.add_option(
                '-c', '--conf', action='store', dest='conf_path',
                help='Path to YAML configuration file.')

        (options, args) = parser.parse_args()

        conf = config.Config(options.conf_path)
        handler = TimedRotatingFileHandler(conf.log_file,
                date_format='%Y-%m-%d')
        handler.push_application()
        log = Logger('Firetower-server')
        log.info('Started server with configuration file %s' % (options.conf_path))

        alert_time = None
        queue = redis_util.Redis(
                host=conf.redis_host,
                port=conf.redis_port,
                redis_db=conf.redis_db)

        cls = classifier.Levenshtein(queue)
        alert = alerts.Alert(queue)
        last_archive = datetime.datetime.utcnow()
        while 1:
            now = datetime.datetime.utcnow()
            err = queue.pop(conf.queue_key)
            if last_archive < now - datetime.timedelta(seconds=conf.archive_time):
                log.debug('Archiving counts older than %s seconds' % (conf.archive_time,))
                for c in category.Category.get_all_categories(queue.conn):
                    log.debug('Archiving for %s category' % (c.cat_id))
                    category.TimeSeries.archive_cat_counts(
                        queue.conn, c.cat_id, last_archive)
                last_archive = now
            if err:
                parsed = json.loads(err)
                cls.classify(parsed, conf.class_thresh)
            else:
                time.sleep(1)


def main():
    main = Main()
    main.run()
