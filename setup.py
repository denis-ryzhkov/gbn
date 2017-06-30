from distutils.core import setup

setup(
    name='gbn',
    version='0.4.0',
    description='Greenlet BottleNeck profiler.',
    long_description='''
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
)