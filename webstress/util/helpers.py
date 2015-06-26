import hashlib
from datetime import datetime

from twisted.protocols import amp

def appendable(key, value):
    if isinstance(value, dict):
        return appendable(key, _hash_dict(value))
    elif isinstance(value, list):
        return tuple(appendable(None, x) for x in value)
    else:
        return hash((key, value))

def _hash_dict(d):
    hashable = []
    for key, value in sorted(d.items()):
        if key == 'uid':
            # If we hash based on the stored UID then we never get anywhere
            continue
        hashable.append(str(appendable(key, value)))

    return ''.join(hashable)

def hash_dict(d):
    return unicode(hashlib.sha1(_hash_dict(d)).hexdigest())

def normalise_datetime(dt, milliseconds=True):
    """
    Return milliseconds since epoch for a given datetime
    """
    epoch = datetime.utcfromtimestamp(0).replace(tzinfo=amp.utc)
    x = (dt - epoch).total_seconds()
    if milliseconds:
        return x * 1000
    else:
        return x

def denormalise_datetime(milliseconds):
    return datetime.utcfromtimestamp(milliseconds / 1000)

def traps(*failures):
    """
    Call `failure.trap(*failures)` before this function is called to raise any
    failures we don't want to deal with.

    @traps(ValueError)
    def foo(failure):
        print "i like value errors"

    is the same as:

    def foo(failure):
        failure.trap(ValueError)
        print "i like value errors"

    """
    from twisted.python.failure import Failure

    def get_trap(args):
        trap = None
        if len(args) >= 2 and isinstance(args[1], Failure):
            trap = args[1].trap

        if args and isinstance(args[0], Failure):
            # Always take the first param as the actual Failure, even if second
            # param is also a Failure
            trap = args[0].trap

        return trap

    def closure(f):
        def called(*a, **kw):
            trap = get_trap(a)
            if trap is not None:
                trap(*failures)
            return f(*a, **kw)
        return called
    return closure

def amp_safe(obj, encoding='utf8'):
    """
    Encode any unicode to bytestrings in any dict, list or unicode string.
    Will leave anything non-unicode as-is.

    twisted.protocols.amp should do this for me ?
    """
    return _make_safe(obj, encode=True, encoding=encoding)

def athena_safe(obj, encoding='utf8'):
    """
    Do the opposite of amp_safe because Athena hates bytestrings as much as AMP
    hates unicode. :(
    """
    return _make_safe(obj, encode=False, encoding=encoding)

def _make_safe(obj, encode=True, encoding='utf8'):
    """
    Make an object safe for something by encoding/decoding its contents
    recursively - helper for `athena_safe` and `amp_safe`
    """
    if isinstance(obj, dict):
        d = {}
        for k, v in obj.iteritems():
            v = _make_safe(v, encode=encode, encoding=encoding)
            if isinstance(k, unicode) and encode:
                d[k.encode(encoding)] = v
            elif isinstance(k, str) and not encode:
                d[k.decode(encoding)] = v
            else:
                d[k] = v
        obj = d
    elif isinstance(obj, list):
        for i, el in enumerate(obj):
            obj[i] = _make_safe(el, encode=encode, encoding=encoding)
    elif isinstance(obj, unicode) and encode:
        obj = obj.encode(encoding)
    elif isinstance(obj, str) and not encode:
        obj = obj.decode(encoding)
    elif isinstance(obj, datetime) and obj.tzinfo is None:
        # AMP balks at naive datetime types so we use its helpful pre-cooked
        # tzinfo
        obj = obj.replace(tzinfo=amp.utc)
    return obj
