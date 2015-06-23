from __future__ import unicode_literals

import datetime
import operator

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

def normalise_datetime(dt):
    """
    Return milliseconds since epoch for a given datetime
    """
    epoch = datetime.datetime.utcfromtimestamp(0)
    x = (dt - epoch).total_seconds() * 1000
    return x

def chart_points(time_spans, durations, num_points=100):
    """
    Given a sequence of time spans and durations, calculate chart points for
    response time over time. Generate no more than `num_points` points - take
    peak time over `num_points` periods in time if input is > `num-points`
    """
    earliest = normalise_datetime(
        min(time_spans, key=operator.itemgetter(0))[0])
    latest = normalise_datetime(
        max(time_spans, key=operator.itemgetter(0))[0])

    if latest - earliest < 1:
        # All responses returned in < 1 second, show number of requests instead
        return {'type': 'linear',
                'title': 'Requests',
                'values': chart_points_linear(
                            durations,
                            num_points=num_points)
        }

    if len(durations) <= num_points:
        # [duration, start time] for each L
        return {'type': 'datetime',
                'title': 'Time',
                'values': [ [normalise_datetime(t[0]), d]
                 for d, t in zip(durations, time_spans) ]
                }

    period = (latest - earliest) / num_points
    next_time = earliest + period
    chunk = []
    chunks = []
    for duration, time_span in zip(durations, time_spans):
        if normalise_datetime(time_span[0]) > next_time:
            chunks.append((next_time - period, chunk))
            chunk = []
            next_time += period
        chunk.append(duration)

    points = [ [start_time, peak(durations)]
               for start_time, durations in chunks ]

    tps = [ [start_time, len(durations)]
            for start_time, durations in chunks ]

    return {'type': 'datetime', 'title': 'Time', 'values': points, 'tps': tps}

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

def generate(time_spans):
    """
    Generate statistics on given time spans. Expects a sequence of 2-element
    tuples (start, end) as datetime objects
    """
    durations = [(end - start).total_seconds()
                 for start, end in time_spans]

    return {"nadir": nadir(durations),
            "peak": peak(durations),
            "median": median(durations),
            "mean": mean(durations),
            "percentiles": percentiles(durations),
            "std_deviation": std_deviation(durations),
            "histogram": histogram(durations),
            "chart_points": chart_points(time_spans, durations),
            "count": len(durations),
    }
