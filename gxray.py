"""
Greenlet X-Ray profiler.
Heavy profiler when you don't know where to profile.

Usage:
    gxray_attach()
    spawn(gxray_report_and_reset, each=600)

gxray version 0.1.0
Copyright (C) 2016 by Denis Ryzhkov <denisr@denisr.com>
MIT License, see http://opensource.org/licenses/MIT
"""

### import

from collections import defaultdict
import greenlet
from greenlet import getcurrent
import os
from time import clock, sleep
import sys

### config

_count_stacks = False
_cumulative = False
_grep = None
_libs_path = greenlet.__file__[:greenlet.__file__.index('greenlet')]

### state

seconds_by_spots = defaultdict(float)
calls_by_spots = defaultdict(int)

seconds_by_stacks = defaultdict(float)
calls_by_stacks = defaultdict(int)

### gxray_attach

def gxray_attach(count_stacks=False, cumulative=False, grep=None):
    """
    Attach and configure gxray:

    @param count_stacks: bool - Count stacks of each spot to understand who calls this spot and how time is distributed.
    @param cumulative: bool - Show cumulative time: spot itself + everything called by this spot.
    @param grep: tuple(file_name: str, first_line_number: int, func_name: str)|None - Count only this spot and everything called by this spot.
    """
    global _count_stacks, _cumulative, _grep
    _count_stacks, _cumulative, _grep = count_stacks, cumulative, grep
    greenlet.settrace(_tracer)
    sys.setprofile(_profiler)

### gxray_detach

def gxray_detach():
    greenlet.settrace(None)
    sys.setprofile(None)

### _profiler

def _profiler(frame, event, arg):
    if event == 'call' or event == 'return':
        now = clock()
        g = getcurrent()
        stack = getattr(g, 'xstack', None)

        ### on call

        if event == 'call':

            ### save previous seconds

            if stack:
                _save_seconds(stack, now - g.xstart)

            ### push to stack

            code = frame.f_code
            spot = (code.co_filename, code.co_firstlineno, code.co_name)
            if stack is not None:
                stack.append(spot)
            else:
                g.xstack = stack = [spot]

            ### save current call

            if not _grep or _grep in stack:
                calls_by_spots[spot] += 1
                if _count_stacks:
                    calls_by_stacks[tuple(stack)] += 1

        ### on return

        elif stack:
            _save_seconds(stack, now - g.xstart)
            stack.pop()

        ### reset timer

        g.xstart = now

### _tracer

def _tracer(event, args):
    if event == 'switch' or event == 'throw':
        origin, target = args
        now = clock()

        ### save current seconds

        stack = getattr(origin, 'xstack', None)
        if stack:
            _save_seconds(stack, now - origin.xstart)

        ### reset timer

        target.xstart = now

### _save_seconds

def _save_seconds(stack, seconds):
    if _grep and _grep not in stack:
        return
    seconds_by_spots[stack[-1]] += seconds
    if _cumulative:
        for parent in stack[:-1]:
            seconds_by_spots[parent] += seconds
    if _count_stacks:
        seconds_by_stacks[tuple(stack)] += seconds
        if _cumulative:
            for parent in xrange(1, len(stack)):
                seconds_by_stacks[tuple(stack[:parent])] += seconds

### gxray_report_and_reset

def gxray_report_and_reset(
    each=600,                                                   # Report and reset each N seconds.
    path_format='/tmp/{pid}.gxray',                             # File path to save report to. May contain {pid} placeholder.

    total='TOTAL',                                              # Name of "TOTAL" pseudo-spot, that aggregates all spots together.
    counters_format='{seconds:.6f}/{calls}={avg:.6f} ',          # Format of counters.
    spot_format='{file_name}:{line_number} {func_name}',     # Format of one spot.
    lines_separator='\n',                                       # Separator between two lines of report.

    # The next options apply only if "count_stacks" is set to True:
    stack_indent=' ' * 4,                                       # Indent to group stacks of one spot.
    stack_separator=' < ',                                      # Separator between two spots in one stack.
    stacks_for_top_spots=20,                                    # Report stacks only for N top spots.
    stacks_per_spot=10,                                         # Report only N top stacks per spot.
):
    while 1:
        sleep(each)

        ### total

        if not _cumulative:
            total_spot = ('', '', total)
            seconds_by_spots[total_spot] = sum(seconds_by_spots.itervalues())
            calls_by_spots[total_spot] = sum(calls_by_spots.itervalues())

        ### prepare report

        sorted_spots_and_seconds = sorted(seconds_by_spots.iteritems(), key=lambda x: -x[1])
        report = []

        for spot_index, (spot, seconds) in enumerate(sorted_spots_and_seconds):
            report.append(
                counters_format.format(seconds=seconds, calls=calls_by_spots[spot], avg=seconds / calls_by_spots[spot] if calls_by_spots[spot] else 0) +
                spot_format.format(file_name=spot[0].replace(_libs_path, ''), line_number=spot[1], func_name=spot[2])
            )

            ### stacks

            if _count_stacks and spot_index < stacks_for_top_spots:
                stacks_and_seconds_of_this_spot = ((stack, seconds) for stack, seconds in seconds_by_stacks.items() if stack[-1] == spot)
                for stack, seconds in sorted(stacks_and_seconds_of_this_spot, key=lambda x: -x[1])[:stacks_per_spot]:
                    report.append(
                        stack_indent +
                        counters_format.format(seconds=seconds, calls=calls_by_stacks[stack], avg=seconds / calls_by_stacks[stack] if calls_by_stacks[stack] else 0) +
                        stack_separator.join(
                            spot_format.format(file_name=spot[0].replace(_libs_path, ''), line_number=spot[1], func_name=spot[2])
                            for spot in reversed(stack)
                        )
                    )
                report.append('')

        ### reset

        seconds_by_spots.clear()
        calls_by_spots.clear()
        seconds_by_stacks.clear()
        calls_by_stacks.clear()

        ### save report

        with open(path_format.format(pid=os.getpid()), 'w') as f:
            f.write(lines_separator.join(report))
