import hashlib

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

