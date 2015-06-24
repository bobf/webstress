from __future__ import unicode_literals

import datetime
import operator
import math
import itertools

import numpy

def nadir(L):
    return numpy.amin(L)

def peak(L):
    return numpy.amax(L)

def median(L):
    return numpy.median(L)

def mean(L):
    return numpy.mean(L)

def percentiles(L):
    return list(numpy.percentile(L, range(0, 110, 10)))

def std_deviation(L):
    return numpy.std(L)

def histogram(L):
    histogram, edges = numpy.histogram(L, 5)
    return {"histogram": list(histogram), "edges": list(edges)}

def normalise_datetime(dt, milliseconds=True):
    """
    Return milliseconds since epoch for a given datetime
    """
    epoch = datetime.datetime.utcfromtimestamp(0)
    x = (dt - epoch).total_seconds()
    if milliseconds:
        return x * 1000
    else:
        return x

# Borrowed from http://stackoverflow.com/a/8991553
def grouper(n, iterable):
    it = iter(iterable)
    while True:
       chunk = tuple(itertools.islice(it, n))
       if not chunk:
           return
       yield chunk

def calculate_tps(chunks):
    def to_nearest_second(v):
        return math.ceil(normalise_datetime(v[1], milliseconds=False))

    tps = []

    for start_time, durations in chunks:
        timespans = [x['timespan'] for x in durations]
        timespans.sort(key=to_nearest_second)
        groups = itertools.groupby(timespans, to_nearest_second)
        for key, timespan_group in groups:
            requests = list(timespan_group)
            tps.append((key * 1000, len(requests)))

    result = []
    for chunk in grouper(10, tps):
        end = max(x[0] for x in chunk)
        avg = mean([x[1] for x in chunk])
        result.append((end, avg))
    return result

def chart_points(timespans, durations, num_points=100):
    """
    Given a sequence of time spans and durations, calculate chart points for
    response time over time. Generate no more than `num_points` points - take
    peak time over `num_points` periods in time if input is > `num-points`
    """
    earliest = normalise_datetime(
        min(timespans, key=operator.itemgetter(0))[0])
    latest = normalise_datetime(
        max(timespans, key=operator.itemgetter(0))[0])

    if latest - earliest < 1:
        # All responses returned in < 1 second, show number of requests instead
        return {'type': 'linear',
                'title': 'Requests',
                'values': chart_points_linear(
                            durations,
                            num_points=num_points)
        }

    period = (latest - earliest) / num_points
    next_time = earliest + period
    chunk = []
    chunks = []
    for duration, timespan in zip(durations, timespans):
        if normalise_datetime(timespan[0]) > next_time:
            chunks.append((next_time - period, chunk))
            chunk = []
            next_time += period
        chunk.append({"duration": duration, "timespan": timespan})

    points = [ [start_time, peak([x['duration'] for x in chunk])]
               for start_time, chunk in chunks ]

    tps = calculate_tps(chunks)
    return {'type': 'datetime',
            'title': 'Time',
            'values': points,
            'tps': tps}

def chart_points_linear(L, num_points=100):
    """
    Calculate peaks for a given sequence of durations; don't care about
    timelining, just durations over requests
    """
    points = []
    chunks = []
    if len(L) <= num_points:
        return list(enumerate(L))

    chunk_size = len(L) / num_points

    for i in xrange(0, len(L), chunk_size):
        chunks.append(L[i:i + chunk_size])

    # Add remainder
    if L[i + chunk_size:]:
        chunks.append(L[i + chunk_size:])

    for i, chunk in enumerate(chunks):
        points.append([i * chunk_size, peak(chunk)])

    return points

def generate(timespans):
    """
    Generate statistics on given time spans. Expects a sequence of 2-element
    tuples (start, end) as datetime objects
    """
    durations = [(end - start).total_seconds()
                 for start, end in timespans]

    return {"nadir": nadir(durations),
            "peak": peak(durations),
            "median": median(durations),
            "mean": mean(durations),
            "percentiles": percentiles(durations),
            "std_deviation": std_deviation(durations),
            "histogram": histogram(durations),
            "chart_points": chart_points(timespans, durations),
            "count": len(durations),
    }
