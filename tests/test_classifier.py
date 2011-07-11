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
        self.r = Redis('localhost', 6379)
        self.lev = classifier.Levenshtein(self.r)

    def test_str_ratio(self):
        """Test Levenshtein.str_ratio function."""

        known_str = "hello"
        test_str = "hello"

        assert self.lev.str_ratio(known_str, test_str) == 1.0
        assert self.lev.str_ratio(known_str, "wacky") < 0.5

    def test_is_similar(self):
        """Test Levenshtein.is_similar function."""
        know_str = "wombat"
        test_str = "combat"
        assert self.lev.is_similar(know_str, test_str, 0.5)

