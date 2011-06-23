"""
redis_util
----------

the main queue handler for firetower.
"""

import redis
import time


class Redis(object):

    def __init__(self):
        self.conn = redis.Redis(host='localhost', port=6379, db=0)

    def pop(self, key):
        return self.conn.rpop(key)

    def push(self, key, value):
        self.conn.lpush(key, value)

    def get_counts(self, tracked_keys):
        """
        Return the hgetall for each tracked_key in a list.
        redis keys are named queues
        Values are {timestamp: count, ...}

        returns something like {named_queue: { timestamp: count, ...}, ...}
        """
        error_counts = {}
        for key in tracked_keys:
            error_counts[key] = self.conn.hgetall(key)
        return error_counts

    def sum_timeslice_values(self, error_counts, timeslice, start=None):
        """Return sum of all error instances within time_slice."""
        #XXX:dc: what are the error_counts a list of?
        if not start:
            start = int(time.time())
        end = start - timeslice
        error_sums = {}
        for queue, error_dict in error_counts.items():
            error_sums[queue] = 0
            for timestamp, count in error_dict.items():
                thresh_start = int(end)
                if timestamp > thresh_start:
                    error_sums[queue] += count
        return error_sums
