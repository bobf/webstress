import webstress.client.api
import webstress.config.parser

from twisted.python import log

def expose(f):
    f.exposed = True
    return f

class DelegateMeta(type):
    def __init__(cls, name, bases, namespace):
        super(DelegateMeta, cls).__init__(name, bases, namespace)
        # Create a _handlers class attribute on all subclasses
        cls._handlers = [
            v for
            v in cls.__dict__.values()
            if getattr(v, "exposed", False)
        ]


class Delegate(object):
    __metaclass__ = DelegateMeta

    def __init__(self):
        self.called = False

    def _call(self, method, args, kwargs):
        for handler in self._handlers:
            if handler.__name__ == method:
                response = handler(self, *args, **kwargs)
                self.called = True
                return response
        log.msg("Unhandled method: <%r> on %r" % (method, self))


class StressTestDelegate(Delegate):
    @expose
    def launch_test(self, requested_targets, _uid=None):
        if webstress.configuration.DEBUG:
            webstress.client.api.reload_config()

        targets = []
        for request in requested_targets:
            target = webstress.configuration.target_by_name(
                request["config"], request["name"])
            targets.append(target)

        return self.make_test_deferred(targets, _uid)

    @expose
    def launch_test_from_config(self, config_string, _uid=None):
        config = webstress.config.parser.Config(config_string)

        return self.make_test_deferred(config.targets)

    @expose
    def list_configs(self):
        configs = webstress.configuration.list_configs(to_json=True)
        self._transport.send("configs", *configs)

    def make_test_deferred(self, targets, _uid):
        def each_callback(result):
            self._transport.send("result", result.to_json(), **{u"_uid": _uid})
            return result
        def all_callback(results):
            self._transport.send("all_results",
                                 [x.to_json() for x in results],
                                 **{u"_uid": _uid})
            return results

        d = webstress.client.api.launch_tests(each_callback, targets=targets)
        d.addCallback(all_callback)

        return d
