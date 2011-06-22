#!/usr/bin/env python

import datetime
import redis_util
import simplejson as json
import time

LEV = True
try:
    import Levenshtein
except ImportError:
    LEV = False
    import difflib

"""Firetower Aggregator. Takes JSON data, increments counts, and saves data.

Data comes in as a dictionary; we evaluate the significant keys.

Keys that are significant are added to minute-by-minute aggregate counts.
Then the JSON value of the error is saved in a time indexed hash.
"""

significant_keys = {'test': 'Test Error',}

class Aggregator(object):

  def __init__(self):
    self.r = redis_util.Redis()

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

  def incr_counter(self, root_key):
    """Increment normalized count of errors by type."""
    self.r.conn.hincrby(root_key, int(time.time()), 1) # default inc of 1.

  def save_error(self, error, sig_key):
    """Save JSON encoded string into proper bucket."""
    error_data_key = 'data_%s' % (sig_key)
    self.r.conn.zadd(error_data_key, time.time(), json.dumps(error))

  def consume(self, error):
    """Increment counters, store long-term data."""
    for key in error:
      if not error[key]:
          pass
      for sig_key in significant_keys:
        if self.is_similar(significant_keys[sig_key], error[key], 0.5):
          self.incr_counter(significant_keys[sig_key])
          #self.save_error(error, sig_key)
