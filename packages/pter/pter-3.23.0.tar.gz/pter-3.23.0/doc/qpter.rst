=====
qpter
=====
--------------------------------
Qt Personal Task Entropy Reducer
--------------------------------

Synopsis
========

::

  qpter [-h] [-v] [-u] [-a] [-n task] [-c configuration] filename [filename ...]


Description
===========

pter is a tool to manage your tasks when they are stored in the todo.txt
file format. pter is targeted at users applying the `Getting Things Done`_
method, but can be used by anyone that uses todo.txt files.

qpter offers these features:

 - Fully compatible to the todo.txt standard
 - Support for `due:`, `t:` (threshold date), `h:` (hide task)
 - Extensive search/filter capabilities (see `Searching`_)
 - Sort tasks through search queries (see `Sorting`_)
 - Convenient entering of dates (see `Relative Dates`_)
 - Task sequencing (see `Task Sequences`_)
 - Automatic identifiers (see `Unique Task Identifiers`_)
 - Track time spent per task (see `Time Tracking`_)
 - Support for `Recurring Tasks`_
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

  ``-a``
    Only available for qpter: either start qpter, immediately open the New
    Task panel. Or, if qpter is running already, bring it to the foreground
    and open the New Task panel.

  ``-n task``
    Add ``task`` to the todo.txt file. The advantage of using this over
    just ``echo "task" >> todo.txt`` is that relative dates are properly
    expanded (see `Relative Dates`_).
    If you provide ``-`` instead of a task, the task will be read from
    stdin. Multiple tasks can be added, one per line.

    If you don't provide a todo.txt file on the commandline, the first file
    from the ``files`` option in your configuration file will be used.

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


Keyboard controls
=================

qpter is a regular Qt application, so it can be controlled by mouse and keyboard as you would expect.

However, it should be usable by using only your keyboard.

 - Quit: ``Ctrl+Q``
 - Open the manual: ``F1``
 - Focus the task list: ``F6``
 - Open and focus the named searches: ``F8``
 - Create a new task: ``Ctrl+N``
 - Copy the selected task to clipboard: ``Ctrl+C``
 - Edit the selected task: ``Ctrl+E``
 - Toggle 'done' state of selected task: ``Ctrl+D``
 - Toggle 'hidden' state of selected task: ``Ctrl+H``
 - Toggle 'tracking' state of selected task: ``Ctrl+T``
 - Delegate the selected task: ``Ctrl+G``


Clipboard Support
=================

You can copy the selected task to clipboard when you press ``Ctrl+C`` or right click and select "Copy to clipboard".


.. include:: relative_dates.rst

.. include:: searching.rst

.. include:: sorting.rst

.. include:: timetracking.rst

.. include:: delegate.rst

.. include:: task_ids.rst

.. include:: task_seq.rst

.. include:: recurrences.rst

.. include:: gtd.rst

.. include:: extensions.rst

.. include:: conforming_to.rst


See Also
========

`pter.config(5)`_, `qpter(1) <man:qpter>`_


Bugs
====

Probably plenty. Please report your findings at `Codeberg <https://codeberg.org/vonshednob/pter>`_, `Github <https://github.com/vonshednob/pter>`_ or via email to the authors at `<https://vonshednob.cc/pter>`_.

