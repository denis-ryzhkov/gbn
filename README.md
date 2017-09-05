gbn
===

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

See [help(gbn)](https://github.com/denis-ryzhkov/gbn/blob/master/gbn.py#L147) for detailed docs.

Additional tools:
* [gxray](https://github.com/denis-ryzhkov/gbn/blob/master/gxray.py) - Heavy profiler when you don't know where to profile.
* [gswitched](https://github.com/denis-ryzhkov/gbn/blob/master/gswitched.py) - Checks if greenlet switched.

gbn version 0.4.3  
Copyright (C) 2016-2017 by Denis Ryzhkov <denisr@denisr.com>  
MIT License, see http://opensource.org/licenses/MIT
