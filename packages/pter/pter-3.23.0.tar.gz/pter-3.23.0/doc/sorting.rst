Sorting
=======

Tasks can be sorted by passing ``sort:`` to the search. The properties of
tasks to sort by are separated by comma. The following properties can be
used for sorting:

  ``due_in``
    The number of days until the task is due, if there is a due
    date given.

  ``completed``
    Whether or not the task has been completed.

  ``completed_date``
    Completion date of the task

  ``priority``
    The priority of the task, if any.

  ``linenr``
    The line of the task in its todo.txt file

  ``file``
    The name of the todo.txt file the task is in.

  ``project``
    The first project (alphabetically sorted) of the task.

  ``context``
    The first context (alphabetically sorted) of the task.

  ``created``
    Creation date of the task.

The default sorting order is ``completed,due_in,priority,linenr`` and will
be assumed if no ``sort:`` is provided in the search. The default sorting order
can be configured with the ``[General]`` section's ``sort-order`` setting.
