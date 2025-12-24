
===================
 Built-in Commands
===================

Below are the :term:`subcommands <subcommand>` which come with
WuttaSync.

It is fairly simple to add more; see :doc:`custom`.


.. _wutta-import-csv:

``wutta import-csv``
--------------------

Import data from CSV file(s) to the Wutta :term:`app database`.

This *should* be able to automatically target any table mapped in the
:term:`app model`.  The only caveat is that it is "dumb" and does not
have any special field handling.  This means the column headers in the
CSV file must be named the same as in the target table, and some data
types may not behave as expected etc.

Defined in: :mod:`wuttasync.cli.import_csv`

.. program-output:: wutta import-csv --help


.. _wutta-import-versions:

``wutta import-versions``
-------------------------

Import latest data to version tables, for the Wutta :term:`app
database`.

The purpose of this is to ensure version tables accurately reflect
the current "live" data set, for given table(s).  It is only
relevant/usable if versioning is configured and enabled.  For more
on that see :doc:`wutta-continuum:index`.

This command can check/update version tables for any versioned class
in the :term:`app model`.

Defined in: :mod:`wuttasync.cli.import_versions`

.. program-output:: wutta import-versions --help
