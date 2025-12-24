
WuttaSync
=========

This provides a "batteries included" way to handle data sync between
arbitrary source and target.

This builds / depends on :doc:`WuttJamaican <wuttjamaican:index>`, for
sake of a common :term:`config object` and :term:`handler` interface.
It was originally designed for import to / export from the :term:`app
database` but **both** the source and target can be "anything" -
e.g. CSV or Excel file, cloud API, another DB.

The basic idea is as follows:

* read a data set from "source"
* read corresonding data from "target"
* compare the two data sets
* where they differ, create/update/delete records on the target

Although in some cases (e.g. export to CSV) the target has no
meaningful data so all source records are "created" on / written to
the target.

.. note::

   You may already have guessed, that this approach may not work for
   "big data" - and indeed, it is designed for "small" data sets,
   ideally 500K records or smaller.  It reads both (source/target)
   data sets into memory so that is the limiting factor.

   You can work around this to some extent, by limiting the data sets
   to a particular date range (or other "partitionable" aspect of the
   data), and only syncing that portion.

   However this is not meant to be an ETL engine involving a data
   lake/warehouse.  It is for more "practical" concerns where some
   disparate "systems" must be kept in sync, or basic import from /
   export to file.

The general "source → target" concept can be used for both import and
export, since "everything is an import" from the target's perspective.

In addition to the import/export framework proper, a CLI framework is
also provided.

A "real-time sync" framework is also (eventually) planned, similar to
the one developed in the Rattail Project;
cf. :doc:`rattail-manual:data/sync/index`.

.. image:: https://img.shields.io/badge/linting-pylint-yellowgreen
    :target: https://github.com/pylint-dev/pylint

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black


.. toctree::
   :maxdepth: 2
   :caption: Documentation

   glossary
   narr/install
   narr/cli/index
   narr/concepts
   narr/custom/index

.. toctree::
   :maxdepth: 1
   :caption: Package API

   api/wuttasync
   api/wuttasync.app
   api/wuttasync.cli
   api/wuttasync.cli.base
   api/wuttasync.cli.import_csv
   api/wuttasync.cli.import_versions
   api/wuttasync.emails
   api/wuttasync.importing
   api/wuttasync.importing.base
   api/wuttasync.importing.csv
   api/wuttasync.importing.handlers
   api/wuttasync.importing.model
   api/wuttasync.importing.versions
   api/wuttasync.importing.wutta
   api/wuttasync.testing
   api/wuttasync.util
