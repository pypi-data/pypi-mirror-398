====
pter
====
-----------------------------
Personal Task Entropy Reducer
-----------------------------

This help describes the configuration files for both pter and qpter.


Configuration Files
===================

Aside from the data files in the todo.txt format (see `Conforming to`_),
pter's behaviour can be configured through a configuration file.

The configuration file's default location is at ``~/.config/pter/pter.conf``.

There should have been an example configuration file, ``example.conf``
distributed with your copy of pter that can give you an idea on how that
works. In this documentation you will find the full explanation.

Note that the configuration file content is case-sensitive!

The configuration file is entirely optional and each option has a default
value. That allows you to run pter just fine without ever configuring
anything.

The configuration file has these four sections:

 - `General`_, for general behaviour,
 - `Symbols`_, for icons used in the (task) display,
 - `Keys`_, to override default keyboard controls in lists,
 - Editor:Keys, to override the default keyboard controls in edit fields (detailed in `Keys`_),
 - `Colors`_, for coloring the TUI,
 - `GUI:Colors`_, for coloring the tasks in the GUI,
 - `Highlight`_, for coloring specific tags of tasks,
 - GUI:Highlight, for coloring specific tags of tasks (GUI version, see `Highlight`_).
 - `GUI`_, for other GUI specific options
 - `Hooks`_, for calling external programs at times from within pter

This help also includes details on these topics:

 - How to include additional configuration files, see `Include`_,
 - Use an external program for `Time Tracking`_.


General
=======

  ``use-colors``
    Whether or not to use colors. Defaults to 'yes'.

  ``scroll-margin``
    How many lines to show at the lower and upper margin of lists. Defaults
    to '5'.

  ``safe-save``
    Safe save means that changes are written to a temporary file and that
    file is moved over the actual file after writing was completed.
    Defaults to 'yes'.

    This can be problematic if your files are in folders synchronised with
    cloud services.

  ``search-case-sensitive``
    Can be set to ``yes`` (the default), ``no`` (make all searches ignore upper/lower case), or
    ``smart``. Please consult the section "Smart case-sensitive search" in the pter/qpter documentation
    for details.

  ``auto-template-case-sensitive``
    Can be set to ``yes`` (the default), ``no`` (auto template matching is case insensitive), or
    ``smart`` (if the auto template text has upper case characters, matching this one will be
    case sensitive).

  ``human-friendly-dates``
    Here you can define what fields of a task, that are known to contain a
    date, should be displayed in a more human-friendly way. By default no
    dates are translated.

    Human-friendly means that instead of a 'YYYY-MM-DD' format it might
    show 'next wednesday', 'tomorrow', or 'in 2 weeks'. It means that
    dates, that are further away (in the future or the past) will be less
    precise.

    Possible values are ``due`` (for due dates), ``t`` (for the
    threshold/tickler dates), ``completed`` (for completion dates),
    ``created`` (for creation dates), or ``all`` (for all of the above).
    You can also combine these values by comma separating them like this::

      [General]
      human-friendly-dates = due, t

  ``task-format``
    The format string to use for displaying tasks. Defaults to "``{selection: >} {nr: >} {done} {tracking }{due }{(pri) }{description}``".

    See `Task Format`_ below for more details.

  ``clear-contexts``
    A list of comma separated contexts (without the leading ``@``) to remove from a task
    when it is being marked as done.

    For example, you might want to remove the ``@in`` context or any
    ``@today`` tags when marking a task as done. In that case
    ``clear-contexts`` should be set to ``in, today``.

  ``default-threshold``
    The default ``t:`` search value to use, even when no other search has
    been defined. Defaults to 'today'.

    This option supports Relative Dates (see pter documentation).

  ``delegation-marker``
    Marker to add to a task when delegating it. Defaults to ``@delegated``.

  ``delegation-action``
    Action to take when delegating a task.
    One of 'none', or 'mail-to' (defaulting to 'mail-to').

    'none' does nothing, but 'mail-to' will attempt to start your email
    program to write an email. If your task has a 'to:' attribute (or
    whatever you set up for ``delegation-to``, it will be used as the
    recipient for the email.

  ``delegation-to``
    Attribute name to use when delegating a task via email. Defaults to
    ``to``. Eg. "clean the dishes to:bob" will compose the email to "bob"
    when delegating a task and the delegation action is "mail-to".

  ``due-delta``
    The difference that should be used to increase/decrease the due date when
    ``inc-due`` or ``dec-due`` is used.

    Defaults to ``1d``.

  ``due-skip-weekend``
    Whether or not to skip weekends while increasing/decreasing due dates.

  ``business-days``
    Define what a business day is for use with ``b`` in relative dates.

    This is expected to be a comma-separated list of ISO weekday numbers
    (1 through 7) or weekday names in english (3-letter version or full name,
    capitalisation is ignored).

    Valid examples are: ``mon, Tue, wed``, ``tuesday, Wednesday``, ``5, 6``.

    Defaults to ``1,2,3,4,5`` (Monday through Friday).

  ``editor``
    The external text editor to use instead of whatever is defined in the
    ``VISUAL`` or ``EDITOR`` environment variables.
    If pter can’t find a valid editor in neither this configuration option
    nor these environment variables, it will fall back to ``nano`` in the
    wild hopes that it might be installed.

    Defaults to nothing, because the environment variables should be all
    that’s required.

    This option is ignored in ``qpter``.

  ``viewer``
    The external program to use to view notes. Defaults to ``less`` or ``more``
    and has no effect in ``qpter``.

  ``protocols``
    What protocols should be considered when using the 'Open URL' function
    on a task. Defaults to ``http, https, mailto, ftp, ftps``.

  ``add-creation-date``
    Whether or not to automatically add the creation date of a task
    to it. Defaults to ``yes``.

  ``add-completion-date``
    Whether or not to automatically add the completion date to a task
    when marking it as completed. Defaults to ``always``.

    Other than ``always`` you could set this to ``yes``, to only set a
    completion date when that task also has a creation date.

    Note that ``always`` will set a completion date for tasks that do not
    have a creation date when you mark the task as completed, but if the
    ``file-format`` is set to ``pedantic`` (the default),
    the completion date will not actually be saved to disk!

  ``create-from-search``
    If set to ``yes``, positive expressions (that do not refer to time or
    ``done``) of the active search (eg. ``@context +project word``, but not
    ``-@context due:+7d done:y -others``) will be added automatically to a
    newly created task.

    If the search contains a ``file:`` search, one of the matching files
    will be used as the default file when creating a new task.

    Defaults to ``no``.

  ``auto-id``
    Whether or not to automatically add an ID to newly created tasks.
    Defaults to ``no``.

  ``hide-sequential``
    Whether or not to automatically hide tasks that have uncompleted
    preceding tasks (see Task Sequences in pter documentation).
    Defaults to ``yes``.

  ``info-timeout``
    How long should info messages remain visible in the status bar of the
    TUI application. Defaults to ``5``, so 5 seconds.

  ``use-completion``
    Whether or not to use completion for contexts (``@``) and projects
    (``+``) in the search field, task creation, and task editing fields of
    the TUI. Defaults to ``yes``.

  ``delete-is``
    What behaviour the delete function is actually showing. Can be one of
    these:

     - ``disabled``, no functionality at all. There is no delete. This is
       the default.
     - ``trash``, deleted tasks are moved to the trash file (see
       ``trash-file`` option below).
     - ``permanent``, actually deletes the task.

  ``reduce-distraction``
    Reduce distractions by hiding the task list when creating or editing a task.

    Defaults to ``no``.

  ``esc-timeout``
    The number of ms curses should wait after ``Esc`` has been detected before.
    Play around with this if pter is reacting too slowly to you pressing ``Esc``
    or doesn't register when you press key combinations like ``Alt+Backspace``.

    Defaults to ``200``.

  ``reset-terminal``
    Reset the terminal extra hard to prevent inconsistent mouse wheel interaction.

    Defaults to ``no``.

  ``word-boundaries``
    Letters that are considered word boundaries when using functions like ``del-word-left``,
    ``del-word-right``, ``go-word-left``, and ``go-word-right``.

    Defaults to ``+- @``.

    You can enclose the letters with ``"`` to ensure spaces are preserved.

  ``trash-file``
    Where your trash file is. This option is only used if ``delete-is`` is
    set to ``trash``. Defaults to ``~/.config/pter/trash.txt``.

  ``archive-is``
    Defines the behaviour of the ``archive`` function. Can be one of these:

     - ``relative``, the archive file is assumed to be in the same place as
       the ``todo.txt`` file, but called ``archive.txt``,
     - ``centralised``, there is only one archive file for all ``todo.txt``
       files. Its location is controlled by ``archive-file``,
     - ``disabled``, there is no archiving.

    Defaults to ``centralised``.

  ``archive-file``
    Where your archive file is. This file will be used to receive archived
    tasks if the ``archive-is`` option is set to ``centralised``. Defaults
    to ``~/.config/pter/archive.txt``.

  ``archive-origin-marker``
    If you want to add the original filename of the todo.txt file where the
    task that you are archiving just now was coming from (especially useful
    if you use a ``centralised`` archive file), set this option to the name
    of the attribute to add to the archived task.

    For example, if you set this to ``origin`` and archive a task from the
    ``work.txt``, the archived task will have the additional attribute
    ``origin:work.txt``.

    By default this option is not set to anything and therefore ignored.

  ``archive-origin-is``
    What to save as the original task file when archiving a task. Note that
    this option is ignored unless ``archive-origin-marker`` is set.

    Options are:

     - ``full-path``, save the full path to the original file,
     - ``name``, save only the name of the original file,
     - ``stem``, save only the filename of the original file, without the suffix (which is most often ``.txt`` anyway)

    The default is ``full-path``.

  ``done-is``
    Defines the behaviour of the ``done`` function. Can be on of these:

     - ``mark``, just mark the task as done
     - ``move``, move the task into the ``done-file``
     - ``mark-move``, mark the task as done and move it into the ``done-file``

    Note that in case of ``move`` or ``mark-move`` toggling the state of a
    task from done to not-done will move the task back from the done file into
    *one of your open task files* (probably the first file).

    Defaults to ``mark``.

  ``done-file``
    Where your file for completed tasks it. This file will be used if ``done-is``
    is set to ``move`` or ``mark-move``.

    Defaults to ``~/.config/pter/done.txt``.

  ``reuse-recurring``
    Reuse existing recurring task entry instead of creating a new one. If
    set, completing a task with a ``rec:`` (recurring) tag will be reused
    for the follow-up task instead of creating a new task.

    Defaults to ``no``.

  ``related-show-self``
    Whether or not to show the current task, too, when showing its related
    tasks. This can be set to ``yes``, ``no`` or ``force``.

    ``yes`` means, not only the related tasks are shown, but also this one.

    ``force`` is the same as ``yes``, but if the current task does not have
    an ``id:`` attribute, it will be given one. In other words, this option
    may modify your ``todo.txt`` file.

    Defaults to ``yes``.

  ``sort-order``
    The default sorting order if you don't set one in the search with the
    ``sort:`` keyword.

    Defaults to ``completed,due_in,priority,linenr``

  ``files``
    Default todo file(s) to load. This option is ignored when pter is given
    some todo.txt file(s) in the command line parameters.

    For example: ``files = ~/Documents/todo.txt``.
    
    To provide multiple files, separate them with newlines, like this::

        [General]
        files =
            ~/shared/group_todo.txt
            ~/Documents/todo.txt
            ~/GTD/some day maybe.txt

    The last example shows how to deal with spaces in filenames.

    This option does not apply to qpter, which tracks opened files differently.

  ``notes``
    The directories where notes should be looked for when references as ``note:``
    in a task.

    For example: ``notes = ~/Documents/task_notes/``.

    To provide multiple folder, separate them with newlines, like this::

        [General]
        notes =
            ~/shared/group_notes/
            ~/Documents/task_notes/

    Multiple folders will be searched in order when opening a task note. If no
    note exists, it will be created in the first given folder.

    If this option is not provided, the folders of your selected todo.txt files
    will be used. For example, if you use run with ``Documents/Tasks/todo.txt`` and
    did not set up this ``notes`` option, the directory ``Documents/Tasks/`` will
    be used as the default location for notes.

  ``note-suffix``
    The file extension that's used when finding notes when the file extension is not
    provided.

    Defaults to ``.txt``.

  ``note-naming``
    Defines the behaviour of pter when you edit a task's note, but no ``note:`` tag
    is defined.

    Possible options are:

       - ``cancel``, don't try to edit the task's note
       - ``auto``, create a file based on the task's ID, create a task ID if necessary
       - ``user-input``, ask the user for the name of the file

    Defaults to ``user-input``.

  ``time-tracking``
    What external program you want to use for time tracking. See below, `Time Tracking`_
    for all details.

    By default this option is not set, which means that pter's internal time tracking
    is used.

  ``help-actions``
    A new-line separated list of actions to show in the help bar of the main task list.

    Defaults to the very basic functions::

        help-actions =
            show-help
            quit
            edit-task
            create-task
            search
            load-search
            save-search
            toggle-done
            jump-to
            next-item
            prev-item
            edit-note

  ``include``
    Include these configuration files. May be a newline separated list of additional
    configuration files, or a single additional configuration file to load after this
    base configuration file has been processed.

    Examples::

        [General]
        include = ~/.pter/extra.conf

    or::

        [General]
        include =
            ~/.pter/extra.conf
            ~/.config/colors/pter.conf

    The additional configuration will be loaded in order and may overwrite earlier
    settings.

  ``file-format``
    There are multiple interpretations of the ``todo.txt`` specification. With this
    option you can choose whether to follow the rules very pedantically or in a more
    relaxed manner when writing tasks to disk.

    Set this to ``pedantic`` (the default) to be very strict about how files are written.

    The only other alternative is ``relaxed``, which allows a few more corner cases (like
    "completed on" dates even if no "created on" date was set.


Symbols
=======

The following symbols (single unicode characters or even longer strings of
unicode characters) can be defined:

 - ``selection``, what symbol or string to use to indicate the selected item of a list
 - ``not-done``, what symbol or string to use for tasks that are not done
 - ``done``, what symbol or string to use for tasks that are done
 - ``overflow-left``, what symbol or string to use to indicate that there is more text to the left
 - ``overflow-right``, what symbol or string to use to indicate that there is more text to the right
 - ``overdue``, the symbol or string for tasks with a due date in the past
 - ``due-today``, the symbol or string for tasks with a due date today
 - ``due-tomorrow``, the symbol or string for tasks with a due date tomorrow
 - ``tracking``, the symbol or string to show that this task is currently being tracked

If you want to use spaces around your symbols, you have to quote them either
with ``'`` or ``"``.

An example could be::

    [Symbols]
    not-done = " "
    done = ✔


Keys
=====

In the configuration file you can assign keyboard shortcuts to the various
functions in pter and qpter.

For details on how to setup shortcuts for qpter, please see below in
section `GUI Keys`_.

There are three main distinct groups of functions. The first, for general
lists:

 - ``cancel``: cancel or exit the current window or input field
 - ``jump-to``: enter a number to jump to that item in the list
 - ``first-item``: jump to the first item in a list
 - ``last-item``: jump to the last item in a list
 - ``page-up``: scroll up by one page
 - ``page-down``: scroll down by one page
 - ``next-item``: select the next item in a list
 - ``prev-item``: select the previous item in a list

Second, there are more complex functions to edit tasks or control pter
(for these functions you may use key sequences, see below for details):

 - ``quit``: quit the program
 - ``show-help``: show the full screen help (only key bindings so far)
 - ``open-manual``: open this manual in a browser
 - ``create-task``: create a new task
 - ``edit-task``: edit the selected task
 - ``edit-external``: edit the selected task in an external text editor
 - ``edit-file-external``: edit the todo.txt of the selected task in an external editor
 - ``duplicate-task``: create a copy of the selected task (deduplicates any ``id:``)
 - ``delete-task``: delete the selected task or move it to trash, depends
   on the configuration option ``delete-is`` (by default not bound to any
   key)
 - ``archive``: move the selected task to the designated archive file
 - ``edit-note``: edit the first note of this task
 - ``view-note``: view the first note of this task
 - ``load-search``: show the saved searches to load one
 - ``open-url``: open a URL of the selected task
 - ``refresh-screen``: rebuild the GUI
 - ``reload-tasks``: enforce reloading of all tasks from all sources
 - ``save-search``: save the current search
 - ``search``: enter a new search query
 - ``clear-search``: clear the search query
 - ``search-context``: select a context from the selected task and search for it
 - ``search-project``: select a project from the selected task and search for it
 - ``select-context``: select a context from all used contexts and search for it
 - ``select-project``: select a project from all used projects and search for it
 - ``show-related``: show tasks that are related to this one (by means of ``after:`` or ``ref:``)
 - ``toggle-done``: toggle the "done" state of a task
 - ``toggle-hidden``: toggle the "hidden" state of a task
 - ``toggle-tracking``: start or stop time tracking for the selected task
 - ``to-clipboard``: copy the selected task's full text to clipboard
 - ``delegate``: delegate a task
 - ``inc-due``: increase the due date by ``due-delta`` (usually 1 day) or add a due date if there is none
 - ``dec-due``: decrease the due date by ``due-delta`` (usually 1 day) or add a due date if there is none
 - ``clear-due``: clear the due date
 - ``prio-a``: set the selected task's priority to ``(A)``
 - ``prio-b``: set the selected task's priority to ``(B)``
 - ``prio-c``: set the selected task's priority to ``(C)``
 - ``prio-d``: set the selected task's priority to ``(D)``
 - ``prio-none``: remove the priority from the selected task
 - ``prio-up``: increase the priority of the selected task
 - ``prio-down``: decrease the priority of the selected task
 - ``nop``: nothing (in case you want to unbind keys)

And finally, the list of functions for edit fields (to be set in the ``[Editor:Keys]`` section):

 - ``cancel``, cancel editing, leave the editor (reverts any changes)
 - ``del-left``, delete the character left of the cursor
 - ``del-right``, delete the character right of the cursor
 - ``del-to-bol``, delete all characters from the cursor to the beginning of the line
 - ``del-to-eol``, delete all characters from the cursor to the end of the line
 - ``del-word-right``, delete the everything right of the cursor until the end of the word
 - ``del-word-left``, delete everything left of the cursor until the end of the word
 - ``go-bol``, move the cursor to the beginning of the line
 - ``go-eol``, move the cursor to the end of the line
 - ``go-left``, move the cursor one character to the left
 - ``go-right``, move the cursor one charackter to the right
 - ``go-word-left``, move the cursor one word to the left
 - ``go-word-right``, move the cursor one word to the right
 - ``goto-empty``, move the cursor to the next ``tag:value`` where the is no ``value``
 - ``submit-input``, accept the changes, leave the editor (applies the changes)
 - ``select-file``, when creating a new task, this allows you to select
   what todo.txt file to save the task in
 - ``comp-next``, next item in the completion list
 - ``comp-prev``, previous item in the completion list
 - ``comp-use``, use the selected item in the completion list
 - ``comp-close``, close the completion list

Keyboard shortcuts are given by their character, for example ``d``.
To indicate the shift key, use the upper-case of that letter (``D`` in this
example).

To express that the control key should be held down for this shortcut,
prefix the letter with ``^``, like ``^d`` (for control key and the letter
"d").

Additionally there are some special keys understood by pter:

 - ``<backspace>``
 - ``<alt_backspace>``, alt key and backspace key
 - ``<ctrl_backspace>``, ctrl key and backspace key
 - ``<del>``
 - ``<ctrl_del>``, ctrl key and del key
 - ``<left>`` left cursor key
 - ``<right>`` right cursor key
 - ``<up>`` cursor key up
 - ``<down>`` cursor key down
 - ``<ctrl_left>``, ctrl key and left cursor key
 - ``<ctrl_right>``, ctrl key and right cursor key
 - ``<pgup>`` page up
 - ``<pgdn>`` page down
 - ``<home>``
 - ``<end>``
 - ``<escape>``
 - ``<return>``
 - ``<tab>``
 - ``<f1>`` through ``<f20>``

An example could look like this::

  [Keys]
  ^k = quit
  <F3> = search
  C = create-task

Note that due to the file format of the configuration file you have to use
special sequences if you want to bind ``:``, ``;``, or ``=`` to functions.

 - Use ``<colon>`` for ``:``
 - Use ``<semicolon>`` for ``;``
 - Use ``<equal>`` for ``=``
 - Use ``<hash>`` for ``#``
 - Use ``<lbrack>`` for ``[``
 - Use ``<rbrack>`` for ``]``

For example, if you don't want to have ``jump-to`` on ``:``::

  [Keys]
  <colon> = nop


Key Sequences
-------------

For the functions of the second list, the more complex functions for
editing tasks or controlling pter, you may also use key sequences. For
example, you may want to prefix all shortcuts to manipulate the priority of
a task with the letter ``p`` and define these sequences::

  [Keys]
  p+ = prio-up
  p- = prio-down
  pa = prio-a
  pb = prio-b
  pc = prio-c
  pd = prio-d
  p0 = prio-none

Now to increase the priority of a task, you would type first ``p``,
followed by ``+``.

The progress of a key sequence will show in the lower left of the screen,
showing the keys that you have pressed so far. To cancel a key sequence
type the single key shortcut for ``cancel`` (usually ``Escape`` or ``Ctrl-C``)
or just type any invalid key that's not part of the sequence (in the
previous example, ``px`` would do the trick).


GUI Keys
--------

To assign shortcuts to functions in the Qt GUI, you will have to use the Qt
style key names, see https://doc.qt.io/qt-5/qkeysequence.html#details .

The assignment is done in the group ``GUI:Keys``, like this::

  [GUI:Keys]
  new = Ctrl+N
  toggle-done = Ctrl+D

Available function names are:

 - ``quit``, quit qpter
 - ``open-manual``, open this manual
 - ``open-file``, open an additional todo.txt,
 - ``new``, open the editor to create a new task,
 - ``new-related``, open the editor to create a new task that is
   automatically related (has a ``ref:`` attribute) to the
   currently selected task. If the currently selected task does not have an
   ``id:`` yet, it will be given one automatically
 - ``new-subsequent``, open the editor to create a new task that is
   following the currently selected task (has an ``after:`` attribute).
   If the currently selected task does not have an ``id:`` yet, it will
   be given one automatically.
 - ``to-clipboard``, copies the text of the selected task to the clipboard,
 - ``edit``, opens the editor for the selected task,
 - ``toggle-done``, toggles the completion of a task,
 - ``toggle-tracking``, toggle the 'tracking' attribute of the selected task,
 - ``toggle-hidden``, toggle the 'hidden' attribute of the selected task,
 - ``search``, opens and focuses the search field,
 - ``named-searches``, opens and focuses the list of named searches,
 - ``focus-tasks``, focuses the task list,
 - ``delegate``, delegate the selected task,
 - ``delete-task``, delete the selected task (subject to the value of the configuration option ``delete-is``)
 - ``prio-up``, increase the priority of the selected task
 - ``prio-down``, decrease the priority of the selected task
 - ``prio-none``, remove the priority of the selected task
 - ``toggle-dark-mode``, toggle between dark and light mode (requires qdarkstyle to be installed)


Colors
======

Colors are defined in pairs, separated by comma: foreground and background
color. Some color's names come with a ``sel-`` prefix so you can define the
color when it is a selected list item.

You may decide to only define one value, which will then be used as the text
color. The background color will then be taken from ``normal`` or ``sel-normal``
respectively.

If you do not define the ``sel-`` version of a color, pter will use the
normal version and put the ``sel-normal`` background to it.

If you specify a special background for the normal version, but none for the
selected version, the special background of the normal version will be used
for the selected version, too!

 - ``normal``, any normal text and borders
 - ``sel-normal``, selected items in a list
 - ``error``, error messages
 - ``overflow``, ``sel-overflow``, color for the scrolling indicators when editing tasks (and when selected)
 - ``overdue``, ``sel-overdue``, color for a task when it’s due date is in the past (and when selected)
 - ``due-today``, ``sel-due-today``, color for a task that’s due today (and when selected)
 - ``due-tomorrow``, ``sel-due-tomorrow``, color for a task that’s due tomorrow (and when selected)
 - ``completed``, ``sel-completed``, color for a task that has been completed (and when selected)
 - ``inactive``, color for indication of inactive texts
 - ``help``, help text at the bottom of the screen
 - ``help-key``, color highlighting for the keys in the help
 - ``pri-a``, ``sel-pri-a``, color for priority A (and when selected)
 - ``pri-b``, ``sel-pri-b``, color for priority B (and when selected)
 - ``pri-c``, ``sel-pri-c``, color for priority C (and when selected)
 - ``pri-d``, ``sel-pri-d``, color for priority D (and when selected)
 - ``context``, ``sel-context``, color for contexts (and when selected)
 - ``project``, ``sel-project``, color for projects (and when selected)
 - ``tracking``, ``sel-tracking``, color for tasks that are being tracked right now (and when selected)
 - ``file``, ``sel-file``, color for the ``{file}}`` component of ``task-format`` (and when selected)

If you prefer a red background with green text and a blue context, you could define your
colors like this::

  [Colors]
  normal = 2, 1
  sel-normal = 1, 2
  context = 4


Color Priorities
----------------

When selecting the color for a task, pter will use the configured colors in
this order of priority:

 - ``sel-tracking`` (highest priority)
 - ``tracking``
 - ``sel-overdue``
 - ``overdue``
 - ``sel-due-tomorrow``
 - ``due-tomorrow``
 - ``sel-due-today``
 - ``due-today``
 - ``sel-completed``
 - ``completed``
 - ``sel-normal``
 - ``normal`` (lowest priority)

In human words, if a task is due tomorrow, but you are tracking it, it will
show the tracking color. If you also move the cursor onto that task, the
``sel-tracking`` color will be used.


GUI:Colors
==========

The GUI has a somewhat different coloring scheme. The available colors are:

 - ``normal``, any regular text in the description of a task,
 - ``done``, color for tasks that are done,
 - ``overdue``, text color for overdue tasks,
 - ``due-today``, color for tasks that are due today,
 - ``due-tomorrow``, color for tasks that are due tomorrow,
 - ``project``, color for projects,
 - ``context``, color for contexts,
 - ``tracking``, color for tasks that are currently being tracked,
 - ``pri-a``, color for the priority A,
 - ``pri-b``, color for the priority B,
 - ``pri-c``, color for the priority C,
 - ``pri-d``, color for the priority D,
 - ``url``, color for clickable URLs (see ``protocols`` in `General`_)


Highlight
=========

Highlights work exactly like colors, but the color name is whatever tag you
want to have colored.

If you wanted to highlight the ``due:`` tag of a task, you could define
this::

  [Highlight]
  due = 8, 0

For the GUI, use ``GUI:Highlight``. The colors can be specific as hex
values (3, or 6-digits) or named::

  [GUI:Highlight]
  due = red
  t = #4ee
  to = #03fe4b


Task Format
===========

The task formatting is a mechanism that allows you to configure how tasks are
being displayed in pter. It uses placeholders for elements of a task that you can
order and align using a mini language similar to `Python’s format
specification mini-language <https://docs.python.org/library/string.html#formatspec>`_, but
much less complete.

qpter uses only part of the definition, see below in the list of field
names, if you only care for qpter.

If you want to show the task’s age and description, this is your
task format::

    task-format = {age} {description}

The space between the two fields is printed! If you don’t want a space
between, this is your format::

    task-format = {age}{description}

You might want to left align the age, to make sure all task descriptions start
below each other::

    task-format = {age: <}{description}

Now the age field will be left aligned and the right side is filled with
spaces. You prefer to fill it with dots?::

    task-format = {age:.<}{description}

Right align works the same way, just with ``>``. There is currently no
centering.

Suppose you want to surround the age with brackets, then you would want to use
this::

    task-format = {[age]:.<}{description}

Even if no age is available, you will always see the ``[...]`` (the amount of
periods depends on the age of the oldest visible task; in this example some
task is at least 100 days old).

If you don’t want to show a field, if it does not exist, for example the
completion date when a task is not completed, then you must not align it::

    task-format = {[age]:.<}{completed}{description}

You can still add extra characters left or right to the field. They will not
be shown if the field is missing::

    task-format = {[age]:.<}{ completed 😃 }{description}

Now there will be an emoji next to the completion date, or none if the task has
no completion date.

All that being said, qpter uses the same ``task-format`` configuration
option to show tasks, but will disregard some fields (see below) and only
use the field names, but not alignment or decorations.


Field Names
-----------

The following fields exist:

 - ``description``, the full description text of the task
 - ``created``, the creation date (might be missing)
 - ``age``, the age of the task in days (might be missing)
 - ``completed``, the completion date (might be missing, even if the task is completed)
 - ``done``, the symbol for a completed or not completed task (see below)
 - ``pri``, the character for the priority (might not be defined)
 - ``due``, the symbol for the due status (overdue, due today, due tomorrow; might not be defined)
 - ``duedays``, in how many days a task is due (negative number when overdue tasks)
 - ``selection``, the symbol that’s shown when this task is selected in the list (disregarded in qpter)
 - ``nr``, the number of the task in the list (disregarded in qpter)
 - ``tracking``, the symbol to indicate that you started time tracking of this task (might not be there)
 - ``file``, the filename of this tasks’s todo.txt file
 - ``spent``, the total time spent on the task (sum of all ``spent:`` tags)
 - ``note``, the first ``note:`` tag
 - ``contexts``, all context tags
 - ``projects``, all project tags

``description`` is potentially consuming the whole line, so you might want to
put it last in your ``task-format``.


GUI
=====

The GUI specific options are defined in the ``[GUI]`` section:

  ``font``
    The name of the font to use for the task list.

  ``font-size``
    The font size to use for the task list. You can specify the size either
    in pixel (eg. ``12px``) or point size (eg. ``14pt``). Unlike pixel
    sizes, point sizes may be a non-integer number, eg. ``16.8pt``. 

  ``single-instance``
    Whether or not qpter may only be started once.

  ``clickable``
    If enabled, this allows you to click on URLs (see option ``protocols``
    in `General`_) to open them in a webbrowser, and to click on contexts
    and projects to add them to the current search. Disabling this option
    may improve performance. The default is ``yes``, ie. URLs, contexts,
    and projects are clickable.

  ``daily-reload``
    The time (in format HH:MM) when qpter will automatically reload upon
    passing midnight. Defaults to 00:00.


Hooks
=====

Hooks are a mechanism to call external programs under certain conditions from within pter (*not* qpter).
Hooks are defined in their own ``[Hooks]`` section, like this::

  [Hooks]
  on-select = echo {{full}} > ~/current-task.txt
  on-quit = rm -f ~/current-task.txt

The following hooks exist:

  ``on-start``
    Is run when pter starts.

  ``on-select``
    Is run when the selection of the current task changes.

  ``on-new``
    Is run when a task has been created.

  ``on-tracking``
    Is run when the user starts tracking a task.

  ``on-change``
    Is run when a task has been modified by the user (changed priority, description, marked as completed, etc).
    It will not be run if a task is being created, archived, or deleted.

  ``on-done``
    Is run when a task is marked as done.

  ``on-archive``
    Is run when a task has been archived.

  ``on-delete``
    Is run when a task has been deleted.

  ``on-quit``
    Is run when pter quits.

Some of these hooks will be run at the same conditions. For example, if ``on-start`` and
``on-select`` are both defined, both will be run at the start of pter (if there's a task that can be selected).
In these cases, the order of hook execution is the order that they are listed above. I.e. ``on-start`` will be
run before ``on-select``, ``on-tracking`` will be run before ``on-change``.

Even though ``on-tracking`` may appear to have the same functionality as ``tracking`` (using an external time
tracker, see below), the difference is that ``on-tracking`` will always be called, even when there is no
external time tracker defined. That also means both, the external time tracker and ``on-tracking`` will be called
if both are defined. ``on-tracking`` will be run after calling the external time tracker.


Parameter format
----------------

You can use several special values to transfer values from the selected task to
the external program:

 - ``{{description}}``, the bare description without attributes, contexts, or projects
 - ``{{full}}``, the full description (without dates or priority)
 - ``{{raw}}``, the task in its raw todo.txt representation with dates and priority
 - ``{{id}}``, the ``id:`` attribute (this may be empty if there is no id)
 - ``{{project}}``, the first project (marked with ``+``)
 - ``{{projects}}`` or ``{{*projects}}``, all projects
 - ``{{context}}``, the first context (marked with ``@``)
 - ``{{contexts}}`` or ``{{*contexts}}``, all contexts
 - ``{{note}}``, the first ``note:`` attribute (this may be an empty string if there is no such attribute)

You can also add texts before and after the keywords. For example, if the external program
receives a parameter ``--label`` for each context that you would like to add, you could set it up like this::

    on-select = external_program {--label {context}}

This would only add the ``--label`` if the selected task actually has a context.

When adding the description, pter will automatically add the quotes, so this will work::

    on-delete = report_deleted {{project}} {--description {description}} {--label {context}}

In case you wish to add all contexts or projects as parameters to the external program, you
have two options, depending on how multiple values are accepted::

    on-done = track_completed_tasks {--project {projects}}

or::

    on-done = track_completed_tasks {--project {*projects}}

The first option will repeat the ``--project`` parameter together with each
project tag (like ``--project p1 --project p2``).
The second option will set the ``--project`` prefix only once and then add all
project tags (e.g. ``--project p1 p2``).


Time Tracking
=============

The ``time-tracking`` option can be used to use an external program for time
tracking instead of pter.

If you set this option, pter will call the configured external program when you
start tracking a task (which is by default on the key ``t``).

In these examples the documentation will refer to a hypothetical time tracking
program, ``the_accountant``.

The ``time-tracking`` option is expected to have the name of the program to
call first, followed by its parameters. For example::

    time-tracking = the_accountant --start my-project

Parameter expansion works exactly the same way as with hooks (see above).


Integration tricks
------------------

Note that pter can only communicate that you *start* working on a task. If your
time tracking program allows tracking of multiple activities at the same time or
you have to tell it to stop tracking a task before starting with another,
you might have to write a small script that stops tracking and then starts
tracking the task that you selected in pter.

For example, if ``the_accountant`` required such extras, a simple shell script
to first stop tracking and then start could look like this::

    #!/bin/sh

    the_accountant stop
    exec the_accountant start "@$"

Instead of using ``the_accountant`` directly for ``time-tracking``, you would then use
this shell script.


Include
========

You can specify additional configuration files by specifying the ``include``
option in the ``[General]`` section, see above.

The previous method to include a secondary configuration file by means of
the ``[Include]`` section is deprecated.


Conforming To
=============

pter config files are read using Python's ``ConfigParser`` and therefore follow its syntax. For more details, see
`<https://docs.python.org/3/library/configparser.html>`_.


See Also
========

`pter(1) <man:pter>`_, `qpter(1) <man:qpter>`_

