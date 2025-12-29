Unique Task Identifiers
=======================

Tasks can be given an identifier with the ``id:`` attribute. pter can
support you in creating unique IDs by creating a task with ``id:#auto`` or,
shorter, ``id:#``.

If you would like to group your tasks IDs, you can provide a prefix to the
id::

  Clean up the +garage id:clean3

If you now create a task with ``id:clean#`` or ``id:clean#auto``, the next
task will be given ``id:clean4``.

In case you want all your tasks to be created with a unique ID, have a look
at the configuration option ``auto-id``.

You can refer to other tasks using the attribute ``ref:`` following the id
of the task that you are referring to. This may also be a comma separated
list of tasks (much like ``after:``, see `Task Sequences`_).

You may use the ``show-related`` function (by default on the key ``r``) to
show the tasks that this task is referring to by means of ``ref:`` or
``after:``.

