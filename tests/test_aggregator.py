from unittest import TestCase

from firetower.aggregator import Aggregator


class TestAggregator(TestCase):

    def setUp(self):
        self.agg = Aggregator()

    def test_str_ratio(self):
        known_str = "hello"
        test_str = "hello"

        assert self.agg.str_ratio(known_str, test_str) == 1.0
        assert self.agg.str_ratio(known_str, "wacky") < 0.5

    def test_is_similar(self):
        know_str = "wombat"
        test_str = "combat"
        assert self.agg.is_similar(know_str, test_str, 0.5)

    def test_incr_counter(self):
        key = 'test-key'
        self.agg.incr_counter(key)
        from pdb import set_trace; set_trace()
        saved = self.agg.r.get_counts(['test-key'])


    def test_consume(self):
        error = {'test': 'Test Erronius'}
        self.agg.consume(error)
        assert self.agg.r.pop('data_test')
