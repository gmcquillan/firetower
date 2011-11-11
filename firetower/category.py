import calendar
from collections import namedtuple
import re

import redis_util

TSTuple = namedtuple("TimeSeriesTuple", ("timestamp", "count"))

class TimeSeries(object):
    def __init__(self, redis_conn, cat_id):
        """Create a time series instance for a category

        This object exposes the time series data stored in the sorted set
        ts_{cat_id}.

        """
        self.cat_id = cat_id
        self.redis_conn = redis_conn

    def convert_ts_list(self, ts_list):
        """Process lists from timeseries sorted sets.

        Takes a list of scores and values from a time series sorted set and
        return a list of entries in the form ({TIMESTAMP}, {COUNT}). This is
        required because the TS sorted set doesn't hold the raw count, to make
        the values unique it stores them as '{TIMESTAMP}:{COUNT}'

        """
        ret = []
        for ts_entry in ts_list:
            ret.append(
                TSTuple(
                    int(ts_entry[1]),
                    int(ts_entry[0].split(":")[1])
                )
            )
        return ret

    def all(self):
        """Return all timeseries data for the category.

        The data will be returned as a sequence of sequences.
        Each sub-sequence is of the form (VALUE, TIMESTAMP) where TIMESTAMP is
        a number of seconds since epoch and VALUE is the number of times the
        category appeared in that second.
        """
        return self.convert_ts_list(self.redis_conn.zrange(
            "ts_%s" % (self.cat_id), 0, -1, withscores=True
        ))

    def range(self, start, end):
        """Return all timeseries data for the category between start and end.

        start and end are assumed to be seconds since the epoch.

        The data will be returned as a sequence of sequences.
        Each sub-sequence is of the form (VALUE, TIMESTAMP) where TIMESTAMP is
        a number of seconds since epoch and VALUE is the number of times the
        category appeared in that second.
        """
        return self.convert_ts_list(self.redis_conn.zrevrangebyscore(
            "ts_%s" % (self.cat_id), end, start, withscores=True
        ))

    @staticmethod
    def generate_ts_value(ts, count):
        """Turn a timestamp and cat count into a value for storage in a set"""
        return "%s:%s" % (ts, count)

    @classmethod
    def archive_cat_counts(cls, conn, cat_id, start_time):
        """Move everything before start_time into a Sorted Set.

        Args:
            conn: Redis connection
            cat_id: The category hash ID
            start_time: int, epoch time.
        """
        ts_key = 'ts_%s' % (cat_id,)
        counter_key = 'counter_%s' % (cat_id,)
        counts = conn.hgetall(counter_key)
        counters_to_delete = []
        for ts in counts:
            if int(ts) < calendar.timegm(start_time.timetuple()):
                conn.zadd(ts_key, cls.generate_ts_value(ts, counts[ts]), ts)
                counters_to_delete.append(ts)

        # Remove the counters from the 'counter' key.
        # We store longterm counters in the timeseries key (ts).
        for counter in counters_to_delete:
            conn.hdel(counter_key, counter)


class Events(object):
    def __init__(self, redis_conn, cat_id):
        self.cat_id = cat_id
        self.redis_conn = redis_conn

    def last_x(self, count):
        self.redis_conn.zrevrange(
            "data_%s" % self.cat_id, 0, count
        )

    def _backfill_timeseries(self, delete=False):
        """This is for pulling data out an event stream and putting in ts.

        Args:
            delete: bool, whether or not to delete the archived ts.
        """
        # Not sure this is an ideal solution, since it depends on archiving
        # to work properly, which may be why we're backfilling in the
        # first place.
        events = self.redis_conn.zrange(
                "data_" % self.cat_id, 0, -1, withscores=True)
        cat_counter_id = "counter_%s" % (self.cat_id,)
        cat_ts_id = "ts_%s" % (self.cat_id,)
        if delete:
            self.redis_conn.delete(cat_ts_id)
        for _sig, ts in events:
            self.redis_conn.hincrby(cat_counter_id, int(ts), 1)


class Category(object):
    """A class to encapsulate operations involving categories and their metadata

    Currently exposes 3 read/write properties: signature, human_name and
    threshold.

    """

    CAT_META_HASH = "category_ids"
    SIGNATURE_KEY = "signature"
    HUMAN_NAME_KEY = "human_name"
    THRESHOLD_KEY = "threshold"

    def __init__(self, redis_conn, signature=None, cat_id=None):
        self.conn = redis_conn

        if signature:
            self.cat_id = redis_util.Redis.construct_cat_id(signature)
        elif cat_id:
            self.cat_id = cat_id
        else:
            self.cat_id = None

        if self.cat_id:
            self.timeseries = TimeSeries(redis_conn, self.cat_id)
            self.events = Events(redis_conn, self.cat_id)

    def to_dict(self):
        return {
            self.SIGNATURE_KEY: self.signature,
            self.HUMAN_NAME_KEY: self.human_name,
            self.THRESHOLD_KEY: self.threshold,
        }

    @classmethod
    def create(cls, redis_conn, signature):
        """Adds category metadata.

        This method will set 3 metadata fields for the category hash:
        * category is the full text of the original cateory.
        * verbose_name is the human readable name for this category (used for
            display purposes)
        * threshold is the custom threshold for this category

        The key values are in the form {category_hash}:{metadata_name} e.g.
        a909ede39c09d84ed1839c5ca0f9b9876113770b:category
        """
        redis_conn.zadd("categories", signature, 0)
        cat_id = redis_util.Redis.construct_cat_id(signature)
        cat_fields = (
            (cls.SIGNATURE_KEY, signature), (cls.HUMAN_NAME_KEY, cat_id),
            (cls.THRESHOLD_KEY, ""),
        )
        for key, value in cat_fields:
            redis_conn.hset(cls.CAT_META_HASH, "%s:%s" %(cat_id, key), value)

        return cls(redis_conn, cat_id=cat_id)

    @classmethod
    def get_all_categories(cls, redis_conn):
        """Return a list of all currently defined categories"""
        categories = []
        hash_map = redis_conn.hgetall(cls.CAT_META_HASH)
        for key in hash_map:
            if key.endswith(cls.SIGNATURE_KEY):
                categories.append(cls(
                    redis_conn,
                    cat_id=key.replace(":" + cls.SIGNATURE_KEY, "")
                ))
        return categories

    def _get_key(self, key):
        return self.conn.hget(
            self.CAT_META_HASH, "%s:%s" %(self.cat_id, key)
        )

    def _set_key(self, key, value):
        return self.conn.hset(
            self.CAT_META_HASH, "%s:%s" %(self.cat_id, key), value
        )

    def _get_signature(self):
        return self._get_key(self.SIGNATURE_KEY)

    def _set_signature(self, value):
        return self._set_key(self.SIGNATURE_KEY, value)

    signature = property(_get_signature, _set_signature)

    def _get_human(self):
        return self._get_key(self.HUMAN_NAME_KEY)

    def _set_human(self, value):
        return self._set_key(self.HUMAN_NAME_KEY, value)

    human_name = property(_get_human, _set_human)

    def _get_threshold(self):
        thresh_str = self.conn.hget(
            self.CAT_META_HASH, "%s:%s" %(self.cat_id, self.THRESHOLD_KEY)
        )
        if not thresh_str:
            return None

        try:
            thresh = float(thresh_str)
        except ValueError as e:
            # TODO: Need some error handling/logging
            raise e
        else:
            return thresh

    def _set_threshold(self, value):
        return self.conn.hset(
            self.CAT_META_HASH,
            "%s:%s" %(self.cat_id, self.THRESHOLD_KEY),
            value
        )

    threshold = property(_get_threshold, _set_threshold)
