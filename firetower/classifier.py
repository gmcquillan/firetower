import difflib
import json

from logbook import Logger

from firetower import category

log = Logger('Firetower-classifier')

def longest_common_substr(s1, s2):
    """
    Args:
        s1: str, first string to compare.
        s2: str, second string to compare.

    Influenced by:
    http://en.wikibooks.org/wiki/Algorithm_implementation/Strings/ \
    Longest_common_substring#Python
    """
    if len(s1) < len(s2):
        s1, s2 = s2, s1

    M = [[0]*(1+len(s1)) for i in xrange(1+len(s1))]
    longest, x_longest = 0, 0
    for x in xrange(1, 1+len(s1)):
        for y in xrange(1, 1+len(s2)):
            if s1[x-1] == s2[y-1]:
                M[x][y] = M[x-1][y-1] + 1
                if M[x][y] > longest:
                    longest = M[x][y]
                    x_longest = x
            else:
                M[x][y] = 0
    return s1[x_longest-longest: x_longest]


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
        return difflib.SequenceMatcher(None, golden, test_str).real_quick_ratio()

    def is_similar(self, golden, test_str, thresh):
        """Returns True if similarity is larger than thresh."""

        ratio = self.str_ratio(golden, test_str)
        if ratio > thresh:
            return True

        return False

    def write_errors(self, cat_id, error):
        """Increment counters, save data.

        Args:
            cat_id: str, category id hash.
            error: dict, new payload to save.
        """
        cat_counter = 'counter_%s' % (cat_id,)
        cat_data = 'data_%s' % (cat_id,)
        self.redis.incr_counter(cat_counter)
        self.redis.save_error(cat_data, error)

    def check_message(self, cat, error, default_thresh):
        """Compare error with messages from a category.

        Args:
            cat: tuplel, containing an id and a category name.
                 Example: (0, 'Test Error')
            error: dict, error message we're processing.
            thresh: float, the ratio of similarity needed to match.
        """
        sig = error['sig']

        custom_thresh = cat.threshold
        thresh = custom_thresh if custom_thresh is not None else default_thresh
        log.debug('Checking message using %s threshold value' % (str(thresh),))

        exemplar_str = None
        last_data = cat.events.last_x(1)
        if not last_data:
            exemplar_str = cat.signature
        else:
            exemplar_str = json.loads(last_data)['sig']

        if self.is_similar(sig, exemplar_str, thresh):
            log.debug('Found match for category id: %s' % (cat_id,))
            return True

    def classify(self, error, thresh):
        """Determine which category, if any, a signature belongs to.

        If it doesn't find a match, then it'll save the error into a new
        category, which subsequent errors are checked against.

        Args:
            error: dict of json payload with a 'sig' key.
            thresh: float, classification threshold to match.
        """
        categories = category.Category.get_all_categories(self.redis.conn)
        for cat in categories:
            if self.check_message(cat, error, thresh):
                self.write_errors(cat.cat_id, error)
        else:
            cat_sig = error['sig']
            cat_id = self.redis.construct_cat_id(cat_sig)
            log.info('Adding new category with id: %s' % (cat_id,))
            self.redis.add_category(cat_sig)
            self.write_errors(cat_id, error)
