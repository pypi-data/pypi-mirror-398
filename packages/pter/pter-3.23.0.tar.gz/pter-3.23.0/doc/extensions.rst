Extensions to todo.txt
======================

Pter is fully compatible with the standard format, but also supports
the following extra key/value tags:

- ``after:4``, signifies that this entry can only be started once entry with ``id:4`` has been completed.
- ``due:2071-01-01``, defines a due date for this task.
- ``h:1``, hides a task.
- ``id:3``, allows you to assign a unique identifier to entries in the todo.txt, like ``3``. pter will accept when there non-unique IDs, but of course uniquely identifying entries will be tricky.
- ``rec:1w``, indicate that this task should be recurring in 1 week intervals.
- ``ref:6``, indicate that this task refers to the task with ``id:6``.  Comma-separated IDs are supported, like ``ref:13,9``.
- ``spent:5h3m``, pter can be used for time tracking and will store the time spent on a task in the ``spent`` attribute.
- ``t:2070-12-24``, the threshold tag can be used to hide before the given date has come.
- ``to:person``, when a task has been delegated (by using a delegation marker like ``@delegated``), ``to`` can be used to indicate to whom the task has been delegated. The option is configurable, see ``delegation-to`` above for details.
- ``tracking:``, a technical tag used for time tracking. It indicates that you started working on the task and wanted to do time tracking. The value is the date and time when you started working. Upon stopping tracking, the spent time will be stored in the ``spent`` tag.
- ``note:``, a filename with additional notes about this task
- both ``t:`` and ``due:`` may be full ISO 8601 date and time format, like ``2023-05-01T19:31:05+00:00``

