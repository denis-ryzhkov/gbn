"""
Greenlet BottleNeck profiler.
Measures time precisely using "greenlet.settrace" to pause/continue counting time on switch from/to original greenlet.
May count wall-clock time too. Also counts step calls and context switches.

Usage:
    gbn_attach()

    gbn('step1')
    step1()

    gbn('step2')
    step2()

    wall = gbn('step3')
    step3()

    wall = gbn('step4', wall=wall)
    step4()

    gbn('step5', wall=wall)
    step5()

    gbn()
    does_not_count_this()

    log.info(gbn_report_and_reset())
    # OR
    spawn(gbn_report_and_reset, each=60, log=log.info)


gbn version 0.4.1
Copyright (C) 2016-2017 by Denis Ryzhkov <denisr@denisr.com>
MIT License, see http://opensource.org/licenses/MIT
"""

### import

from collections import defaultdict
from greenlet import getcurrent, settrace
from time import time, sleep

### state

state = dict(attached=False)

seconds_sum = {}
seconds_min = {}
seconds_max = {}

wall_seconds_sum = {}
wall_seconds_min = {}
wall_seconds_max = {}

calls = {}
switches = {}
other = dict(step='OTHER')  # Name of "OTHER" pseudo-step, that aggregates all NOT profiled greenlets.

### _save

def _save(step, seconds):
    """
    Save seconds and calls per step to state.
    """

    if step in seconds_sum:
        seconds_sum[step] += seconds
    else:
        seconds_sum[step] = seconds

    if step not in seconds_min or seconds_min[step] > seconds:
        seconds_min[step] = seconds

    if step not in seconds_max or seconds_max[step] < seconds:
        seconds_max[step] = seconds

    if step in calls:
        calls[step] += 1
    else:
        calls[step] = 1

def _save_wall(step, seconds):
    """
    Save wall-clock seconds per step to state.
    """

    if step in wall_seconds_sum:
        wall_seconds_sum[step] += seconds
    else:
        wall_seconds_sum[step] = seconds

    if step not in wall_seconds_min or wall_seconds_min[step] > seconds:
        wall_seconds_min[step] = seconds

    if step not in wall_seconds_max or wall_seconds_max[step] < seconds:
        wall_seconds_max[step] = seconds

### gbn_attach / gbn_detach

def gbn_attach():
    """
    Attach gbn to pause/continue counting time on switch from/to original greenlet.
    Please do it once before using gbn.
    """
    settrace(_gbn_tracer)
    state['attached'] = True

def gbn_detach():
    """
    Detach gbn to reduce overhead.
    Please do not use gbn after detach.
    """
    settrace(None)
    state['attached'] = False

### _gbn_tracer

def _gbn_tracer(event, args):
    if event == 'switch' or event == 'throw':
        origin, target = args
        now = time()

        ### pause counting

        if hasattr(origin, 'gbn'):
            step = origin.gbn
            origin.gbn_seconds += now - origin.gbn_start
        else:
            step = other['step']
            if 'start' in other:
                _save(other['step'], now - other.pop('start'))

        ### count switch

        if step in switches:
            switches[step] += 1
        else:
            switches[step] = 1

        ### continue counting

        if hasattr(target, 'gbn'):
            target.gbn_start = now
        else:
            other['start'] = now

### gbn

def gbn(new_step=None, wall=None):
    """
    Stop counting time of current step, if any.
    Start counting time of new step, if any.
    Each greenlet counts time independent of other greenlets.
    Returns "wall" anchor that may be passed to another gbn(wall=wall) to count wall-clock time too.

    @param new_step: str|None - name of new step, if any.
    @param wall: tuple(step: str, start: float)|None - previous wall-clock time anchor, if any.
    @return tuple(step: str, start: float)|None - new wall-clock time anchor.
    """
    if not state['attached']:
        return

    greenlet = getcurrent()
    now = time()

    if hasattr(greenlet, 'gbn'):
        _save(greenlet.gbn, greenlet.gbn_seconds + now - greenlet.gbn_start)
        if new_step is None:
            del greenlet.gbn, greenlet.gbn_start, greenlet.gbn_seconds

    if wall:
        step, start = wall
        _save_wall(step, now - start)

    if new_step is not None:
        greenlet.gbn = new_step
        greenlet.gbn_start = now
        greenlet.gbn_seconds = 0
        return new_step, now

### gbn_report_and_reset

def gbn_report_and_reset(
        step_format='{step}: {sum:.6f}:{min:.6f}..{avg:.6f}..{max:.6f} wall={wall_sum:.6f}:{wall_min:.6f}..{wall_avg:.6f}..{wall_max:.6f} calls={calls} switches={switches}',
        steps_separator=', ', sum_step='SUM', each=None, log=None):
    """
    Report and reset time counters.

    @param step_format: str - Format of report about one step.
    @param steps_separator: str - Separator of reports about multiple steps.
    @param sum_step: str - Name of "SUM" pseudo-step, that aggregates all steps together. See also: other['step'] = 'OTHER'
    @param each: int|None - If set to N, report and reset each N seconds to "log" function.
    @param log: callable(str)|None - Function to report to, when "each" is set. E.g. log=logging.getLogger('gbn').info

    Usage:
        log.info(gbn_report_and_reset())
        # OR
        spawn(gbn_report_and_reset, each=60, log=log.info)
    """

    while each:
        sleep(each)
        log(gbn_report_and_reset(step_format, steps_separator, sum_step))

    seconds_sum[sum_step] = sum(seconds_sum.itervalues())
    seconds_min[sum_step] = min(seconds_min.itervalues()) if seconds_min else 0
    seconds_max[sum_step] = max(seconds_min.itervalues()) if seconds_max else 0

    wall_seconds_sum[sum_step] = sum(wall_seconds_sum.itervalues())
    wall_seconds_min[sum_step] = min(wall_seconds_min.itervalues()) if wall_seconds_min else 0
    wall_seconds_max[sum_step] = max(wall_seconds_min.itervalues()) if wall_seconds_max else 0

    calls[sum_step] = sum(calls.itervalues())
    switches[sum_step] = sum(switches.itervalues())

    result = steps_separator.join(
        step_format.format(
            step=step,

            sum=seconds_sum_,
            min=seconds_min[step],
            avg=seconds_sum_ / calls[step] if calls[step] else 0,
            max=seconds_max[step],

            wall_sum=wall_seconds_sum.get(step, 0),
            wall_min=wall_seconds_min.get(step, 0),
            wall_avg=wall_seconds_sum[step] / calls[step] if calls[step] and step in wall_seconds_sum else 0,
            wall_max=wall_seconds_max.get(step, 0),

            calls=calls[step],
            switches=switches.get(step, 0),
        )
        for step, seconds_sum_ in sorted(seconds_sum.iteritems(), key=lambda x: -x[1])
    )

    seconds_sum.clear()
    seconds_min.clear()
    seconds_max.clear()

    wall_seconds_sum.clear()
    wall_seconds_min.clear()
    wall_seconds_max.clear()

    calls.clear()
    switches.clear()

    return result
