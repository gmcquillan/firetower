from unittest import TestCase

from firetower.redis_util import MockRedis
from firetower.redis_util import Redis


class TestMockRedis(TestCase):

    def setUp(self):
        self.r = MockRedis()
        self.r.zadd('myzlist', 'one', 1)
        self.r.zadd('myzlist', 'two', 2)
        self.r.zadd('myzlist', 'three', 3)

    def tearDown(self):
        self.r.data.clear()


    def test_zrange(self):
        assert (self.r.zrange('myzlist', 0, -1) ==
                [(1, 'one'), (2, 'two'), (3, 'three')])
        assert self.r.zrange('myzlist', 2, 3) == [(3, 'three')]
        assert self.r.zrange('myzlist', -2, -1) == [(2, 'two'), (3, 'three')]

    def test_zrevrange(self):
        assert (self.r.zrevrange('myzlist', 0, -1) ==
                [(3, 'three'), (2, 'two'), (1, 'one')])
        assert self.r.zrevrange('myzlist', 2, 3) == [(1, 'one')]
        assert self.r.zrevrange('myzlist', -2, -1) == [(2, 'two'), (1, 'one')]


class TestRedisUtil(TestCase):

    def setUp(self):
        self.r = MockRedis()
        self.r_util = Redis('localhost', 6300)
        self.r.lpush('test_key', 'something worth keeping')

    def tearDown(self):
        self.r.data.clear()

    def test_pop(self):
        """Test that the redis_util pop wrapper works."""
        result = self.r_util.pop('test_key')
        assert result == 'something worth keeping'

    def test_push(self):
        """Test that the redis_util push wrapper works."""

        test_val = 'another thing of note'
        self.r_util.push('test_key', test_val)
        result = self.r.lpop('test_key')

        assert result == test_val

    def test_add_category(self):
        """Test that we can successfully add categories"""
        cat_str = "Test category"
        cat_id = self.r_util.construct_cat_id(cat_str)
        self.r_util.add_category(cat_str)
        self.assertEqual(
            self.r_util.get_category_from_id(cat_id),
            cat_str,
        )
        self.assertTrue(
            self.r_util.get_threshold_from_id(cat_id) is None
        )

    def test_getting_cat_threshold(self):
        cat_id = "cat_id"
        thresh_key = "cat_id:threshold"
        cat_key = "category_ids"

        self.r_util.conn.hset(cat_key, thresh_key, "0")
        self.assertEqual(self.r_util.get_threshold_from_id(cat_id), 0)

        self.r_util.conn.hset(cat_key, thresh_key, "0.2")
        self.assertEqual(self.r_util.get_threshold_from_id(cat_id), 0.2)

        self.r_util.conn.hset(cat_key, thresh_key, "foobar")
        self.assertRaises(ValueError, self.r_util.get_threshold_from_id, cat_id)
