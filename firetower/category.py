import calendar
from collections import namedtuple
import hashlib
import simplejson as json
import time

from logbook import Logger

import classifier
import redis_util

log = Logger('Firetower-category')
TSTuple = namedtuple("TimeSeriesTuple", ("timestamp", "count"))

SECOND = 1
MINUTE = 60
HOUR = MINUTE * 60
DAY = HOUR * 24
WEEK = DAY * 7

TIME_SLICES = {
    "second": SECOND, "minute": MINUTE, "5_minute": MINUTE * 5,
    "10_minute": MINUTE * 10, "15_minute": MINUTE * 15,
    "30_minute": MINUTE * 30, "hour": HOUR, "3_hour": HOUR * 3,
    "6_hour": HOUR * 6, "12_hour": HOUR * 12, "day": DAY,
    "week": WEEK
}

class TimeSeries(object):
    def __init__(self, redis_conn, cat_id):
        """Create a time series instance for a category

        Args:
            redis_conn: redis.Redis connection.
            cat_id: str, identifier for category.

        This object exposes the time series data stored in the sorted set
        ts_{cat_id}.

        """
        self.cat_id = cat_id
        self.redis_conn = redis_conn

    def convert_ts_list(self, ts_list, time_slice=None):
        """Process lists from timeseries sorted sets.

        Args:
            ts_list: List of tuples from the ts_ sorted set.
            time_slice: Optional. Name of a key in TIME_SLICES. The value of
                that key sets the size of the bucket the time series data
                is sorted into. Defaults to minute buckets.


        Takes a list of scores and values from a time series sorted set and
        return a list of entries in the form ({TIMESTAMP}, {COUNT}). This is
        required because the TS sorted set doesn't hold the raw count, to make
        the values unique it stores them as '{TIMESTAMP}:{COUNT}'

        """
        ret = []

        slice_dict = {}
        # This will be an int of seconds pulled from TIME_SLICES. This is how
        # large the buckets will be when sorting the time series data.
        if time_slice is None:
            time_slice = "minute"
        time_slice = TIME_SLICES[time_slice]

        if not ts_list:
            return []

        for ts_entry in ts_list:
            ts = int(ts_entry[1])
            count = int(ts_entry[0].split(":")[1])
            key = ts/time_slice
            slice_dict[key] = slice_dict.get(key, 0) + count

        keys = slice_dict.keys()
        keys.sort()
        for i in range(keys[0], keys[-1]):
            if i not in slice_dict:
                slice_dict[i] = 0
        keys = slice_dict.keys()
        keys.sort()

        for key in keys:
            ret.append(TSTuple(key*time_slice, slice_dict[key]))
        return ret

    def all(self, time_slice=None):
        """Return all timeseries data for the category.

        The data will be returned as a sequence of sequences.
        Each sub-sequence is of the form (VALUE, TIMESTAMP) where TIMESTAMP is
        a number of seconds since epoch and VALUE is the number of times the
        category appeared in that second.
        """
        return self.convert_ts_list(
            self.redis_conn.zrange(
                "ts_%s" % (self.cat_id), 0, -1, withscores=True
            ), time_slice
        )

    def range(self, start, end, time_slice=None):
        """Return all timeseries data for the category between start and end.

        start and end are assumed to be seconds since the epoch.

        The data will be returned as a sequence of sequences.
        Each sub-sequence is of the form (VALUE, TIMESTAMP) where TIMESTAMP is
        a number of seconds since epoch and VALUE is the number of times the
        category appeared in that second.
        """
        return self.convert_ts_list(
            self.redis_conn.zrevrangebyscore(
                "ts_%s" % (self.cat_id), end, start, withscores=True
            ),
            time_slice
        )

    @staticmethod
    def generate_ts_value(ts, count):
        """Turn a timestamp and cat count into a value for storage in a set"""
        return "%s:%s" % (ts, count)

    def archive_cat_counts(self, start_time, preserve=True):
        """Move everything before start_time into a Sorted Set.

        Args:
            start_time: datetime, utc timezone.
            preserve: boolean, if set will add to existing ts counts rather than
                over-writing them. Useful when archiving counts that already
                have entries in the ts set (e.g. backfilling)
        """
        ts_key = 'ts_%s' % (self.cat_id,)
        counter_key = 'counter_%s' % (self.cat_id,)
        check_mark = calendar.timegm(start_time.timetuple())
        now  = calendar.timegm(time.gmtime())
        counters_to_delete = []
        count_dict = self.redis_conn.hgetall(counter_key)

        interesting_ts = [
            x for x in count_dict if int(x) < check_mark
        ]

        for ts in interesting_ts:
            if ts == now:
                continue
            new_value = count_dict[ts]
            if preserve:
                existing_entry = self.range(ts, ts)
                if existing_entry:
                    # If there is an existing entry then don't overwrite it.
                    # If we do find something it should be the only entry for
                    # that second timeslot.
                    new_value += existing_entry[0].count
            self.redis_conn.zadd(
                ts_key, self.generate_ts_value(ts, new_value), ts
            )
            counters_to_delete.append(ts)

        # Remove the counters from the 'counter' key.
        # We store longterm counters in the timeseries key (ts).
        for counter in counters_to_delete:
            self.redis_conn.hdel(counter_key, counter)


class Events(object):
    def __init__(self, redis_conn, cat_id):
        self.cat_id = cat_id
        self.redis_conn = redis_conn

    def add_event(self, event, timestamp=None,
            event_increment=True, ts_increment=True):
        """Add an event to the event list.

        Args:
            event: the event dictionary to save into the event set
            timestamp: Optional time stamp to use when inserting the event.
                Defaults to now.
            event_increment: Optional. boolean - adds event to event series.
            ts_increment: Optional. boolean - Increments the counter for this category.

        """
        if timestamp is None:
            timestamp = int(time.time())

        event['ts'] = timestamp
        if event_increment:
            self.redis_conn.zadd("data_" + self.cat_id,  json.dumps(event), timestamp)
        if ts_increment:
            self.redis_conn.hincrby("counter_" + self.cat_id, timestamp, 1)

    def get_recent(self, num_events):
        """Return a list of recent events up to the num specified.

        Args:
            num_events: int, number of events to return.
        Returns:
            list, the most recent events up to num_events.
        """
        return self.range(int(num_events).__neg__(), -1)

    def recent_signatures(self, num_sigs):
        """Return a list of recent sigatures."""

        events = self.get_recent(num_sigs)
        return [json.loads(event)['sig'] for event in events]

    def range(self, start, end):
        """Return a range of events

        Args:
            start: Start index to return from.
            end: End index to return to.

        Both start and end are inclusive.
        """
        return self.redis_conn.zrange("data_%s" % (self.cat_id,), start, end)

    def _backfill_timeseries(self, delete=False):
        """This is for pulling data out an event stream and putting in ts.

        Args:
            delete: bool, whether or not to delete the archived ts.
        """
        # Not sure this is an ideal solution, since it depends on archiving
        # to work properly, which may be why we're backfilling in the
        # first place.
        events = self.redis_conn.zrange(
                "data_%s" % self.cat_id, 0, -1, withscores=True)
        cat_counter_id = "counter_%s" % (self.cat_id,)
        cat_ts_id = "ts_%s" % (self.cat_id,)
        if delete:
            self.redis_conn.delete(cat_ts_id)
        for _sig, ts in events:
            self.redis_conn.hincrby(cat_counter_id, int(ts), 1)

    def delete(self):
        """Delete an entire set of data"""
        self.redis_conn.delete("data_%s" % self.cat_id)


class Category(object):
    """A class to encapsulate operations involving categories and their metadata

    Currently exposes 3 read/write properties: signature, human_name, and
    threshold.

    """

    CAT_META_HASH = "category_ids"
    SIGNATURE_KEY = "signature"
    HUMAN_NAME_KEY = "human_name"
    THRESHOLD_KEY = "threshold"
    STDEV_KEY = "stdev"
    MEAN_KEY = "mean"
    RE_KEY = "regex"

    keys = [
        CAT_META_HASH, SIGNATURE_KEY, HUMAN_NAME_KEY, THRESHOLD_KEY,
        STDEV_KEY, MEAN_KEY, RE_KEY
    ]

    def __init__(self, redis_conn, signature=None, cat_id=None, event=None):
        """ Init.

        Args:
            redis_conn: redis.Redis instance.
            signature: str.
            cat_id: str, used to fetch existing category if it exists.
            event: dict, added to existing set of events.
        """
        self.conn = redis_conn

        if signature:
            self.cat_id = redis_util.Redis.construct_cat_id(signature)
        elif cat_id:
            self.cat_id = cat_id
        else:
            self.cat_id = None

        self.timeseries, self.events = None, None

        if self.cat_id:
            self.timeseries = TimeSeries(self.conn, self.cat_id)
            self.events = Events(self.conn, self.cat_id)

        if event and self.events:
            self.events.add_event(event)

    def to_dict(self, num_recent=5):
        """Return a dictionary representation of this cats metadata

        Args:
            num_recent: int, number of recent categorizations to include.
            defaults to five.
        Returns:
            dict, containing string value of signature, human readbable name
            of the category, the classification threshold, and a list of the
            most recent event signatures classified as this category.
        """
        return {
            self.SIGNATURE_KEY: self.signature,
            self.HUMAN_NAME_KEY: self.human_name,
            self.THRESHOLD_KEY: self.threshold,
            "recent_signatures": self.events.recent_signatures(num_recent)
        }

    def recategorise(self, default_threshold, archive_time=None):
        """WARNING: Will remove this category and re-sort its events

        Args:
            default_threshold: Default threshold to try and reclassify on.
                This takes the place of what is pulled from the config in
                firetower-server.
            archive_time: Optional. After reclassification if this is set
                everything before this time will be archived from this point
                back.

        """

        for key in self.keys:
            self.conn.hdel(self.CAT_META_HASH, "%s:%s" % (self.cat_id, key))

        comp = classifier.Levenshtein()

        event_chunk = 1000
        curr_count = 0
        while 1:
            events = self.events.range(curr_count, (curr_count+event_chunk-1))
            if not events:
                break
            for event in events:
                event_dict = json.loads(event)
                self.classify(self.conn, comp, event_dict, default_threshold)
            curr_count += event_chunk
        if archive_time:
            for cat in self.get_all_categories(self.conn):
                cat.timeseries.archive_cat_counts(archive_time)

        self.events.delete()
        self.conn.delete("counter_%s" % self.cat_id)
        self.conn.delete("ts_%s" % self.cat_id)

    @classmethod
    def classify(cls, queue, classifiers, error, threshold):
        """Determine which category, if any, a signature belongs to.

        If it doesn't find a match, then it'll save the error into a new
        category, which subsequent errors are checked against.

        Args:
            queue: redis connection instance.
            classifiers: list of Classifier instances.
            error: dict of json payload with a 'sig' key.
            threshold: float, classification threshold to match.
        """
        categories = cls.get_all_categories(queue)
        matched_cat = None
        start = time.time()
        for classifier in classifiers:
            matched = False
            for cat in categories:
                if classifier.check_message(cat, error, threshold):
                    cat.events.add_event(error)
                    matched_cat = cat
                    matched = True
                    break
            if matched:
                break
        else:
            cat_sig = error['sig']
            matched_cat = cls.create(queue, cat_sig, event=error)

        end = time.time()
        log.info('Classification took %.2f seconds for matched category %s' % (
            end - start, matched_cat.cat_id))
        return matched_cat

    @classmethod
    def create(cls, redis_conn, signature, event=None):
        """Adds category metadata.

        Args:
            redis_conn: Redis connection to use.
            signature: Signature of the new category.
            event: Optional. Event to save under the new category.

        This method will set 3 metadata fields for the category hash:
        * category is the full text of the original cateory.
        * verbose_name is the human readable name for this category (used for
            display purposes)
        * threshold is the custom threshold for this category

        The key values are in the form {category_hash}:{metadata_name} e.g.
        a909ede39c09d84ed1839c5ca0f9b9876113770b:category
        """
        redis_conn.zadd("categories", signature, 0)
        cat_id = cls.construct_cat_id(signature)
        cat_fields = (
            (cls.SIGNATURE_KEY, signature), (cls.HUMAN_NAME_KEY, cat_id),
            (cls.THRESHOLD_KEY, ""),
        )
        for key, value in cat_fields:
            redis_conn.hset(cls.CAT_META_HASH, "%s:%s" %(cat_id, key), value)

        kwargs = {"cat_id": cat_id}
        if event:
            kwargs["event"] = event
        return cls(redis_conn, **kwargs)

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

    @staticmethod
    def construct_cat_id(signature):
        """Create Category ID hash from a category signature.

        Args:
            signature: str, signature of category.
        Returns:
            str, sha1 hash.
        """
        cat_id = hashlib.sha1()
        cat_id.update(signature)
        return cat_id.hexdigest()

    def _get_key(self, key):
        return self.conn.hget(
            self.CAT_META_HASH, "%s:%s" % (self.cat_id, key)
        )

    def _set_key(self, key, value):
        return self.conn.hset(
            self.CAT_META_HASH, "%s:%s" % (self.cat_id, key), value
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
        return self._get_key(self.THRESHOLD_KEY)

    def _set_threshold(self, value):
        return self._set_key(self.THRESHOLD_KEY, value)

    threshold = property(_get_threshold, _set_threshold)

    def _get_stdev(self):
        return self._get_key(self.STDEV_KEY)

    def _set_stdev(self, value):
        return self._set_key(self.STDEV_KEY)

    stdev = property(_get_stdev, _set_stdev)

    def _get_mean(self):
        return self._get_key(self.MEAN_KEY)

    def _set_mean(self, value):
        return self._set_key(self.MEAN_KEY, value)

    mean = property(_get_mean, _set_mean)

    def _get_regex(self):
        return self._get_key(self.RE_KEY)

    def _set_regex(self, value):
        return self._set_key(self.RE_KEY, value)

    regex = property(_get_regex, _set_regex)
