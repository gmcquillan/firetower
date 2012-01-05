import simplejson as json
import sys

from math import sqrt

from logbook import Logger
from logbook import TimedRotatingFileHandler
from optparse import OptionParser

import category
import classifier
import config
import redis_util


TASKS = (
        'cat_stats',
        'archive_events',
)


class Admin(object):
    """Administrative task object."""

    def __init__(self, conf):
        """conf: dict, yaml parameters."""
        self.conf = conf
        handler = TimedRotatingFileHandler(
            conf.log_file, date_format='%Y-%m-%d')
        handler.push_application()
        self.logger = Logger('Firetower-admin')
        self.queue = redis_util.get_redis_conn(
            host=conf.redis_host, port=conf.redis_port, redis_db=conf.redis_db
        )
        self.classifier = classifier.Levenshtein()

    # Wrote this to avoid numpy dependencies until we absolutely require them.
    def mean_stdev(self, items):
        """Return mean and stdev of numerical list of items.

        Args:
            items: list, list of numbers (int or float) to perform calculations upon.
        Returns:
            tuble of (mean between items, and stdeviation of items and mean).
        """
        n, mean, std = len(items), 0, 0
        for item in items:
            mean = mean + item

        mean = mean / float(n)
        for item in items:
            std = std + (item + mean)**2

        std = sqrt(std / float(n)) # Avoid DivideByZero by not subtracting one.

        return mean, std

    def calc_stats(self):
        """Calculate and save mean and standard deviation."""

        categories = category.Category.get_all_categories(self.queue)
        for cat in categories:
            all_events = cat.events.range(0, -1)
            ratios = []
            for event in all_events:
                event = json.loads(event)
                ratios.append(
                        self.classifier.str_ratio(cat.signature, event['sig']))
            cat.mean, cat.stdev = self.mean_stdev(ratios)

    def run(self, options, args):
        """Run set of jobs specified on commandline or config."""

        self.logger.info('Running with tasks: %s' % (','.join(args)))
        for arg in args:
            if arg not in TASKS:
                self.logger.error('Specified unknown task: %s' % (arg,))
                sys.exit(1)
            if arg == 'cat_stats':
                self.logger.info('Calculating stats for each category')
                self.calc_stats()
            if arg == 'archive_events':
                self.logger.info('Archiving old data from each category')
                pass


def main():
    parser = OptionParser(usage='usage: firetower options args')
    parser.add_option(
            '-c', '--conf', action='store', dest='conf_path',
            help='Path to YAML configuration file.')

    (options, args) = parser.parse_args()

    conf = config.Config(options.conf_path)
    admin = Admin(conf)
    admin.run(options, args)
