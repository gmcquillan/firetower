import time

import redis_util
import config


class TimeSeries(object):

    def __init__(self, redis_conn, cat_id):
        self.cat_id = cat_id
        self.redis_conn = redis_conn

    def range(self, start, end):
        return self.redis_conn.zrevrangebyscore(
            "ts_%s" % self.cat_id, end, start, withscores=True
        )


class Events(object):
    def __init__(self, redis_conn, cat_id):
        self.cat_id = cat_id
        self.redis_conn = redis_conn

    def last_x(self, count):
        self.redis_conn.zrevrange(
            "data_%s" % self.cat_id, 0, count
        )


class Category(object):

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
        self.timeseries = TimeSeries(redis_conn, self.cat_id)
        self.events = Events(redis_conn, self.cat_id)

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

        return cls(redis_conn, cat_id)

    @classmethod
    def get_all_categories(cls, redis_conn):
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

    def _set_threshold(self):
        return self.conn.hset(
            self.CAT_META_HASH,
            "%s:%s" %(self.cat_id, self.THRESHOLD_KEY),
            value
        )

    threshold = property(_get_threshold, _set_threshold)
