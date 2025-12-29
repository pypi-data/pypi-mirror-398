Recurring Tasks
===============

Recurring (or repeating) tasks can be indicated by adding the ``rec:`` tag
and a `Relative Dates`_ specifier, like this::

  A weekly task rec:1w
  Do this again in 3 days rec:3d

By marking such a task as done, a new task will be added with the same
description, but a new creation date.

If you’d rather not have pter create new tasks every time, you can set the
``reuse-recurring`` option in the configuration file to ``yes``.

Recurring tasks usually only have meaning when a ``due:`` date is given,
but when there is no ``due:``, a ``t:`` will be used as a fallback if there
is any.

When completing such a task, pter can either create the follow-up task
based on the date of completion or based on the due date of the task. This
behaviour called the "recurring mode" which can be either

 - strict: the new due date is based on the old due date, or
 - normal: the new due date is based on the completion date.

To use strict mode, add a ``+`` before the time interval. For example you would
write ``rec:+2w`` for strict mode and ``rec:2w`` for normal mode.

An example. Given this task (starting June, you want to rearrange your
flowers in the living room every week)::

  2021-06-01 Rearrange flowers in the living room due:2021-06-05 rec:1w

In strict mode (``rec:+1w``), if you complete that task already on
2021-06-02, the next due date will be 2021-06-13 (old due date + 1 week).
But in normal mode (``rec:1w``) the new due date will be 2021-06-09 (date of
completion + 1 week).

If your recurring tasks has a due date and a threshold/tickler tag
(``t:``), upon completion the new task will also receive a ``t:`` tag with
the same relative time to the due date as the original task.

So, if you set up a due date 2021-06-05 and a threshold ``t:2021-06-04``
the new task will also have a threshold in such a way that the task is
hidden until one day before the due date.

