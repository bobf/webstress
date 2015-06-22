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
    return {u"histogram": list(histogram), u"edges": list(edges)}

def chart_points(L, num_points=100):
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
