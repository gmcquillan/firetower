import pprint
import datetime
import time
from optparse import OptionParser

import config
from redis_util import Redis

class Display(object):

    def __init__(self, conf):
        self.r = Redis(conf.redis_host, conf.redis_port)
        self.conf = conf

    def dump_data(self, tracked_keys):
        counts = self.r.get_counts(tracked_keys)
        pprint.pprint(counts)
        lastlogs = []
        log_keys = self.r.conn.keys()
        print "These are the log_keys"
        pprint.pprint(log_keys)
        for key in log_keys:
            #Because we don't want to regurgitate the count keys
            data_key = 'data_%' % (key,)
            if data_key in tracked_keys:
                last_hour = time.time() - datetime.timedelta(minutes=60)
                error_data = self.r.conn.zrangebyscore(
                        data_key, last_hour, "inf", limit=1, withscores=True)
                lastlogs.append(error_data)

        pprint.pprint(lastlogs)

    def dump_incoming(self):
        """Display length of incoming queue and its contents."""
        print 'Incoming queue length: ', self.r.len_incoming(self.conf.queue_key)
        print self.r.dump_incoming(self.conf.queue_key)


def main():
    parser = OptionParser(usage='usage: firetower options args')
    parser.add_option(
        '-c', '--conf', action='store', dest='conf_path',
         help='Path to YAML configuration file.')

    (options, args) = parser.parse_args()

    conf = config.Config(options.conf_path)

    display = Display(conf)
    #display.dump_data(['Test Error'])
    display.dump_incoming()
