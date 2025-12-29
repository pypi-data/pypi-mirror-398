====
pter
====
-----------------------------
Personal Task Entropy Reducer
-----------------------------

Synopsis
========

::

  pter [-h] [-v] [-u] [-k] [-n task] [-s search] [-c configuration] filename [filename ...]


Description
===========

pter is a tool to manage your tasks when they are stored in the todo.txt
file format. pter is targeted at users applying the `Getting Things Done`_
method, but can be used by anyone that uses todo.txt files.

pter offers these features:

 - Fully compatible to the todo.txt standard
 - Support for `due:`, `t:` (threshold date), `h:` (hide task)
 - Extensive search/filter capabilities (see `Searching`_)
 - Save and recall search queries for quick access (see `Named Searches`_)
 - Sort tasks through search queries (see `Sorting`_)
 - Convenient entering of dates (see `Relative Dates`_)
 - Task sequencing (see `Task Sequences`_)
 - Task templates (see `Task Templates`_)
 - Automatic identifiers (see `Unique Task Identifiers`_)
 - Track time spent per task (see `Time Tracking`_)
 - Support for `Recurring Tasks`_
 - Detailed notes per task (see `Task Notes`_)
 - Highly configurable behaviour, shortcuts, and colors (see `Configuration Files`_)

qpter is the Qt version of pter (ie. pter with a graphical user interface)
and supports mostly the same features but sometimes looks for other
sections in the configuration. For more details, see the `dedicated documentation
for qpter <doc/qpter.rst>`_ or the `qpter man page <man:qpter>`_.


Options
=======


  ``-c configuration``
    Path to the configuration file you wish to use. The default is
    ``$XDG_CONFIG_HOME/pter/pter.conf`` (usually
    ``~/.config/pter/pter.conf``).

  ``-h``
    Show the help.

  ``-v``
    Show the version of pter/qpter.

  ``-u``
    Check whether a new version of pter is available on pypi (requires an
    internet connection).

  ``-k``
    List all key bindings and exit.

  ``-n task``
    Add ``task`` to the todo.txt file. The advantage of using this over
    just ``echo "task" >> todo.txt`` is that relative dates are properly
    expanded (see `Relative Dates`_).
    If you provide ``-`` instead of a task, the task will be read from
    stdin. Multiple tasks can be added, one per line.

    If you don't provide a todo.txt file on the commandline, the first file
    from the ``files`` option in your configuration file will be used.

  ``-s search``
    Load this named search upon startup. If a named search by that name does
    not exist, use this as a search term from the start.

  ``-l``
    Log level. Can be one of ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``,
    or ``FATAL``. Defaults to ``ERROR``.

  ``--log-file``
    In what file to log the messages. This is also the file where you can
    find information about crashes, if you encounter any.

  ``filename``
    Path to your todo.txt file. The first file that you provide is the one
    where new tasks will be created in.
    You may choose to not provide any files here. In that case the files
    configured in the ``[General]`` section (in ``files``) will be loaded.



Configuration Files
===================

.. include:: pter_cnf_summary.rst


User Interface and Help
=======================

The user interface consists of three main parts:

 1. The top row is the currently active search (see `Searching`_)
 2. The middle part is a list of all tasks
 3. The bottom row shows a contextual help based on what you're currently working on

There is a full list of all keybindings available when you press ``?``.


Clipboard Support
=================

In the commandline you can easily copy tasks to the clipboard (by default with
`Y`). This functionality depends on the programs ``xsel`` (X11), ``xclip`` (X11),
``wl-copy`` (wayland) or ``tmux`` (terminal) being installed.

pter will attempt to copy the text of the selected task to all of these programs.

If you are running pter in tmux, the copied task will be available via ``tmux saveb``
(default binding in tmux is ``C-b ]``).


.. include:: relative_dates.rst

.. include:: searching.rst

.. include:: sorting.rst


Named Searches
==============

Search queries can become very long and it would be tedious to type them
again each time.

To get around it, you can save search queries and give each one a name. The
default keyboard shortcut to save a search is "s" and to load a search is
"l".

The named queries are stored in your configuration folder in the file
``~/.config/pter/searches.txt``.

Each line in that file is one saved search query in the form ``name = search
query``.

Here are some useful example search queries::

  Due this week = done:no duebefore:mon
  Done today = done:yes completed:0
  Open tasks = done:no


Task Templates
==============

Manual templates
----------------

When using todo.txt files for project planning it can be very tedious to type
due dates, time estimates project and context, tickler values, custom tags, 
etc for every task. Another scenario is if a certain type of task comes up on 
a regular basis, e.g. bugfixes.

To get around typing out the task every time, you can edit a file stored in your
configuration folder ``~/.config/pter/templates.txt``. The syntax is identical to
the ``searches.txt`` file. Alternatively an existing task can be saved as a template.

Each line in that file is one saved template in the form ``name = task template``.

The default keyboard shortcut to load a template is "L", to set no template, select
the ``None`` template. To save an existing task the default key is "S". Once a 
template has been selected any new task created will contain the template text when
editing starts.

Here are some useful example search queries::

  Paper revision = @paper +revision due:+7d estimate:
  Bug fix = (A) @programming due:+2d estimate: git:
  Project X = @work +projectx due:2021-04-11 estimate: 


Automatic templates
-------------------

The other template mechanism is automatic template selection. You can define task templates
in the configuration file ``~/.config/pter/auto_templates.conf`` with trigger words and
their template texts like this::

    [template name]
    trigger = @paper
    template = due:+5d

So if you create a new task and add the context ``@paper``, the task edit field will indicate
that the "template name" auto template will be used. Once you create the task, it will
automatically receive the template text ``due:+5d``.

To trigger an auto template, you must mention all trigger words in the new task. The order of
the words is not relevant though. For example, if you set up a ``trigger = this is urgent``,
but you create a task with the phrase ``urgent this is``, the auto template will still trigger.

The templates are checked in the order that they are listed in the ``auto_templates.conf``
file, the first one that matches will be used.

Unless you change the ``auto-template-case-sensitive`` option in the configuration file
to something else, it will be set to ``yes``, meaning that matches are case sensitive (``@paper``
will match, but if you create a new task with ``@PAPER``, it won't match the auto template
shown above).

Your auto templates will also show up when you load regular templates, so you do not need to
define them twice.


.. include:: timetracking.rst


.. include:: delegate.rst


.. include:: task_ids.rst


.. include:: task_seq.rst


.. include:: recurrences.rst


Task Notes
==========

This extension only works in ``pter``, not in ``qpter``.

You may provide a text file with additional notes about a task using the ``note:`` tag.

The location of notes is managed via the configuration file in the ``General``
section with the ``notes`` option.

Notes are assumed to be ``.txt`` text files, but you can overwrite that with
the ``note-suffix`` configuration option.

For example, if you define a task with ``note:details``, pter will assume you
meant a file with the name ``details.txt``.

However, you can just define the full filename with extension in which case pter
will not use the ``note-suffix`` default. For example ``Some task note:details.md``.

The function ``edit-note`` (usually on shortcut ``N``) will either edit the
note of this task or create a note.

Have a look at the ``note-naming`` option to change the behaviour how new notes
are created.

For editing, ``pter`` will use the external text editor configured with
``editor`` in the configuration file's ``General`` section.


.. include:: gtd.rst


.. include:: extensions.rst


Keyboard controls
=================

pter is fully controlled by keyboard and has no mouse support.

These default keyboard controls are available in any list:

 - "↓", "↑" (cursor keys): select the next or previous item in the list
 - "j", "k": select the next or previous item in the list
 - "Home": go to the first item
 - "End": go the last item
 - ":": jump to a list item by number (works even if list numbers are not shown)
 - "1".."9": jump to the list item with this number
 - "Esc", "^C": cancel the selection (this does nothing in the list of tasks)

In the list of tasks, the following controls are also available:

 - "?": Show help
 - "m": open this manual in a browser
 - "e": edit the currently selected task
 - "E": edit the currently selected task in an external text editor
 - "n": create a new task
 - "v": duplicate the selected task
 - "/": edit the search query
 - "^": clear the search
 - "c": search for a context of the currently selected task
 - "p": search for a project of the currently selected task
 - "r": search for all tasks that this task is referring to with ``ref:`` or ``after:``
 - "F6": select one project out of all used projects to search for
 - "F7": select one context out of all used contexts to search for
 - "q": quit the program
 - "l": load a named search
 - "s": save the current search
 - "L": load a named task template
 - "S": Save a task as a named template
 - "u": open a URL listed in the selected task
 - "t": Start/stop time tracking of the selected task
 - ">": Delegate the selected task
 - "A": Set the priority of this task to ``(A)``
 - "B": Set the priority of this task to ``(B)``
 - "C": Set the priority of this task to ``(C)``
 - "D": Set the priority of this task to ``(D)``
 - "+": Increase the priority of this task
 - "-": Decrease the priority of this task
 - "=": Remove the priority of this task
 - "%": Move this task into the archive
 - "N": Edit or create this task's note
 - "Y": Copy (yank) the selected task's full text to clipboard

In edit fields the following keyboard controls are available:

 - "←", "→" (cursor keys): move the cursor one character to the left or right
 - "Ctrl+←", "Ctrl+→" (ctrl key and cursor keys): mvoe the cursor one word to the left or right
 - "Home": move the cursor to the first charater
 - "End": move the cursor to the last character
 - "Backspace", "^?": delete the character to the left of the cursor
 - "Ctrl+Backspace", "^H", "^W": delete everything left of the cursor until the end of the word
 - "Del": delete the character under the cursor
 - "Ctrl+Del": delete everything right of the cursor until the end of the word
 - "^U": delete from before the cursor to the start of the line
 - "^K": delete everything from the cursor to the end of the line
 - "Escape", "^C": cancel editing
 - "Enter", "Return": accept input and submit changes
 - "↓", "Tab", "^N": next item in the completion list
 - "↑", "^P": previous item in the completion list
 - "Tab": jump to the next ``key:value`` field where there is not ``value``
 - "Enter": use the selected item of the completion list
 - "Esc", "^C": close the completion list

While creating tasks, the following additional keyboard controls exist:

 - "^Y": Create the task without applying the auto template
 - "F6": Select the todo.txt file to save the task in (if you are using multiple files)

Note that, as with all applications based on ``curses``, hitting the ``Esc`` key will only
show an effect after a short waiting time. You can either hit ``Esc`` twice to get the effect
at once or set the environment variable ``ESCDELAY`` to something more to your liking,
like ``50``. Please refer to the documentation of your terminal/shell about how to do that.


.. include:: conforming_to.rst


See Also
========

`pter.config(5)`_, `qpter(1) <man:qpter>`_


Bugs
====

Probably plenty. Please report your findings at `Codeberg <https://codeberg.org/vonshednob/pter>`_, `Github <https://github.com/vonshednob/pter>`_ or via email to the authors at `<https://vonshednob.cc/pter>`_.

