import unittest

from firetower import redis_util
from firetower.category import TimeSeries

def ts_to_hits(ts):
    return int(ts[1].split(":")[1])

class TestArchive(unittest.TestCase):
    def setUp(self):
        self.r = redis_util.MockRedis(share_state=False)
        self.start_time = 1000
        self.cat_id = "foobar"
        self.counter = "counter_%s" % self.cat_id

    def test_simple_archive(self):
        count = 10

        self.r.hset(self.counter, self.start_time-1, count)
        TimeSeries.archive_cat_counts(self.r, self.cat_id, self.start_time)
        self.assertRaises(KeyError, self.r.hget, self.counter, self.start_time-1)

        ts = self.r.zrange("ts_%s" % self.cat_id, 0, -1, withscores=True)
        self.assertEqual(len(ts), 1)
        self.assertEqual(ts_to_hits(ts[0]), 10)

    def test_archive_skip(self):
        """Test that the archive method skips new entries"""

        self.r.hset(self.counter, self.start_time-1, 1)
        self.r.hset(self.counter, self.start_time+1, 2)
        TimeSeries.archive_cat_counts(self.r, self.cat_id, self.start_time)

        self.assertRaises(KeyError, self.r.hget, self.counter, self.start_time-1)
        self.assertTrue(self.r.hget(self.counter, self.start_time+1))

        ts = self.r.zrange("ts_%s" % self.cat_id, 0, -1, withscores=True)
        self.assertEqual(len(ts), 1)
        self.assertEqual(ts_to_hits(ts[0]), 1)

    def test_multiple_archive(self):
        for step in [1,2]:
            self.r.hset(self.counter, self.start_time-step, 1)

        TimeSeries.archive_cat_counts(self.r, self.cat_id, self.start_time)

        for step in [1, 2]:
            self.assertRaises(
                KeyError, self.r.hget, self.counter, self.start_time-step)

        ts = self.r.zrange("ts_%s" % self.cat_id, 0, -1, withscores=True)
        self.assertEqual(len(ts), 2)
        for record in ts:
            self.assertEqual(ts_to_hits(record), 1)

if __name__ == '__main__':
    unittest.main()
