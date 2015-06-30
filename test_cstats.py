LENGTH = 100000

import time
import datetime
import random
import array

from webstress.util import stats, cstats, helpers

def random_date(start, end):
    """
    This function will return a random datetime between two datetime 
    objects.
    """
    from random import randrange
    from datetime import timedelta

    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = randrange(int_delta)
    d = start + timedelta(seconds=random_second)
    return (helpers._make_safe(d), helpers._make_safe(d + timedelta(seconds=1)))

class Sentinel(object):
    pass

status_codes = [200, 500, 404]
targets = ['target1', 'target2', 'target3']

def build_timespans():
    now = datetime.datetime.now()
    timespans = [random_date(now - datetime.timedelta(seconds=random.randrange(1, 30)), now) for _ in xrange(LENGTH)]

    starts = [helpers.normalise_datetime(x) for x, y in timespans]
    ends = [helpers.normalise_datetime(y) for x, y in timespans]

    return starts, ends

all_starts, all_ends = [], []
all_targets, all_codes = [], []
for target in targets:
    for code in status_codes:
        starts, ends = build_timespans()
        all_starts.extend(starts)
        all_ends.extend(ends)
        all_targets.extend([target] * len(ends))
        all_codes.extend([code] * len(ends))

c_starts = array.array('d', all_starts)
c_ends = array.array('d', all_ends)
c_codes = array.array('d', all_codes)
c_targets = array.array('d', all_targets)

content_lengths = [random.randrange(10, 2000) for _ in xrange(LENGTH)] * (len(targets) * len(codes))

start = time.time()
generated = stats.generate(zip(all_starts, all_ends), content_lengths)
generated_runtime = time.time() - start

start = time.time()
c_generated = cstats.generate(c_starts, c_ends, c_targets, c_codes, content_lengths)
c_generated_runtime = time.time() - start

for key in generated:
    expected, got = generated[key], c_generated.get(key, Sentinel)

    if expected == got:
        pass_fail = "\033[1m\033[92m[OK]\033[0m"
    else:
        if got is Sentinel:
            pass_fail = "\033[93m[Unimplemented]\033[0m"
        else:
            pass_fail = "\033[1m\033[91m[Fail]\033[0m"
            pass_fail += " Expected: %s, Got: %s" % (expected, got)
    print "%25s" % (key,), pass_fail

print; print
print "Run times:"
print "    Python:", "%.4f" % (generated_runtime,)
print "    Cython:", "%.4f" % (c_generated_runtime,)
