#!/usr/bin/env python

import copy
import redis
import time

"""redis_util - the main queue handler for firetower."""

class Redis(object):

  def __init__(self):
    self.conn = redis.Redis(host='localhost', port=6379, db=0)

  def pop(self, key):
    return self.conn.rpop(key)

  def push(self, key, value):
    self.conn.lpush(key, value)

  def get_counts(self, tracked_keys):
    """Return the hgetall for each tracked_key in a list."""
    error_counts = {}
    for key in tracked_keys:
      error_counts[key] = self.conn.hgetall(key)

    return error_counts

  def sum_timeslice_values(self, error_counts, timeslice, start=None):
    """Return sum of all error instances within time_slice."""
    if not start:
      start = int(time.time())
    end = start - timeslice
    error_sums = {}
    for error in error_counts:
      error_sums[error] = 0
      for instant in error_counts[error]:
        thresh_start = int(start - timeslice)
        instant = int(instant.split('.')[0])
        if instant > thresh_start:
          error_sums[error] += int(error_counts[error][str(instant)])

    return error_sums
