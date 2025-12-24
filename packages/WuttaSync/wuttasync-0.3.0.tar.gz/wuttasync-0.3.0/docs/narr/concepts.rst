
Concepts
========

Things hopefully are straightforward but it's important to get the
following straight in your head; the rest will come easier if you do.


Source vs. Target
-----------------

Data always flows from source to target, it is the #1 rule.

Docs and command output will always reflect this, e.g. **CSV →
Wutta**.

Source and target can be anything as long as the :term:`import
handler` and :term:`importer(s) <importer>` implement the desired
logic.  The :term:`app database` is often involved but not always.


Import vs. Export
-----------------

Surprise, there is no difference.  After all from target's perspective
everything is really an import.

Sometimes it's more helpful to think of it as an export, e.g. **Wutta
→ CSV** really seems like an export.  In such cases the
:attr:`~wuttasync.importing.handlers.ImportHandler.orientation` may be
set to reflect the distinction.


.. _import-handler-vs-importer:

Import Handler vs. Importer
---------------------------

The :term:`import handler` is sort of the "wrapper" around one or more
:term:`importers <importer>` and the latter contain the table-specific
sync logic.

In a DB or similar context, the import handler will make the
connection, then invoke all requested importers, then commit
transaction at the end (or rollback if dry-run).

And each importer will read data from source, and usually also read
data from target, then compare data sets and finally write data to
target as needed.  But each would usually do this for just one table.

See also the base classes for each:

* :class:`~wuttasync.importing.handlers.ImportHandler`
* :class:`~wuttasync.importing.base.Importer`
