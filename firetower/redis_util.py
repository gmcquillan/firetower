"""
redis_util
----------

the main queue handler for firetower.
"""
import calendar
from heapq import heappush, merge
import json
import hashlib
import time

import redis
from redis.exceptions import ConnectionError

import category

class MockRedis(object):
    _data = {}

    def __init__(self, share_state=True):
        if share_state:
            self.data = self._data
        else:
            self.data = {}

    def hgetall(self, key):
        return self.data[key]

    def hincrby(self, root_key, sub_key, default):
        rhash = self.data.get(root_key, {})
        value = rhash.get(sub_key, 0)
        rhash[sub_key] = value + default
        self.data[root_key] = rhash

    def hget(self, root_key, sub_key):
        return self.data[root_key][sub_key]

    def hset(self, root_key, sub_key, value):
        rhash = self.data.get(root_key, {})
        rhash[sub_key] = value
        self.data[root_key] = rhash

    def hdel(self, root_key, sub_key):
        del self.data[root_key][sub_key]

    def keys(self):
        return self.data.keys()

    def llen(self, key):
        values = self.data.get(key, [])
        return len(values)

    def lpush(self, key, value):
        val_list = self.data.get(key, [])
        new = [value] + val_list
        val_list = new
        self.data[key] = val_list

    def lpop(self, key):
        val_list = self.data.get(key, [])
        if val_list:
            return val_list.pop(0)
        else:
            return None

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

    def _zrange_op(self, name, start, stop, reverse, withscores=False):
        zheap = self.data.get(name, [])
        if stop < 0:
            stop += len(zheap) + 1
        heap_list = list(merge(zheap))
        if reverse:
            heap_list.reverse()
        if withscores:
            return heap_list[start:stop]
        else:
            return [x[0] for x in heap_list]

    def zrange(self, name, start, stop, withscores=False):
        return self._zrange_op(name, start, stop, False, withscores=withscores)

    def zrevrange(self, name, start, stop, withscores=False):
        return self._zrange_op(name, start, stop, True, withscores=withscores)

    def zrevrangebyscore(self, name, stop, start, withscores=True):
        zheap = self.data.get(name, [])
        heap_list = list(merge(zheap))
        ret = []
        for score, value in heap_list:
            if score >= start and score <= stop:
                ret.append([score, value])
        if withscores:
            return ret
        else:
            return [x[0] for x in ret]
        return ret


class Redis(redis.Redis):
    pass

def get_redis_conn(host, port, redis_db=1):
    try:
        conn = Redis(
            host=host, port=port, db=redis_db)
        conn.ping()
    except ConnectionError:
        conn = MockRedis()
    return conn
#
#
#class Redis(object):
#    """Redis - Controls all Firetower interaction with Redis."""
#
#    def __init__(self, host, port, redis_db=1):
#        """Initialize Redis Connections.
#
#        Args:
#            conf: conf.Config obj, container for configuraton data
#        """
#        try:
#            self.conn = redis.Redis(
#                host=host, port=port, db=redis_db)
#            self.conn.ping()
#        except ConnectionError:
#            self.conn = MockRedis()
#
#
#
#    def len_incoming(self, key):
#        """Return the length of the incoming queue."""
#        return self.conn.llen(key)
#
#    def dump_incoming(self, key):
#        """Return the contents of the incoming list."""
#        return self.conn.lrange(key, 0, -1)
#
#    def get_counts(self, tracked_keys):
#        """
#        Return the hgetall for each tracked_key in a list.
#        redis keys are named queues
#        Values are {timestamp: count, ...}
#
#        returns something like {named_queue: { timestamp: count, ...}, ...}
#        """
#        error_counts = {}
#        for key in tracked_keys:
#            error_counts[key] = self.conn.hgetall(key)
#        return error_counts
#
#    def get_timeseries(self, category, start=None, end=time.time()):
#        """Get some timeseries counts per category.
#
#        Args:
#            category: str, category name.
#            start: int, epoch time to start query from.
#            end: int, epoch time to end query with.
#        Returns:
#            dict, keys are timestamps, and values are counts.
#        """
#        cat_id = self.construct_cat_id(category)
#        all_counts = self.conn.hgetall('counter_%s' % (cat_id,))
#        if start:
#            for key in all_counts.keys():
#                int_key = int(key)
#                if int_key < start or int_key > end:
#                    del all_counts[key]
#
#        return all_counts
#
#
#    def sum_timeslice_values(self, error_counts, timeslice, start=None):
#        """Return sum of all error instances within time_slice."""
#        if not start:
#            start = int(time.time())
#        end = start - timeslice
#        error_sums = {}
#        for queue, error_dict in error_counts.items():
#            error_sums[queue] = 0
#            for timestamp, count in error_dict.items():
#                thresh_start = int(end)
#                if timestamp > thresh_start:
#                    error_sums[queue] += int(count)
#        return error_sums
#
#    def incr_counter(self, cat_counter_id):
#        """Increment normalized count of errors by type."""
#        self.conn.hincrby(cat_counter_id, int(time.time()), 1)
#
#    def save_error(self, cat_data_id, error):
#        """Save JSON encoded string into proper bucket."""
#        ts = time.time() # our timestamp, needed for uniq
#        error['ts'] = ts
#        self.conn.zadd(cat_data_id,  json.dumps(error), ts)
#
#    def add_category(self, signature):
#        """Add category to our sorted set of categories."""
#        c = category.Category.create(self.conn, signature)
#
#    def get_category_from_id(self, id):
#        """Return the category name from a hash id.
#
#        Args:
#            id: str, hash id.
#        Returns:
#            str, category name.
#        """
#        return self.conn.hget('category_ids', "%s:category" %(id))
#
#    def get_threshold_from_id(self, id):
#        """Return the threshold from a hash id.
#
#        Args:
#            id: str, hash id.
#        Returns:
#            int, category threshold
#        """
#        thresh_str = self.conn.hget('category_ids', "%s:threshold" %(id))
#        if not thresh_str:
#            return None
#
#        try:
#            thresh = float(thresh_str)
#        except ValueError as e:
#            # TODO: Need some error handling/logging
#            raise e
#        else:
#            return thresh
#
#    def get_verbose_name_from_id(self, id):
#        verbose_name = self.conn.hget("category_ids", )
#
#
#    def get_categories(self):
#        """Retrieve the full category set."""
#        return self.conn.zrange('categories', 0, -1)
#
#    def add_unknown_error(self, error):
#        """Add an unknown error to our list."""
#        self.push('unknown_errors', json.dumps(error))
#
#    def get_unknown_errors(self):
#        """Generator to return one value from unknown_errors at a time."""
#        num = 0
#        while num < self.conn.llen('unknown_errors'):
#            yield self.pop('unknown_errors')
#            num += 1
#
#    def get_latest_data(self, category):
#        """Return list of the most recent json encoded errors for a category."""
#
#        cat_id = self.construct_cat_id(category) # Lookup by hash id
#        data_key = 'data_%s' % (cat_id,)
#        list_of_errors = self.conn.zrevrange(data_key, 0, 0)
#        if list_of_errors:
#            return list_of_errors
