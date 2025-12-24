.. _glossary:

Glossary
========

.. glossary::
   :sorted:

   import/export key
     Unique key representing a particular type of import/export job,
     i.e. the source/target and orientation (import vs. export).

     For instance "Wutta → CSV export" uses the key:
     ``export.to_csv.from_wutta``

     More than one :term:`import handler` can share a key, e.g. one
     may subclass another and inherit the key.

     However only one handler is "designated" for a given key; it will
     be used by default for running those jobs.

     This key is used for lookup in
     :meth:`~wuttasync.app.WuttaSyncAppProvider.get_import_handler()`.

     See also
     :meth:`~wuttasync.importing.handlers.ImportHandler.get_key()`
     method on the import/export handler.

   import handler
     This a type of :term:`handler` which is responsible for a
     particular set of data import/export task(s).

     The import handler manages data connections and transactions, and
     invokes one or more :term:`importers <importer>` to process the
     data.  See also :ref:`import-handler-vs-importer`.

     Note that "import/export handler" is the more proper term to use
     here but it is often shortened to just "import handler" for
     convenience.

   importer
     This refers to a Python class/instance responsible for processing
     a particular :term:`data model` for an import/export job.

     For instance there is usually one importer per table, when
     importing to the :term:`app database` (regardless of source).
     See also :ref:`import-handler-vs-importer`.

     Note that "importer/exporter" is the more proper term to use here
     but it is often shortened to just "importer" for convenience.
