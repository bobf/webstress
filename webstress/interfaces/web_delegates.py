import webstress.client.api

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

    def _call(self, method, *args, **kwargs):
        for handler in self._handlers:
            if handler.__name__ == method:
                response = handler(self, *args, **kwargs)
                self.called = True
                return response



class StressTestDelegate(Delegate):
    @expose
    def launch_test(self, targets):
        targets = [webstress.configuration.by_name(x) for x in targets]
        def each_callback(result):
            self._transport.send("result", result)
            return result
        def all_callback(results):
            self._transport.send("all_results", results)
            return results

        d = webstress.client.api.launch_tests(each_callback, targets=targets)
        d.addCallback(all_callback)

        return d
