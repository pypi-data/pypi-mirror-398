Relative dates
==============

Instead of providing full dates for searches or for ``due:`` or ``t:`` when
editing tasks, you may write things like ``due:+4d``, for example, to specify
a date in 4 days.

A relative date will be expanded into the actual date when editing a task
or when being used in a search.

The suffix ``d`` stands for days, ``w`` for weeks, ``m`` for months, ``y`` for years.
The leading ``+`` is implied when left out and if you don’t specify it, ``d`` is
assumed.

``due`` and ``t`` tags can be as simple as ``due:1`` (short for ``due:+1d``, ie.
tomorrow) or as complicated as ``due:+15y-2m+1w+3d`` (two months before the date
that is in 15 years, 1 week and 3 days).

``due`` and ``t`` also support relative weekdays. If you specify ``due:sun`` it is
understood that you mean the next Sunday. If today is Sunday, this is
equivalent to ``due:1w`` or ``due:+7d``.

Finally there are ``today`` and ``tomorrow`` as shortcuts for the current day and
the day after that, respectively. These terms exist for readability only, as
they are equivalent to ``0d`` (or even just ``0``) and ``+1d`` (or ``1d``, or even
just ``1``), respectively.


Business days
-------------

You can use the ``b`` suffix in place of the ``d`` suffix to indicate that the
calculated date for ``due``, ``t``, or ``rec`` will fall on a business day.

In this case the sign before the ``b`` (``-`` or ``+``) will be used to find a
business day before or after the resulting date.

For example, assume today is 2024-11-07 (Thursday) and a new task "Write that big
document" is coming up, due on 2024-11-15 (next week Friday). You could use
``t:+2b`` to hide the task for 2 days. This would fall on a Saturday (2024-11-09),
but since you used the ``b`` suffix and not just ``d``, pter will find the next
business day and use that as the ``t`` date: 2024-11-11 (Monday).

Assume you want to ensure the task is made visible before it is due, you could
construct a task like this: ``due:+2w t:+2w-4b``. This would put the ``t`` at
least 4 business days before the due date, ensuring that you would see the task
pop up on a Friday, so it’s not sneaking up on you.

For example, if today is 2024-11-06 and a task is due in two weeks (Wednesday,
2024-11-20) you could create the task with ``due:+2w t:+2w-4d``, which would
put the ``t`` on 2024-11-17 (a Sunday). With ``t:+2w-4b`` the ``t`` would
instead be put on 2024-11-15 (Friday).

