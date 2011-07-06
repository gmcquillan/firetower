import unittest

from firetower.redis_util import MockRedis


class TestMockRedis(unittest.TestCase):

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

if __name__ == '__main__':
    unittest.main()
