import json
import unittest

import test_category
from firetower import classifier
from firetower import redis_util


class TestClassfier(unittest.TestCase):

    def setUp(self):
        self.r = redis_util.MockRedis(share_state=False)

        self.cat_id = "baz"
        self.cat_sig = "wombat"
        self.cat_thresh = 0.7
        self.cat_name = "Classifier test category"

        self.cat = test_category.create_mock_category(
                self.cat_id,
                self.cat_sig,
                self.cat_thresh,
                self.cat_name)

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
        self.lev = classifier.Levenshtein()

    def test_str_ratio(self):
        """Test Levenshtein.str_ratio function."""

        known_str = 'hello'
        test_str = 'hello'

        assert self.lev.str_ratio(known_str, test_str) == 1.0
        assert self.lev.str_ratio(known_str, "wacky") < 0.5

    def test_is_similar(self):
        """Test Levenshtein.is_similar function."""
        exemplar_str = "wombat"
        test_str = "combat"
        assert self.lev.is_similar(exemplar_str, exemplar_str, 0.5)

    def test_check_message(self):
        """Test the classify function."""

        mock_id = "something"
        mock_sig = "wombat"
        mock_thresh = 0.7
        mock_human = "A test category"
        mock_cat = test_category.create_mock_category(
                mock_id, mock_sig, mock_thresh, mock_human)

        test_error = {"sig": "combat"}

        assert self.lev.check_message(mock_cat, test_error, 0.7)

if __name__ == '__main__':
    unittest.main()
