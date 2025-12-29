Searching
=========

One of the most important parts of pter is the search. You can search for
tasks by means of search queries. These queries can become very long at
which point you can save and restore them.

Unless configured otherwise by you, the search is case-sensitive. Note that
case-sensitivity does not apply at all to: whether or not a task is hidden,
completion status, priority, or any date-related searches (due date, creation
date, completion date, threshold date).

If you configured the search to be smart about case-sensitivity, please consult
`Smart case-sensitive search`_ below for details.

Here's a detailed explanation of search queries.


Search for phrases
------------------

The easiest way to search is by phrase in tasks.

For example, you could search for ``read`` to find any task containing the word
``read`` or ``bread`` or ``reading``.

To filter out tasks that do *not* contain a certain phrase, you can search with
``not:word`` or, abbreviated, ``-word``.


Search for tasks that are completed
-----------------------------------

By default all tasks are shown, but you can show only tasks that are not
completed by searching for ``done:no``.

To only show tasks that you already marked as completed, you can search for
``done:yes`` instead.

If you want to express that any state is accepted, you could search for ``done:any``.


Hidden tasks
------------

Even though not specified by the todotxt standard, some tools provide the
“hide” flag for tasks: ``h:1``. pter understands this, too, and by default
hides these tasks.

To show only hidden tasks, search for ``hidden:yes`` (or ``hidden:1`` or even
just ``h:1``).

To show all tasks, no matter their hidden status, you can search for ``hidden:any`` or ``hidden:``.

The search phrase ``hidden:no`` is the default, but you can provide it if you feel like it.

Instead of searching for ``hidden:`` you can also search for ``h:`` (it’s a synonym).


Projects and Contexts
---------------------

To search for a specific project or context, just search using the
corresponding prefix, ie. ``+`` or ``@``.

For example, to search for all tasks for project "FindWaldo", you could search
for ``+FindWaldo``.

If you want to find all tasks that you filed to the context "email", search
for ``@email``.

Similar to the search for phrases, you can filter out contexts or projects by
search for ``not:@context``, ``not:+project``, or use the abbreviation ``-@context``
or ``-+project`` respectively.


Priority
--------

Searching for priority is supported in two different ways: you can either
search for all tasks of a certain priority, eg. ``pri:a`` to find all tasks of
priority ``(A)``.
Or you can search for tasks that are more important or less important than a
certain priority level.

Say you want to see all tasks that are more important than priority ``(C)``, you
could search for ``moreimportant:c``. The keyword for “less important” is
``lessimportant``.

``moreimportant`` and ``lessimportant`` can be abbreviated with ``mi`` and ``li``
respectively.


Due date
--------

Searching for due dates can be done in two ways: either by exact due date or
by defining “before” or “after”.

If you just want to know what tasks are due on 2018-08-03, you can search for
``due:2018-08-03``.

But if you want to see all tasks that have a due date set *after* 2018-08-03,
you search for ``dueafter:2018-08-03``.

Similarly you can search with ``duebefore`` for tasks with a due date before a
certain date.

``dueafter`` and ``duebefore`` can be abbreviated with ``da`` and ``db`` respectively.

If you only want to see tasks that have a due date, you can search for
``due:yes`` or ``due:any``. ``due:no`` also works if you don’t want to see any due dates.

Searching for due dates supports `Relative Dates`_.


Creation date
-------------

The search for task with a certain creation date is similar to the search
query for due date: ``created:2017-11-01``.

You can also search for tasks created before a date with ``createdbefore`` (can
be abbreviated with ``crb``) and for tasks created after a date with
``createdafter`` (or short ``cra``).

To search for tasks created in the year 2008 you could search for
``createdafter:2007-12-31 createdbefore:2009-01-01`` or short ``cra:2007-12-31
crb:2009-01-01``.

Searching for creation dates supports `Relative Dates`_.


Completion date
---------------

The search for tasks with a certain completion date is pretty much identical
to the search for tasks with a certain creation date (see above), but using
the search phrases ``completed``, ``completedbefore`` (the short version is ``cob``), or
``completedafter`` (short form is ``coa``).

Searching for completion dates supports `Relative Dates`_.


Threshold or Tickler search
---------------------------

pter understand the the non-standard suggestion to use ``t:`` tags to
indicate that a task should not be active prior to the defined date.

If you still want to see all tasks, even those with a threshold in the future,
you can search for ``threshold:any`` (or, short, ``t:any``). ``any`` is the same
as search for a standalone ``t:``.

To find all tasks that have a threshold, search for ``t:yes``. To only show tasks that have no threshold, use ``t:no``.

See also configuration option ``default-threshold``.

You can also pretend it’s a certain date in the future (eg. 2042-02-14) and
see what tasks become available then by searching for ``threshold:2042-02-14``.

``threshold`` can be abbreviated with ``t``. ``tickler`` is also a synonym for
``threshold``.

Searching for ``threshold`` supports `Relative Dates`_.


Task Identifier
---------------

You can search for task IDs with ``id:``. If you search for multiple
task IDs, all of these are searched for, not a task that has all given IDs.

You can also exclude tasks by ID from a search with ``not:id:`` or
``-id:``.


Sequence
--------

You can search for tasks that are supposed to follow directly or indirectly
other tasks by searching for ``after:taskid`` (``taskid`` should be the
``id`` of a task). Any task that is supposed to be completed after that
task, will be found.

If the configuration option ``hide-sequential`` is set to ``yes`` (the
default), tasks are hidden that have uncompleted preceding tasks.

If you want to see all tasks, disregarding their declared sequence, you can
search for ``after:`` (without anything after the ``:``).


Task References
---------------

Tasks that refer to other tasks by any of the existing means (eg. ``ref:``
or ``after:``) can be found by searching for ``ref:``.

If you search using multiple references (eg. ``ref:4,5`` or ``ref:4
ref:5``) the task IDs are considered a logical ``or``.


Filename
--------

You can search for parts of a filename that a task belongs to with
``file:``. ``not:`` (or ``-``) can be used to exclude tasks that belong to
a certain file.

For example: ``file:todo.txt`` or ``-file:archive``.


Smart case-sensitive search
---------------------------

You may set the ``search-case-sensitive`` configuration option to ``smart`` (see `pter.config(5)`_)
to change the case-sensitive search behaviour while pter is running.

If set to ``smart``, the search will:

 - search case-insensitive if your search only contains lower-case characters
 - switch to case-sensitive search for projects, contexts, phrases, ids, or filenames by group

"by group" means that the smart case-search is enabled per each of the groups.

For example, if you search for ``Some word +project``, all phrases (``Some`` and ``word``) will be
searched for in a case-sensitive manner, but projects will be searched for case-insensitive.

Another example that would search for projects case-sensitive but contexts in a case-insensitive
manner: ``+Project @context``.

Using inversions (``not`` or ``-``) will also affect the case-sensitivity for that group. For example,
``not:+Project +project`` will search case-sensitive for ``+project`` but will not yield ``+Project``.

The case-sensitivity setting for IDs is affecting all three ID-related searches: ``ref``, ``after``, and ``id``.
That means if you search for ``ref:Task1 after:task3``, the search for ``task3`` is considered case sensitive,
because ``Task1`` is upper-case.

