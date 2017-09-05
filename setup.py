from setuptools import setup

setup(
    name='gbn',
    version='0.4.3',
    description='Greenlet BottleNeck profiler.',
    long_description='''
Greenlet BottleNeck profiler.

Measures time precisely using "greenlet.settrace" to pause/continue counting time on switch from/to original greenlet.

May count wall-clock time too. Also counts step calls and context switches.

Usage::

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

See `help(gbn) <https://github.com/denis-ryzhkov/gbn/blob/master/gbn.py#L152>`_ for detailed docs.

Additional tools:

* `gxray <https://github.com/denis-ryzhkov/gbn/blob/master/gxray.py>`_ - Heavy profiler when you don't know where to profile.
* `gswitched <https://github.com/denis-ryzhkov/gbn/blob/master/gswitched.py>`_ - Checks if greenlet switched.
''',
    url='https://github.com/denis-ryzhkov/gbn',
    author='Denis Ryzhkov',
    author_email='denisr@denisr.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    py_modules=['gbn'],
    install_requires=[
        'greenlet',
    ]
)
