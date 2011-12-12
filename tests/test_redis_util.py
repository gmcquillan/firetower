import unittest

from firetower import redis_util


class TestMockRedis(unittest.TestCase):

    def setUp(self):
        self.r = redis_util.MockRedis()
        self.r.zadd('myzlist', 'one', 1)
        self.r.zadd('myzlist', 'two', 2)
        self.r.zadd('myzlist', 'three', 3)

    def tearDown(self):
        self.r.data.clear()


    def test_zrange(self):
        self.assertEqual(
            self.r.zrange('myzlist', 0, -1, withscores=True),
            [(1, 'one'), (2, 'two'), (3, 'three')]
        )
        self.assertEqual(
            self.r.zrange('myzlist', 2, 3, withscores=True), [(3, 'three')])
        self.assertEqual(
            self.r.zrange('myzlist', -2, -1, withscores=True),
            [(2, 'two'), (3, 'three')]
        )

    def test_zrevrange(self):
        self.assertEqual(
            self.r.zrevrange('myzlist', 0, -1, withscores=True),
            [(3, 'three'), (2, 'two'), (1, 'one')]
        )
        self.assertEqual(
            self.r.zrevrange('myzlist', 2, 3, withscores=True), [(1, 'one')])
        self.assertEqual(
            self.r.zrevrange('myzlist', -2, -1, withscores=True),
            [(2, 'two'), (1, 'one')]
        )

if __name__ == '__main__':
    unittest.main()
