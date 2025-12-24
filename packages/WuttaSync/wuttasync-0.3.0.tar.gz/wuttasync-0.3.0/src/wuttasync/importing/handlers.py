# -*- coding: utf-8; -*-
################################################################################
#
#  WuttaSync -- Wutta Framework for data import/export and real-time sync
#  Copyright © 2024-2025 Lance Edgar
#
#  This file is part of Wutta Framework.
#
#  Wutta Framework is free software: you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the Free
#  Software Foundation, either version 3 of the License, or (at your option) any
#  later version.
#
#  Wutta Framework is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#  FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
#  more details.
#
#  You should have received a copy of the GNU General Public License along with
#  Wutta Framework.  If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
"""
Data Import / Export Handlers
"""

import logging
import os
import sys
from collections import OrderedDict
from enum import Enum

import humanize

from wuttjamaican.app import GenericHandler
from wuttjamaican.diffs import Diff


log = logging.getLogger(__name__)


class Orientation(Enum):
    """
    Enum values for :attr:`ImportHandler.orientation`.
    """

    IMPORT = "import"
    EXPORT = "export"


class ImportHandler(GenericHandler):  # pylint: disable=too-many-public-methods
    """
    Base class for all import/export handlers.

    Despite the name ``ImportHandler`` this can be used for export as
    well.  The logic is no different on a technical level and the
    "export" concept is mostly only helpful to the user.  The latter
    is important of course and to help with that we track the
    :attr:`orientation` to distinguish.

    The role of the "import/export handler" (instance of this class)
    is to orchestrate the overall DB connections, transactions and
    then invoke the importer/exporter instance(s) to do the actual
    data assessment/transfer.  Each of the latter will be an instance
    of (a subclass of) :class:`~wuttasync.importing.base.Importer`.
    """

    source_key = None
    """
    Key identifier for the data source.

    This should "uniquely" identify the data source, within the
    context of the data target.  For instance in the case of CSV →
    Wutta, ``csv`` is the source key.

    Among other things, this value is used in :meth:`get_key()`.
    """

    target_key = None
    """
    Key identifier for the data target.

    This should "uniquely" identify the data target.  For instance in
    the case of CSV → Wutta, ``wutta`` is the target key.

    Among other things, this value is used in :meth:`get_key()`.
    """

    orientation = Orientation.IMPORT
    """
    Orientation for the data flow.  Must be a value from
    :enum:`Orientation`:

    * ``Orientation.IMPORT`` (aka. ``'import'``)
    * ``Orientation.EXPORT`` (aka. ``'export'``)

    Note that the value may be displayed to the user where helpful::

       print(handler.orientation.value)

    See also :attr:`actioning`.

    It's important to understand the difference between import/export
    and source/target; they are independent concepts.  Source and
    target indicate where data comes from and where it's going,
    whereas import vs. export is mostly cosmetic.

    How a given data flow's orientation is determined, is basically up
    to the developer.  Most of the time it is straightforward,
    e.g. CSV → Wutta would be import, and Wutta → CSV would be
    export.  But confusing edge cases certainly exist, you'll know
    them when you see them.  In those cases the developer should try
    to choose whichever the end user is likely to find less confusing.
    """

    dry_run = False
    """
    Flag indicating whether data import/export should truly happen vs.
    dry-run only.

    If true, the data transaction will be rolled back at the end; if
    false then it will be committed.

    See also :meth:`rollback_transaction()` and
    :meth:`commit_transaction()`.
    """

    process_started = None

    warnings = False
    """
    Boolean indicating the import/export should run in "warnings"
    mode.

    If set, this declares that no changes are expected for the
    import/export job.  If any changes do occur with this flag set, a
    diff warning email is sent within :meth:`process_changes()`.

    See also :attr:`warnings_recipients`,
    :attr:`warnings_max_diffs` and :attr:`warnings_email_key`.
    """

    warnings_email_key = None
    """
    Explicit :term:`email key` for sending the diff warning email,
    *unique to this import/export type*.

    Handlers do not normally set this, so the email key is determined
    automatically within :meth:`get_warnings_email_key()`.

    See also :attr:`warnings`.
    """

    warnings_recipients = None
    """
    Explicit recipient list for the warning email.  If not set, the
    recipients are determined automatically via config.

    See also :attr:`warnings`.
    """

    warnings_max_diffs = 15
    """
    Max number of record diffs (per model) to show in the warning email.

    See also :attr:`warnings`.
    """

    importers = None
    """
    This should be a dict of all importer/exporter classes available
    to the handler.  Keys are "model names" and each value is an
    importer/exporter class.  For instance::

       {
           'Widget': WidgetImporter,
       }

    This dict is defined during the handler constructor; see also
    :meth:`define_importers()`.

    Note that in practice, this is usually an ``OrderedDict`` so that
    the "sorting" of importer/exporters can be curated.

    If you want an importer/exporter instance you should not use this
    directly but instead call :meth:`get_importer()`.
    """

    def __init__(self, config, **kwargs):
        """ """
        super().__init__(config, **kwargs)
        self.importers = self.define_importers()

    def __str__(self):
        """ """
        return self.get_title()

    @property
    def actioning(self):
        """
        Convenience property which effectively returns the
        :attr:`orientation` in progressive verb tense - i.e. one of:

        * ``'importing'``
        * ``'exporting'``
        """
        return f"{self.orientation.value}ing"

    @classmethod
    def get_key(cls):
        """
        Returns the :term:`import/export key` for the handler.  This
        is a combination of :attr:`source_key` and :attr:`target_key`
        and :attr:`orientation`.

        For instance in the case of Wutta → CSV export, the key is:
        ``export.to_csv.from_wutta``

        Note that more than one handler may use the same key; but only
        one will be configured as the "designated" handler for that
        key, a la
        :meth:`~wuttasync.app.WuttaSyncAppProvider.get_import_handler()`.

        See also :meth:`get_spec()`.
        """
        return f"{cls.orientation.value}.to_{cls.target_key}.from_{cls.source_key}"

    @classmethod
    def get_spec(cls):
        """
        Returns the "class spec" for the handler.  This value is the
        same as what might be used to configure the default handler
        for a given key.

        For instance in the case of CSV → Wutta, the default handler
        spec is ``wuttasync.importing.csv:FromCsvToWutta``.

        See also :meth:`get_key()`.
        """
        return f"{cls.__module__}:{cls.__name__}"

    def get_title(self):
        """
        Returns the full display title for the handler, e.g. ``"CSV →
        Wutta"``.

        Note that the :attr:`orientation` is not included in this title.

        It calls :meth:`get_source_title()` and
        :meth:`get_target_title()` to construct the full title.
        """
        source = self.get_source_title()
        target = self.get_target_title()
        return f"{source} → {target}"

    def get_source_title(self):
        """
        Returns the display title for the data source.

        By default this returns :attr:`source_key`, but this can be
        overriden by class attribute.

        Base class can define ``generic_source_title`` to provide a
        new default::

           class FromExcelHandler(ImportHandler):
               generic_source_title = "Excel File"

        Subclass can define ``source_title`` to be explicit::

           class FromExcelToWutta(FromExcelHandler, ToWuttaHandler):
               source_title = "My Spreadsheet"

        See also :meth:`get_title()` and :meth:`get_target_title()`.
        """
        if hasattr(self, "source_title"):
            return self.source_title
        if hasattr(self, "generic_source_title"):
            return self.generic_source_title
        return self.source_key

    def get_target_title(self):
        """
        Returns the display title for the data target.

        By default this returns :attr:`target_key`, but this can be
        overriden by class attribute.

        Base class can define ``generic_target_title`` to provide a
        new default::

           class ToExcelHandler(ImportHandler):
               generic_target_title = "Excel File"

        Subclass can define ``target_title`` to be explicit::

           class FromWuttaToExcel(FromWuttaHandler, ToExcelHandler):
               target_title = "My Spreadsheet"

        See also :meth:`get_title()` and :meth:`get_source_title()`.
        """
        if hasattr(self, "target_title"):
            return self.target_title
        if hasattr(self, "generic_target_title"):
            return self.generic_target_title
        return self.target_key

    def process_data(self, *keys, **kwargs):
        """
        Run import/export operations for the specified models.

        :param \\*keys: One or more importer/exporter (model) keys, as
           defined by the handler.

        Each key specified must be present in :attr:`importers` and
        thus will correspond to an importer/exporter class.

        A transaction is begun on the source and/or target side as
        needed, then for each model key requested, the corresponding
        importer/exporter is created and invoked.  And finally the
        transaction is committed (assuming normal operation).

        See also these methods which may be called from this one:

        * :meth:`consume_kwargs()`
        * :meth:`begin_transaction()`
        * :meth:`get_importer()`
        * :meth:`~wuttasync.importing.base.Importer.process_data()` (on the importer/exporter)
        * :meth:`process_changes()`
        * :meth:`rollback_transaction()`
        * :meth:`commit_transaction()`
        """
        kwargs = self.consume_kwargs(kwargs)
        self.process_started = self.app.localtime()
        self.begin_transaction()
        changes = OrderedDict()

        if not keys:
            keys = list(self.importers)

        success = False
        try:

            # loop thru specified importer keys
            for key in keys:

                # invoke importer
                importer = self.get_importer(key, **kwargs)
                created, updated, deleted = importer.process_data()
                changed = bool(created or updated or deleted)

                # log what happened
                msg = "%s: added %d; updated %d; deleted %d %s records"
                if self.dry_run:
                    msg += " (dry run)"
                logger = log.warning if changed and self.warnings else log.info
                logger(
                    msg, self.get_title(), len(created), len(updated), len(deleted), key
                )

                # keep track of any changes
                if changed:
                    changes[key] = created, updated, deleted

            # post-processing for all changes
            if changes:
                self.process_changes(changes)

            success = True

        except:
            log.exception("what should happen here?")  # TODO
            raise

        finally:
            if not success:
                log.warning("something failed, so transaction was rolled back")
                self.rollback_transaction()
            elif self.dry_run:
                log.info("dry run, so transaction was rolled back")
                self.rollback_transaction()
            else:
                log.info("transaction was committed")
                self.commit_transaction()

    def consume_kwargs(self, kwargs):
        """
        This method is called by :meth:`process_data()`.

        Its purpose is to give handlers a hook by which they can
        update internal handler state from the given kwargs, prior to
        running the import/export task(s).

        Any kwargs which pertain only to the handler, should be
        removed before they are returned.  But any kwargs which (also)
        may pertain to the importer/exporter instance, should *not* be
        removed, so they are passed along via :meth:`get_importer()`.

        :param kwargs: Dict of kwargs, "pre-consumption."  This is the
           same kwargs dict originally received by
           :meth:`process_data()`.

        :returns: Dict of kwargs, "post-consumption."
        """
        if "dry_run" in kwargs:
            self.dry_run = kwargs["dry_run"]

        if "warnings" in kwargs:
            self.warnings = kwargs.pop("warnings")

        if "warnings_recipients" in kwargs:
            self.warnings_recipients = self.config.parse_list(
                kwargs.pop("warnings_recipients")
            )

        if "warnings_max_diffs" in kwargs:
            self.warnings_max_diffs = kwargs.pop("warnings_max_diffs")

        return kwargs

    def begin_transaction(self):
        """
        Begin an import/export transaction, on source and/or target
        side as needed.

        This is normally called from :meth:`process_data()`.

        Default logic will call both:

        * :meth:`begin_source_transaction()`
        * :meth:`begin_target_transaction()`
        """
        self.begin_source_transaction()
        self.begin_target_transaction()

    def begin_source_transaction(self):
        """
        Begin a transaction on the source side, if applicable.

        This is normally called from :meth:`begin_transaction()`.
        """

    def begin_target_transaction(self):
        """
        Begin a transaction on the target side, if applicable.

        This is normally called from :meth:`begin_transaction()`.
        """

    def commit_transaction(self):
        """
        Commit the current import/export transaction, on source and/or
        target side as needed.

        This is normally called from :meth:`process_data()`.

        Default logic will call both:

        * :meth:`commit_target_transaction()`
        * :meth:`commit_source_transaction()`

        .. note::

           By default the target transaction is committed first; this
           is to avoid edge case errors when the source connection
           times out.  In such cases we want to properly cleanup the
           target and then if an error happens when trying to cleanup
           the source, it is less disruptive.
        """
        # nb. it can sometimes be important to commit the target
        # transaction first.  in particular when the import takes a
        # long time, it may be that no activity occurs on the source
        # DB session after the initial data read.  then at the end
        # committing the source transaction may trigger a connection
        # timeout error, which then prevents target transaction from
        # committing.  so now we just commit target first instead.
        # TODO: maybe sequence should be configurable?
        self.commit_target_transaction()
        self.commit_source_transaction()

    def commit_source_transaction(self):
        """
        Commit the transaction on the source side, if applicable.

        This is normally called from :meth:`commit_transaction()`.
        """

    def commit_target_transaction(self):
        """
        Commit the transaction on the target side, if applicable.

        This is normally called from :meth:`commit_transaction()`.
        """

    def rollback_transaction(self):
        """
        Rollback the current import/export transaction, on source
        and/or target side as needed.

        This is normally called from :meth:`process_data()`.  It is
        "always" called when :attr:`dry_run` is true, but also may be
        called if errors are encountered.

        Default logic will call both:

        * :meth:`rollback_target_transaction()`
        * :meth:`rollback_source_transaction()`

        .. note::

           By default the target transaction is rolled back first;
           this is to avoid edge case errors when the source
           connection times out.  In such cases we want to properly
           cleanup the target and then if an error happens when trying
           to cleanup the source, it is less disruptive.
        """
        # nb. it can sometimes be important to rollback the target
        # transaction first.  in particular when the import takes a
        # long time, it may be that no activity occurs on the source
        # DB session after the initial data read.  then at the end
        # rolling back the source transaction may trigger a connection
        # timeout error, which then prevents target transaction from
        # being rolled back.  so now we always rollback target first.
        # TODO: maybe sequence should be configurable?
        self.rollback_target_transaction()
        self.rollback_source_transaction()

    def rollback_source_transaction(self):
        """
        Rollback the transaction on the source side, if applicable.

        This is normally called from :meth:`rollback_transaction()`.
        """

    def rollback_target_transaction(self):
        """
        Rollback the transaction on the target side, if applicable.

        This is normally called from :meth:`rollback_transaction()`.
        """

    def define_importers(self):
        """
        This method must "define" all importer/exporter classes
        available to the handler.  It is called from the constructor.

        This should return a dict keyed by "model name" and each value
        is an importer/exporter class.  The end result is then
        assigned as :attr:`importers` (in the constoructor).

        For instance::

           return {
               'Widget': WidgetImporter,
           }

        Note that the model name will be displayed in various places
        and the caller may invoke a specific importer/exporter by this
        name etc.  See also :meth:`get_importer()`.
        """
        return OrderedDict()

    def get_importer(self, key, **kwargs):
        """
        Returns an importer/exporter instance corresponding to the
        given key.

        Note that this will always create a *new* instance; they are
        not cached.

        The key will be the "model name" mapped to a particular
        importer/exporter class and thus must be present in
        :attr:`importers`.

        This method is called from :meth:`process_data()` but may also
        be used by ad-hoc callers elsewhere.

        It will call :meth:`get_importer_kwargs()` and then construct
        the importer/exporter instance using those kwargs.

        :param key: Model key for desired importer/exporter.

        :param \\**kwargs: Extra/override kwargs for the importer.

        :returns: Instance of (subclass of)
           :class:`~wuttasync.importing.base.Importer`.
        """
        if key not in self.importers:
            orientation = self.orientation.value
            raise KeyError(f"unknown {orientation} key: {key}")

        kwargs = self.get_importer_kwargs(key, **kwargs)
        kwargs["handler"] = self

        # nb. default logic should (normally) determine keys
        if "keys" in kwargs and not kwargs["keys"]:
            del kwargs["keys"]

        factory = self.importers[key]
        return factory(self.config, **kwargs)

    def get_importer_kwargs(self, key, **kwargs):  # pylint: disable=unused-argument
        """
        Returns a dict of kwargs to be used when construcing an
        importer/exporter with the given key.  This is normally called
        from :meth:`get_importer()`.

        :param key: Model key for the desired importer/exporter,
           e.g. ``'Widget'``

        :param \\**kwargs: Any kwargs we have so collected far.

        :returns: Final kwargs dict for new importer/exporter.
        """
        return kwargs

    def process_changes(self, changes):
        """
        Run post-processing operations on the given changes, if
        applicable.

        This method is called by :meth:`process_data()`, if any
        changes were made.

        Default logic will send a "diff warning" email to the
        configured recipient(s), if :attr:`warnings` mode is enabled.
        If it is not enabled, nothing happens.

        :param changes: :class:`~python:collections.OrderedDict` of
           changes from the overall import/export job.  The structure
           is described below.

        Keys for the ``changes`` dict will be model/importer names,
        for instance::

           {
               "Sprocket": {...},
               "User": {...},
           }

        Value for each model key is a 3-tuple of ``(created, updated,
        deleted)``.  Each of those elements is a list::

           {
               "Sprocket": (
                   [...], # created
                   [...], # updated
                   [...], # deleted
               ),
           }

        The list elements are always tuples, but the structure
        varies::

           {
               "Sprocket": (
                   [ # created, 2-tuples
                       (obj, source_data),
                   ],
                   [ # updated, 3-tuples
                       (obj, source_data, target_data),
                   ],
                   [ # deleted, 2-tuples
                       (obj, target_data),
                   ],
               ),
           }
        """
        if not self.warnings:
            return

        def make_diff(*args, **kwargs):
            return Diff(self.config, *args, **kwargs)

        runtime = self.app.localtime() - self.process_started
        data = {
            "handler": self,
            "title": self.get_title(),
            "source_title": self.get_source_title(),
            "target_title": self.get_target_title(),
            "dry_run": self.dry_run,
            "argv": sys.argv,
            "runtime": runtime,
            "runtime_display": humanize.naturaldelta(runtime),
            "changes": changes,
            "make_diff": make_diff,
            "max_diffs": self.warnings_max_diffs,
        }

        # maybe override recipients
        kw = {}
        if self.warnings_recipients:
            kw["to"] = self.warnings_recipients
            # TODO: should we in fact clear these..?
            kw["cc"] = []
            kw["bcc"] = []

        # send the email
        email_key = self.get_warnings_email_key()
        self.app.send_email(email_key, data, fallback_key="import_export_warning", **kw)

        log.info("%s: warning email was sent", self.get_title())

    def get_warnings_email_key(self):
        """
        Returns the :term:`email key` to be used for sending the diff
        warning email.

        The email key should be unique to this import/export type
        (really, the :term:`import/export key`) but not necessarily
        unique to one handler.

        If :attr:`warnings_email_key` is set, it will be used as-is.

        Otherwise one is generated from :meth:`get_key()`.

        :returns: Email key for diff warnings
        """
        if self.warnings_email_key:
            return self.warnings_email_key

        return self.get_key().replace(".", "_") + "_warning"


class FromFileHandler(ImportHandler):
    """
    Handler for import/export which uses input file(s) as data source.

    This handler assumes its importer/exporter classes inherit from
    :class:`~wuttasync.importing.base.FromFile` for source parent
    logic.
    """

    def process_data(self, *keys, **kwargs):  # pylint: disable=empty-docstring
        """ """

        # interpret file vs. folder path
        # nb. this assumes FromFile importer/exporter
        path = kwargs.pop("input_file_path", None)
        if path:
            if not kwargs.get("input_file_dir") and os.path.isdir(path):
                kwargs["input_file_dir"] = path
            else:
                kwargs["input_file_path"] = path

        # and carry on
        super().process_data(*keys, **kwargs)


class FromSqlalchemyHandler(ImportHandler):
    """
    Base class for import/export handlers using SQLAlchemy ORM (DB) as
    data source.

    This is meant to be used with importers/exporters which inherit
    from :class:`~wuttasync.importing.base.FromSqlalchemy`.  It will
    set the
    :attr:`~wuttasync.importing.base.FromSqlalchemy.source_session`
    attribute when making them; cf. :meth:`get_importer_kwargs()`.

    This is the base class for :class:`FromWuttaHandler`, but can be
    used with any database.

    See also :class:`ToSqlalchemyHandler`.
    """

    source_session = None
    """
    Reference to the :term:`db session` for data source.

    This will be ``None`` unless a transaction is running.
    """

    def begin_source_transaction(self):
        """
        This calls :meth:`make_source_session()` and assigns the
        result to :attr:`source_session`.
        """
        self.source_session = self.make_source_session()

    def commit_source_transaction(self):
        """
        This commits and closes :attr:`source_session`.
        """
        self.source_session.commit()
        self.source_session.close()
        self.source_session = None

    def rollback_source_transaction(self):
        """
        This rolls back, then closes :attr:`source_session`.
        """
        self.source_session.rollback()
        self.source_session.close()
        self.source_session = None

    def make_source_session(self):
        """
        Make and return a new :term:`db session` for the data source.

        Default logic is not implemented; subclass must override.

        :returns: :class:`~sqlalchemy.orm.Session` instance
        """
        raise NotImplementedError

    def get_importer_kwargs(self, key, **kwargs):
        """
        This modifies the new importer kwargs to add:

        * ``source_session`` - reference to :attr:`source_session`

        See also docs for parent method,
        :meth:`~ImportHandler.get_importer_kwargs()`.
        """
        kwargs = super().get_importer_kwargs(key, **kwargs)
        kwargs["source_session"] = self.source_session
        return kwargs


class FromWuttaHandler(FromSqlalchemyHandler):
    """
    Handler for import/export which uses Wutta ORM (:term:`app
    database`) as data source.

    This inherits from :class:`FromSqlalchemyHandler`.

    See also :class:`ToWuttaHandler`.
    """

    source_key = "wutta"
    ""  # nb. suppress docs

    def get_source_title(self):
        """
        This overrides default logic to use
        :meth:`~wuttjamaican:wuttjamaican.app.AppHandler.get_title()`
        as the default value.

        Subclass can still define
        :attr:`~wuttasync.importing.handlers.ImportHandler.source_title`
        (or
        :attr:`~wuttasync.importing.handlers.ImportHandler.generic_source_title`)
        to customize.

        See also docs for parent method:
        :meth:`~wuttasync.importing.handlers.ImportHandler.get_source_title()`
        """
        if hasattr(self, "source_title"):
            return self.source_title
        if hasattr(self, "generic_source_title"):
            return self.generic_source_title
        return self.app.get_title()

    def make_source_session(self):
        """
        This calls
        :meth:`~wuttjamaican:wuttjamaican.app.AppHandler.make_session()`
        and returns it.
        """
        return self.app.make_session()


class ToSqlalchemyHandler(ImportHandler):
    """
    Base class for import/export handlers which target a SQLAlchemy
    ORM (DB).

    This is the base class for :class:`ToWuttaHandler`, but can be
    used with any database.

    See also :class:`FromSqlalchemyHandler`.
    """

    target_session = None
    """
    Reference to the SQLAlchemy :term:`db session` for the target side.

    This may often be a session for the :term:`app database` (i.e. for
    importing to Wutta DB) but it could also be any other.

    This will be ``None`` unless an import/export transaction is
    underway.  See also :meth:`begin_target_transaction()`.
    """

    def begin_target_transaction(self):
        """
        Establish a new :term:`db session` via
        :meth:`make_target_session()` and assign the result to
        :attr:`target_session`.
        """
        self.target_session = self.make_target_session()

    def rollback_target_transaction(self):
        """
        Rollback the :attr:`target_session`.
        """
        self.target_session.rollback()
        self.target_session.close()
        self.target_session = None

    def commit_target_transaction(self):
        """
        Commit the :attr:`target_session`.
        """
        self.target_session.commit()
        self.target_session.close()
        self.target_session = None

    def make_target_session(self):
        """
        Make and return a new :term:`db session` for the import/export.

        Subclass must override this; default logic is not implemented.
        """
        raise NotImplementedError

    def get_importer_kwargs(self, key, **kwargs):  # pylint: disable=empty-docstring
        """ """
        kwargs = super().get_importer_kwargs(key, **kwargs)
        kwargs.setdefault("target_session", self.target_session)
        return kwargs


class ToWuttaHandler(ToSqlalchemyHandler):
    """
    Handler for import/export which targets Wutta ORM (:term:`app
    database`).

    This inherits from :class:`ToSqlalchemyHandler`.

    See also :class:`FromWuttaHandler`.
    """

    target_key = "wutta"
    ""  # nb. suppress docs

    def get_target_title(self):  # pylint: disable=empty-docstring
        """ """
        # nb. we override parent to use app title as default
        if hasattr(self, "target_title"):
            return self.target_title
        if hasattr(self, "generic_target_title"):
            return self.generic_target_title
        return self.app.get_title()

    def make_target_session(self):
        """
        Call
        :meth:`~wuttjamaican:wuttjamaican.app.AppHandler.make_session()`
        and return the result.

        :returns: :class:`~wuttjamaican:wuttjamaican.db.sess.Session`
           instance.
        """
        return self.app.make_session()
