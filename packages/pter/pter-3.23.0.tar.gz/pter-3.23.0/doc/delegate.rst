Delegating Tasks
================

The ``delegate`` function (on shortcut ``>`` (pter) or ``Ctrl+G`` (qpter)
by default) can be used to mark a task as delegated and trigger the
delegation action.

When delegating a task the configured marker is being added to the task
(configured by ``delegation-marker`` in the configuration file).

The delegation action is configured by setting the ``delegation-action`` in
the configuration file to ``mail-to``. In that case an attempt is made to
open your email program and start a new email. In case you defined a
``to:`` (configurable by defining ``delegation-to``) in your task
description, that will be used as the recipient for the email.

