"""
Checks if greenlet switched.

Usage:
    with gswitched() as g:
        # code
    print(g.switched)

gswitched version 0.1.0
Copyright (C) 2017 by Denis Ryzhkov <denisr@denisr.com>
MIT License, see http://opensource.org/licenses/MIT
"""

import greenlet

_stack = []

def _on_switch(event, args):
    if event == 'switch' or event == 'throw':
        g, _ = args
        g.switched = True

class gswitched(object):

    def __enter__(self):
        g = greenlet.getcurrent()
        g.switched = False
        _stack.append(greenlet.settrace(_on_switch))
        return g

    def __exit__(self, exc_type, exc_val, exc_tb):
        greenlet.settrace(_stack.pop())

### tests

def tests():

    import gevent.monkey
    gevent.monkey.patch_all()

    import time

    with gswitched() as g:
        time.sleep(2)
    assert g.switched

    with gswitched() as g:
        for x in xrange(15**4):
            2 ** x
    assert not g.switched

    print('OK')

if __name__ == '__main__':
    tests()
