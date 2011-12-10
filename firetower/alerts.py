import datetime


class Alert(object):

    def __init__(self, redis):
        self.conn = redis
        self.all_counts = {}

    def send_alert(self, msg):
        """Send a quick email with the error message."""
        print "%s: Alert! %s" % (str(datetime.datetime.now()), msg)

    def check_thresh(self, error_sums, timeslice, threshold):
        """Check to see if the sum exceeds the threshold for our time_slice."""
        for error, error_sum in error_sums.items():
            if error_sum > threshold:
                self.send_alert(
                    "%s has violated %s threshold for %s timeperiod (%s)" % (
                        error, threshold, timeslice, error_sum))

    def check(self, error_sigs, timeslices):
        """Run a check of all the thresholds."""
        counts = self.conn.get_counts(error_sigs.keys())
        for timeslice in timeslices:
            error_sums = self.conn.sum_timeslice_values(counts, timeslice)
            for error in error_sigs:
                for threshold in error_sigs[error]['alert_thresholds'].values():
                    self.check_thresh(error_sums, timeslice, int(threshold))
