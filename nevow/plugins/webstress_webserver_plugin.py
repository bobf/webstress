from nevow import athena
from nevow import athena, loaders, tags as T
from nevow import athena, loaders, tags as T
from twisted.python import util

import webstress

# http://blackjml.livejournal.com/21602.html
def _f(*sib):
    return util.sibpath(webstress.__file__, '/'.join(sib))

myPackage = athena.JSPackage({
    'TransportMaker': _f('static', 'js', 'transport_maker.js'),
    'Transport': _f('static', 'js', 'transport.js'),
    })

