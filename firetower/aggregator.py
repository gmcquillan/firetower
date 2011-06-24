import datetime
from itertools import ifilter
import json
import time

try:
        import Levenshtein
        LEV = True
except ImportError:
        LEV = False
        import difflib

from redis_util import Redis

"""Firetower Aggregator. Takes JSON data, increments counts, and saves data.

Data comes in as a dictionary; we evaluate the significant keys.

Keys that are significant are added to minute-by-minute aggregate counts.
Then the JSON value of the error is saved in a time indexed hash.
"""

significant_keys = {'test': 'Test Error',}


class Aggregator(object):

    def __init__(self, redis):
        self.r = redis

    def ratio(self, golden, test_str):
        """Use appropraite library to do comparisons."""
        if not test_str:
            return 0
        if LEV:
                return Levenshtein.ratio(golden, test_str)
        else:
                return difflib.SequenceMatcher(None, golden, test_str).ratio()

    def str_ratio(self, golden, test_str):
        """Return the ratio of similarity between two strings."""
        return self.ratio(golden, test_str)

    def is_similar(self, golden, test_str, thresh):
        """Returns True if similarity is larger than thresh."""
        ratio = self.str_ratio(golden, test_str)
        if ratio > thresh:
            print "%s: %s matches %s with a %.1f ratio" % (
                    str(datetime.datetime.now()), test_str, golden, ratio)
            return True

        return False

    def consume(self, error):
        """Increment counters, store long-term data."""
        for key, item in ifilter(lambda (x, y): y is not None, error.items()):
            for sig_key in significant_keys:
                if self.is_similar(significant_keys[sig_key], item, 0.5):
                    self.r.incr_counter(significant_keys[sig_key])
                    self.r.save_error(error, sig_key)
