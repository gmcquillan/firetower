from unittest import TestCase

from firetower import redis_util
from firetower.category import Category, TimeSeries

class TestCategory(TestCase):
    def setUp(self):
        self.r = redis_util.MockRedis(share_state=False)

        self.cat_id = "foobar"
        self.cat_sig = "baz"
        self.cat_thresh = 1.0
        self.cat_name = "ham_eggs_spam"

        self.set_meta("signature", self.cat_sig)
        self.set_meta("threshold", self.cat_thresh)
        self.set_meta("human_name", self.cat_name)

        self.cat = Category(self.r, cat_id=self.cat_id)

    def get_meta(self, name):
        self.r.hget(
            Category.CAT_META_HASH, "%s:%s" % (self.cat_id, name)
        )

    def set_meta(self, name, value):
        self.r.hset(
            Category.CAT_META_HASH,
            "%s:%s" % (self.cat_id, name), value
        )

    def test_category_create(self):
        cat = Category.create(self.r, "new test category")
        self.assertEqual(cat.signature, "new test category")
        self.assertTrue(cat.cat_id)

    def test_meta(self):
        """Test meta get/set methods"""
        details = [
            ("signature", self.cat_sig, "new_cat_sig"),
            ("human_name", self.cat_name, "new_cat_name"),
            ("threshold", self.cat_thresh, 0.7)
        ]

        for meta_name, old_value, new_value in details:
            self.assertEqual(getattr(self.cat, meta_name), old_value)
            self.set_meta(meta_name, new_value)
            self.assertEqual(getattr(self.cat, meta_name), new_value)

    def test_non_float_threshold(self):
        self.set_meta("threshold", "banana")
        def get_thresh():
            return self.cat.threshold
        self.assertRaises(ValueError, get_thresh)

    def test_get_all_cats(self):
        new_ids = ["foo", "bar", "baz"]
        for new_id in new_ids:
            self.r.hset(
                Category.CAT_META_HASH,
                "%s:signature" % (new_id), self.cat_sig
            )

        cats = Category.get_all_categories(self.r)
        self.assertEqual(len(cats), len(new_ids) + 1)
        for cat in cats:
            self.assertEqual(cat.signature, self.cat_sig)


class TestTimeSeries(TestCase):
    def add_ts(self, ts, count, cat_id=None):
        if not cat_id:
            cat_id = self.cat_id
        self.r.zadd(
            "ts_%s" % self.cat_id, TimeSeries.generate_ts_value(ts, count), ts
        )

    def setUp(self):
        self.r = redis_util.MockRedis(share_state=False)
        self.cat_id = "foobar"
        self.time_series = TimeSeries(self.r, self.cat_id)

    def test_get_all(self):
        start_ts = 100
        expected_counts = [1, 2, 3]
        for i, count in enumerate(expected_counts):
            self.add_ts(start_ts+i, count)

        ts_list = self.time_series.all()
        self.assertEqual(len(ts_list), len(expected_counts))
        for ts, count in ts_list:
            self.assertTrue(count in expected_counts)

    def test_get_range(self):
        for count, ts in enumerate(range(100, 120)):
            self.add_ts(ts, count)

        ts_list = self.time_series.range(110, 115)
        self.assertEqual(len(ts_list), 6)
