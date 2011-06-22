#!/usr/bin/env python

import datetime
import redis_util
import time


class Alert(object):

  def __init__(self):
    self.conn = redis_util.Redis()
    self.all_counts = {}

  def send_alert(self, msg):
    """Send a quick email with the error message."""
    print "%s: Alert! %s" % (str(datetime.datetime.now()), msg)

  def check_thresh(self, error_sums, timeslice, threshold):
    """Check to see if the sum exceeds the threshold for our time_slice."""
    for error in error_sums:
      if error_sums[error] > threshold:
        self.send_alert("%s has violated %s threshold for %s timeperiod (%s)" %(
            error, threshold, timeslice, error_sums[error]))

  def check(self, tracked_keys, timeslices, thresholds):
    """Run a check of all the thresholds."""
    counts = self.conn.get_counts(tracked_keys)
    for timeslice in timeslices:
      error_sums = self.conn.sum_timeslice_values(counts, timeslice)
      # Should relate a threshold to a timeslice.
      for threshold in thresholds:
        self.check_thresh(error_sums, timeslice, threshold)
