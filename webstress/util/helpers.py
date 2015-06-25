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
