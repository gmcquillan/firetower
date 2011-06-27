import datetime
import difflib
import json

def longest_common_substr(S1, S2):
    M = [[0]*(1+len(S2)) for i in xrange(1+len(S1))]
    longest, x_longest = 0, 0
    for x in xrange(1,1+len(S1)):
        for y in xrange(1,1+len(S2)):
            if S1[x-1] == S2[y-1]:
                M[x][y] = M[x-1][y-1] + 1
                if M[x][y]>longest:
                    longest = M[x][y]
                    x_longest  = x
            else:
                M[x][y] = 0
    return S1[x_longest-longest: x_longest]


class Classifier(object):
    pass


class NaiveBayes(Classifier):
    pass


class Levenshtein(Classifier):

    def __init__(self, redis):
        """init.

        Args:
            conf: a conf.Conf obj.
        """
        self.redis = redis

    def str_ratio(self, golden, test_str):
        """Return the ratio of similarity between two strings; ignore spaces."""
        return difflib.SequenceMatcher(None, golden, test_str).ratio()

    def is_similar(self, golden, test_str, thresh):
        """Returns True if similarity is larger than thresh."""

        ratio = self.str_ratio(golden, test_str)
        if ratio > thresh:
            print "%s: %s matches %s with a %.1f ratio" % (
                    str(datetime.datetime.now()), test_str, golden, ratio)
            return True

        return False

    def write_errors(self, cat, error):
        """Increment counters, save data."""

        cat_counter = 'counter_%s' % (cat,)
        cat_data = 'data_%s' % (cat,)
        self.redis.incr_counter(cat_counter)
        self.redis.save_error(cat_data, error)

    def check_message(self, cat, error):
        """Compare error with messages from a category.
        
        Args:
            cat: str, keyname of a category (maybe unknown_errors)
            error: dict, error message we're processing
        """
        sig = error['sig']
        unknown = 'unknown_errors'
        if cat == unknown:
            cat_errors = self.get_unknown_errors()
        else:
            cat_errors = self.get_latest_data(cat)
        for cat_error in cat_errors:
            decode_error = json.loads(cat_error)
            cat_sig = decode_error['sig']
            if self.is_similar(cat_sig, sig, 0.7):
                if cat == unknown:
                    cat = longest_common_substr(cat_sig, sig)
                    self.add_category(cat)
                    self.write_errors(cat, cat_error)
                self.write_errors(cat, error)
            else:
                self.save_error(unknown, error)

    def classify(self, error):
        """Determine which category, if any, a signature belongs to.

        If it doesn't find a match, then it'll save the error into an
        'unknown' list of errors, which subsequent errors are checked against.
        When a match is found between a new errors and one of the unknown errors
        a new category is created.

        Args:
            error: dict of json payload with a 'sig' key.
        """
        sig = error.get('sig', 'unknown')
        # Check the unclassified errors first.
        uk_errors = self.redis.get_unknown_errors()
        # If we have any previous unknown errors,
        # let's see if our new message matches
        if uk_errors:
            for uk_error in uk_errors:
                uk_error = json.loads(uk_error) # This ends up a str?
                # Is our new error a match?
                if self.is_similar(uk_error['sig'], sig, 0.7):
                    # Save these as a new category, normalize, store.
                    cat = longest_common_substr(uk_error['sig'], sig)
                    self.write_errors(cat, uk_error)
                    self.write_errors(cat, error)
                    self.redis.add_category(cat)
                    continue
                # Can't categorize; store as new unknown.
                else:
                    self.redis.save_error(
                            'unknown_errors', json.dumps(uk_error))

        categories = self.redis.get_categories()

        # Let's see if our message matches a category
        if categories:
            for cat in categories:
                result = self.redis.get_latest_data(cat)
                try:
                    latest_error = json.loads(result)
                except TypeError, e:
                    print "Ran into problem with JSON", e
                    print "latest_error: ", latest_error
                    print "type: ", type(latest_error)
                    continue
                if self.is_similar(latest_error['sig'], sig, 0.7):
                    self.write_errors(cat, error)
                else:
                    self.redis.save_error(
                            'unknown_errors', json.dumps(uk_error))
                continue
        else:
            self.redis.save_error(
                    'unknown_errors', json.dumps(uk_error))
