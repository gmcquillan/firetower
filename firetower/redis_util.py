"""
redis_util
----------

the main queue handler for firetower.
"""
from heapq import heappush, merge

import redis
from redis.exceptions import ConnectionError

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


class _Redis(redis.Redis):
    pass

def get_redis_conn(host, port, redis_db=1):
    try:
        conn = _Redis(
            host=host, port=port, db=redis_db)
        conn.ping()
    except ConnectionError:
        conn = MockRedis()
    return conn
