import twisted.protocols.amp as amp
from twisted.python import log

import ampoule.child

from webstress.util import stats
from webstress.util.helpers import amp_safe

from datetime import datetime


class UpdateStats(amp.Command):
    arguments = [
        ("uid", amp.String()),
        ("category", amp.String()),
        ("target", amp.String()),
        ("start_time", amp.DateTime()),
        ("end_time", amp.DateTime()),
    ]
    response = [('success', amp.Boolean())]

class CalculateStats(amp.Command):
    arguments = [
        ("uid", amp.String()),
    ]
    response = [
        ('response_times',
            amp.AmpList([
                ('name', amp.String()),
                ('results',
                    amp.AmpList([
                        ('code', amp.String()),
                        ('count', amp.Integer()),
                        ('std_deviation', amp.Float()),
                        ('mean', amp.Float()),
                        ('median', amp.Float()),
                        ('nadir', amp.Float()),
                        ('peak', amp.Float()),
                        ('percentiles', amp.ListOf(amp.Float())),
                        ('histogram_edges', amp.ListOf(amp.Float())),
                        ('histogram_values', amp.ListOf(amp.Integer())),
                        ('tps_mean', amp.Float()),
                        ('tps_points',
                            amp.AmpList([
                                ('x', amp.Float()),
                                ('y', amp.Float()),
                            ])
                        ),
                        ('response_time_points',
                            amp.AmpList([
                                ('x', amp.Float()),
                                ('y', amp.Float()),
                            ])
                        ),
                        ('chart_x_axis_type', amp.String()),
                        ('chart_x_axis_title', amp.String()),
                ])),
            ]),
        )
    ]

class StatsAMP(ampoule.child.AMPChild):
    """
    I run in a child process and respond to calls from my parent to update and
    calculate statistics.
    """
    def __init__(self):
        self.timings = {}

    @UpdateStats.responder
    def update(self, uid, category, target, start_time, end_time):
        """
        Store a response round trip-time statistic
        """
        self.timings.setdefault(uid, {}).setdefault(target, {}
            ).setdefault(category, []
            ).append((start_time, end_time))

        self.timings[uid].setdefault('__all__', {}
            ).setdefault(category, []
            ).append((start_time, end_time))

        return {'success': True}

    @CalculateStats.responder
    def calculate(self, uid):
        """
        Iterate over all stored response times and calculate various statistics
        on them.

        Data structure is a bit of a faff in order to placate AMP.
        """
        statistics = []
        for target in self.timings[uid]:
            results = []
            target_stats = {'name': target, 'results': results}
            statistics.append(target_stats)
            all_time_spans = []
            for key in self.timings[uid][target]:
                time_spans = self.timings[uid][target][key]

                generated = stats.generate(time_spans)
                generated['code'] = key

                results.append(generated)

                all_time_spans.extend(time_spans)

            # All status codes, rather than breakdown above
            all_code_stats = {'name': target, 'results': []}

            generated = stats.generate(all_time_spans)
            generated['code'] = '__all__'

            results.append(generated)

        return amp_safe({'response_times': statistics})

class Statistician(object):
    """
    I abstract away all the IPC/process-spawning and provide a simple async
    interface to updating and calculating statistics.
    """
    def __init__(self):
        self.child, self.finished = self.start_process()

    def start_process(self):
        starter = ampoule.main.ProcessStarter()
        child, finished = starter.startAMPProcess(StatsAMP)
        return child, finished

    def errback(self, method, failure):
        """
        Catch-all errback to make sure I don't die when a remote call goes
        wrong.
        """
        log.msg("Statistician subprocess got an error on '%s': %s" % (method, failure))

    def calculate(self, data):
        """
        Request a statistics calculation
        """
        d = self.child.callRemote(CalculateStats, **amp_safe(data))
        d.addErrback(self.errback, "calculate")
        return d

    def update(self, data):
        """
        Send data to my worker process
        """
        d = self.child.callRemote(UpdateStats, **amp_safe(data))
        d.addErrback(self.errback, "update")
        return d

