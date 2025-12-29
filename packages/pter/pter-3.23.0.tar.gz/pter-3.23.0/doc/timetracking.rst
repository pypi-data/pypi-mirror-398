Time Tracking
=============

pter can track the time you spend on a task. By default, type "t" to
start tracking. This will add a ``tracking:`` attribute with the current local
date and time to the task.

When you select that task again and type "t", the ``tracking:`` tag will be
removed and the time spent will be saved in the tag ``spent:`` as hours and
minutes.

If you start and stop tracking multiple times, the time in ``spent:`` will
accumulate accordingly. The smallest amount of time tracked is one minute.


Tracking Using an External Program
----------------------------------

If you do your time tracking in an external program, you can configure pter to
use that program instead of doing it's internal tracking.

The configuration option ``time-tracking`` in the ``[General]`` section should
be pointed to the program that you want to use.

Please find all details in the configuration documentation `pter.config(5)`_.
