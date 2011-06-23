#!/usr/bin/env python

import datetime
import simplejson as json
import time

import alerts
import redis_util
import aggregator

queue_key = 'incoming'
ALERT_TIME = .5 # Minutes between alert checks/notifications.
TIMESLICES = [300] # 5 Minute periods between Alert checks.
ALERT_THRESHOLDS = {
        'high': 1000,
        'medium': 100,
        'low': 10
}
TRACKED_KEYS = ["Test Error"] # This is the keyname of our error signature.


class Main(object):
    """Main loop."""

    def run(self):
        alert_time = None
        queue = redis_util.Redis()
        aggr = aggregator.Aggregator()
        alert = alerts.Alert()
        while 1:
            now = datetime.datetime.now()
            err = queue.pop(queue_key)
            if not alert_time:
                alert_time = datetime.timedelta(minutes=ALERT_TIME) + now
            elif alert_time < now:
                alert.check(TRACKED_KEYS, TIMESLICES, ALERT_THRESHOLDS.values())
                alert_time = datetime.timedelta(minutes=ALERT_TIME) + now
            if err:
                parsed = json.loads(err)
                aggr.consume(parsed)
            else:
                time.sleep(1)


if __name__ == '__main__':
    main = Main()
    main.run()
