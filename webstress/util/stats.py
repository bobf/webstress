from __future__ import unicode_literals

from twisted.protocols.amp import AmpBox, String, Integer, Float, DateTime

from webstress.util import helpers
from webstress.util.helpers import normalise_datetime

import sys
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
    values, edges = numpy.histogram(L, 5)
    return list(values), list(edges)

def sum(L):
    """
    Maybe numpy is faster than built-in sum ... ?
    """
    return numpy.sum(L)

# Borrowed from http://stackoverflow.com/a/8991553
def grouper(n, iterable):
    it = iter(iterable)
    while True:
       chunk = tuple(itertools.islice(it, n))
       if not chunk:
           return
       yield chunk

def calculate_tps(timespans, durations, max_points=20):
    """
    Calculate [completed] Transactions Per Second given a set of timespans and
    durations.

    Returns chart points based over time and the mean
    """
    def to_nearest_second(v):
        return math.ceil(normalise_datetime(v[1], milliseconds=False))

    tps = []

    groups = itertools.groupby(timespans, to_nearest_second)
    for key, timespan_group in groups:
        requests = list(timespan_group)
        tps.append((normalise_datetime(requests[0][1]), len(requests)))

    end = max( timespans, key=lambda x: x[1] )[1]
    start = min( timespans, key=lambda x: x[1] )[1]

    avg = len(timespans) / (end - start).total_seconds()

    points = []
    for chunk in grouper((len(tps) / max_points) or 1, tps):
        plot_x = chunk[0][0]
        plot_y = mean([x[1] for x in chunk])
        points.append({'x': plot_x, 'y': plot_y})

    return {'points': points, 'mean': avg}

def chart_points(timespans, durations, num_points=100):
    """
    Given a sequence of time spans and durations, calculate chart points for
    response time over time. Generate no more than `num_points` points - take
    peak time over `num_points` periods in time if input is > `num-points`
    """
    timespans.sort(key=operator.itemgetter(1))

    earliest = normalise_datetime(
        min(timespans, key=operator.itemgetter(1))[1])
    latest = normalise_datetime(
        max(timespans, key=operator.itemgetter(1))[1])

    if latest - earliest < 1:
        # All responses returned in < 1 second, show number of requests instead
        return {'x_axis_type': 'linear',
                'x_axis_title': 'Requests',
                'points': chart_points_linear(
                            durations,
                            num_points=num_points),
                'tps': {}
        }

    tps = calculate_tps(timespans, durations)

    average_period = (latest - earliest) / num_points
    periods = iter([
        (
          earliest + (i * average_period),
          earliest + ((i + 1) * average_period)
        ) for i in xrange(num_points)])

    chunk = []
    points = []

    timespans = iter((normalise_datetime(s), normalise_datetime(e))
                      for s, e in timespans)

    start, end = timespans.next()
    for lower_limit, upper_limit in periods:
        chunk = []
        while lower_limit <= end < upper_limit:
            chunk.append(end - start)
            try:
                start, end = timespans.next()
            except StopIteration:
                break
        if chunk:
            points.append({'x': upper_limit, 'y': peak(chunk) / 1000})

    return {'x_axis_type': 'datetime',
            'x_axis_title': 'Time',
            'points': points,
            'tps': tps}

def chart_points_linear(L, num_points=100):
    """
    Calculate peaks for a given sequence of durations; don't care about
    timelining, just durations over requests
    """
    points = []
    chunks = []
    if len(L) <= num_points:
        return [{'x': i, 'y': v} for i, v in enumerate(L)]

    chunk_size = len(L) / num_points

    for i in xrange(0, len(L), chunk_size):
        chunks.append(L[i:i + chunk_size])

    # Add remainder
    if L[i + chunk_size:]:
        chunks.append(L[i + chunk_size:])

    for i, chunk in enumerate(chunks):
        points.append({'x': i * chunk_size, 'y': peak(chunk)})

    return points

def generate(timespans, content_lengths):
    """
    Generate statistics on given time spans.

    `timespans` expects a sequence of 2-element tuples (start, end) as datetime
    objects

    `content_lengths` expects a sequence of integers
    """
    durations = [(end - start).total_seconds()
                 for start, end in timespans]

    histogram_values, histogram_edges = histogram(durations)

    chart = chart_points(timespans, durations)

    tps_mean = chart['tps'].get('mean', 0)
    tps_points = chart['tps'].get('points', [])

    return {"nadir": nadir(durations),
            "peak": peak(durations),
            "median": median(durations),
            "mean": mean(durations),
            "percentiles": percentiles(durations),
            "std_deviation": std_deviation(durations),
            "histogram_edges": histogram_edges,
            "histogram_values": histogram_values,
            "count": len(durations),
            "tps_mean": tps_mean,
            "tps_points": tps_points,
            "chart_x_axis_type": chart["x_axis_type"],
            "chart_x_axis_title": chart["x_axis_title"],
            "response_time_points": chart["points"],
            "total_content_length": sum(content_lengths),
    }
