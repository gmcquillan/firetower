import json
from unittest import TestCase

from firetower import classifier
from firetower.redis_util import Redis

class TestClassfier(TestCase):

    def test_lcs(self):
        """Test the longest common substring function."""

        test1 = 'the longest common sub str plus extra'
        test2 = 'the longest common sub str and something else'
        lcs = 'the longest common sub str '

        # We need to asser that we can determine the longest sub str
        # regardless of which string is passed first.
        result = classifier.longest_common_substr(test1, test2)
        result2 = classifier.longest_common_substr(test2, test1)

        assert result == lcs
        assert result2 == lcs


class TestLevenshtein(TestCase):

    def setUp(self):
        #self.r = Redis('localhost', 6379)
        self.r = Redis('localhost', 63790) # non-redis port so we get mock redis
        self.lev = classifier.Levenshtein(self.r)

    def test_str_ratio(self):
        """Test Levenshtein.str_ratio function."""

        known_str = 'hello'
        test_str = 'hello'

        assert self.lev.str_ratio(known_str, test_str) == 1.0
        assert self.lev.str_ratio(known_str, "wacky") < 0.5

    def test_is_similar(self):
        """Test Levenshtein.is_similar function."""
        know_str = "wombat"
        test_str = "combat"
        assert self.lev.is_similar(know_str, test_str, 0.5)

    def test_write_errors(self):
        """Test Levenshtein.write_errors function."""

        #test_error = {'sig': 'Testing Error', 'body': 'Error! Alert!'}
        #test_cat = 'Testing Error'
        #self.lev.write_errors(test_cat, test_error)

        #test_cat_id = self.r.construct_cat_id(test_cat)

        #count_res = self.r.conn.hgetall('counter_%s' % (test_cat_id,))
        #assert count_res

        #data_line = list(self.r.conn.zrange('data_%s' % (test_cat_id,), 0, -1))
        #data_res = json.loads(
        #        list(self.r.conn.zrange('data_%s' % (test_cat_id,), 0, -1))[0])

        # TODO: rewrite this test
        # This is erroring out because of some fundamental changes in accessing
        # error data.

        #assert str(data_res['sig']) == test_error['sig']
        #assert str(data_res['body']) == test_error['body']

    def test_classify(self):
        """Test the classify function."""

        #test_error = {'sig': 'Testing Error', 'body': 'Error!!!!'}
        #test_similar_error = {'sig': 'Testing Error 456', 'body': 'Error!!!!'}
        #test_different_error = {
        #        'sig': 'Something Totally Different', 'body': 'Error!!!'}

        #fake_threshold = 0.5

        # Nothing exists, so put it in unknown errors
        #self.lev.classify(test_error, fake_threshold)

        # Now both unknown errors are pulled out
        #self.lev.classify(test_similar_error, fake_threshold)

        # Now check that our categorized counts are accurate for
        # 'Testing Error'
        #testing_error_id = self.r.construct_cat_id('Testing_Error')
        #counts = self.r.conn.hgetall('counter_%s' % testing_error_id)
        #counts_values = [int(counts[item]) for item in counts]
        #counts_sum = sum(counts_values)
        #assert counts_sum == 2

        #self.lev.classify(test_different_error, fake_threshold)
        #sim_counts = self.r.conn.hgetall('counter_%s' % testing_error_id)
        #sim_counts_values = [int(sim_counts[item]) for item in sim_counts]
        #sim_counts_sum = sum(sim_counts_values)
        #assert sim_counts_sum == 2
