"""
redis_util
----------

the main queue handler for firetower.
"""
from heapq import heappush
import time

import redis
from redis.exceptions import ConnectionError


class MockRedis(object):
    data = {}

    def hgetall(self, key):
        return self.data[key]

    def hincrby(self, root_key, sub_key, default):
        rhash = self.data.get(root_key, {})
        value = rhash.get(sub_key, 0)
        rhash[sub_key] = value + default
        self.data[root_key] = rhash

    def lpush(self, key, value):
        val_list = self.data.get(key, [])
        val_list.append(value)
        self.data[key] = val_list

    def rpop(self, key):
        val_list = self.data.get(key, [])
        if val_list:
            return val_list.pop(-1)
        else:
            return None

    def zadd(self, name, value, score):
        zheap = self.data.get(name, [])
        heappush(zheap, (score, value))
        self.data[name] = zheap


class Redis(object):

    def __init__(self):
        try:
            self.conn = redis.Redis(host='localhost', port=6379, db=0)
            self.conn.ping()
        except ConnectionError:
            self.conn = MockRedis()

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
