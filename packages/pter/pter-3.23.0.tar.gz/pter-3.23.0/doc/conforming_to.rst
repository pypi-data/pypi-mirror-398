Conforming to
=============

pter works with and uses the todo.txt file format and strictly adheres to the format
as described at http://todotxt.org/. Additional special key/value tags are
described in the previous section.

Reading todo.txt files is more lenient than writing them, i.e. files that have been
written by other programs with less interpretations of the todo.txt file format will
be read correctly; writing these files back might result in a different form though
(and potential loss of information, like the completion date for completed tasks that
do not have a creation date).

The ``file-format`` option in the ``[General]`` section of the configuration file can
be set to ``relaxed`` in order to write files that are closer to the format that is
produced by these other todo.txt managers.

