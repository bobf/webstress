from cpython cimport array as c_array
from array import array
import math
import numpy as np

def generate(starts, ends, targets, codes, content_lengths):
    cdef c_array.array durations = array('d', [y - x for x, y in zip(starts, ends)])

    cdef double peak = 0 
    cdef double nadir = 0
    cdef double total = 0
    cdef double mean = 0

    cdef int i = 0
    cdef int durations_l = len(durations)
    cdef int first = 1
    cdef double current

    cdef double M = 0.0
    cdef double S = 0.0
    cdef double tmpM

    for i in range(durations_l):
        current = durations[i]

        total += current

        if first == 1:
            nadir = current

        if current > peak:
            peak = current

        if current < nadir:
            nadir = current

        tmpM = M
        M += (current - tmpM) / (i + 1)
        S += (current - tmpM ) * (current - M)

        first = 0
    
    mean = total / durations_l

    # http://stackoverflow.com/a/897463
    std_deviation = math.sqrt(S / (durations_l))

    median = np.median(durations)
    
    return {
        "peak": peak,
        "nadir": nadir,
        "mean": mean,
        "std_deviation": std_deviation,
        "median": median,
        "count": durations_l,
        "total_content_length": sum(content_lengths),
    }
