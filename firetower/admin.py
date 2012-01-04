from logbook import Logger
from logbook import TimeRotatingFileHandler
from optparse import OptionParser

import category
import classifier
import config
import redis_util


class Admin(object):
    """Administrative task object."""

    def __init__(conf):
        """conf: dict, yaml parameters."""
        self.conf = conf
        handler = TimedRotatingFileHandler(
            conf.log_file, date_format='%Y-%m-%d')
        handler.push_application()
        self.logger = Logger('Firetower-admin')
        self.queue = redis_util.get_redis_conn(
            host=conf.redis_host, port=conf.redis_port, redis_db=conf.redis_db
        )
        self.classifier = classifier.Levenschtein()

    def calc_stats():
        """Calculate and save mean and standard deviation."""

        categories = category.Category.get_all_categories(self.queue)
        for cat in self.categories:
            all_events = cat.events.range(0, -1)
            ratios = []
            for event in all_events:
                ratios.append(
                        self.classifier.str_ratio(cat.signature, event['sig']))
            ratio_array = numpy.array(ratios)
            cat.stdev = ratio_array.std()
            cat.mean = ratio_array.mean()

    def run(options, args):
        """Run set of jobs specified on commandline or config."""
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
