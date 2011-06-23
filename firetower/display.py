import pprint
import datetime
import time
import redis_util


class Display(object):

    def __init__(self):
        self.r = redis_util.Redis()

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


def main():
    display = Display()
    display.dump_data(['Test Error'])
