========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - package
      - | |version| |wheel| |supported-versions|
.. |docs| image:: https://readthedocs.org/projects/robot-birdbrain/badge/?style=flat
    :target: https://robot-birdbrain.readthedocs.io/
    :alt: Documentation Status

.. |github-actions| image:: https://github.com/fmorton/robot-birdbrain/actions/workflows/github-actions.yml/badge.svg
    :alt: GitHub Actions Build Status
    :target: https://github.com/fmorton/robot-birdbrain/actions

.. |requires| image:: https://requires.io/github/fmorton/robot-birdbrain/requirements.svg?branch=main
    :alt: Requirements Status
    :target: https://requires.io/github/fmorton/robot-birdbrain/requirements/?branch=main

.. |codecov| image:: https://codecov.io/gh/fmorton/robot-birdbrain/branch/main/graphs/badge.svg?branch=main
    :alt: Coverage Status
    :target: https://codecov.io/github/fmorton/robot-birdbrain

.. |version| image:: https://img.shields.io/pypi/v/robot-birdbrain.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/robot-birdbrain

.. |wheel| image:: https://img.shields.io/pypi/wheel/robot-birdbrain.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/robot-birdbrain

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/robot-birdbrain.svg
    :alt: Supported versions
    :target: https://pypi.org/project/robot-birdbrain

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/robot-birdbrain.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/robot-birdbrain


.. end-badges

Rewritten Python Library for Birdbrain Technologies Hummingbird Bit and Finch 2

Rewrite inspired by https://github.com/BirdBrainTechnologies/BirdBrain-Python-Library

* Free software: GNU Lesser General Public License v3 (LGPLv3)

Installation
============

::

    pip install robot-birdbrain

You can also install the in-development version with::

    pip install https://github.com/fmorton/robot-birdbrain/archive/main.zip



Hummingbird Example
===================

.. code-block:: python

  from robot.hummingbird import Hummingbird
  from time import sleep

  hummingbird = Hummingbird('A')

  for i in range(0, 10):
    hummingbird.led(1, 100)
    sleep(0.1)

    hummingbird.led(1, 0)
    sleep(0.1)

    hummingbird.stop_all()



Finch Example
===================

.. code-block:: python

  from robot.finch import Finch
  from time import sleep

  finch = Finch('A')

  for i in range(0, 10):
    finch.beak(100, 100, 100)
    sleep(0.1)

    finch.beak(0, 0, 0)
    sleep(0.1)

  finch.stop_all()



Tasks Example (requires the robot-tasks package)
================================================

.. code-block:: python

  from robot.hummingbird import Hummingbird
  from robot.tasks import Tasks

  async def task_1(bird):
    while True:
      print("task_1 running")

      await Tasks.yield_task(1.0)


  async def task_2(bird):
    while True:
      print("task_2 running")

      await Tasks.yield_task(0.5)


  bird = Hummingbird("A")

  tasks = Tasks()

  tasks.create_task(task_1(bird))
  tasks.create_task(task_2(bird))

  tasks.run()



Original Documentation
=============================================

The original documentation from Birdbrain Technolgies can be found at:

Finch: https://learn.birdbraintechnologies.com/finch/python/library/

Hummingbird: https://learn.birdbraintechnologies.com/hummingbirdbit/python/library/


Testing
=======

To run all the tests run (hummingbird (with micro:bit v2) on 'A' and finch on 'B')::

    pytest
