Task Sequences
==============

You can declare that a task is supposed to be done after another task has
been completed by setting the ``after:`` attribute to the preceding task.

By default, ie. with an empty search, any task that is declared to be
``after:`` some other preceding task will not be shown unless the preceding
task has been marked as done.

If you do not like this feature, you can disable it in the
``hide-sequential`` in the configuration file.


Examples
--------

These three tasks may exist::

  Buy potatoes @market id:1
  Make fries @kitchen id:2 after:1
  Eat fries for dinner after:2

This means that ``Make fries`` won’t show in the list of tasks until ``Buy
potatoes`` has been completed. Similarily ``Eat fries for dinner`` will not
show up until ``Make fries`` has been completed.

You can declare multiple ``after:`` attributes, or comma separate multiple
prerequisites to indicate that *all* preceding tasks must be completed
before a task may be shown::

  Buy oil id:1
  Buy potatoes id:2
  Buy plates id:3
  Make fries id:4 after:1,2
  Eat fries after:3 after:4

In this case ``Make fries`` will not show up until both ``Buy oil`` and
``Buy potatoes`` has been completed.

Similarly ``Eat fries`` requires both tasks, ``Make fries`` and ``Buy
plates``, to be completed.

