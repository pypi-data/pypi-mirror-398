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
Importing Versions

This is a special type of import, only relevant when data versioning
is enabled.

See the handler class for more info: :class:`FromWuttaToVersions`
"""

from collections import OrderedDict

from sqlalchemy_utils.functions import get_primary_keys

from wuttjamaican.db.util import make_topo_sortkey

from .handlers import FromWuttaHandler, ToWuttaHandler
from .wutta import FromWuttaMirror
from .model import ToWutta


class FromWuttaToVersions(FromWuttaHandler, ToWuttaHandler):
    """
    Handler for Wutta -> Versions import.

    The purpose of this is to ensure version tables accurately reflect
    the current "live" data set, for given table(s).  It is only
    relevant/usable if versioning is configured and enabled.  For more
    on that see :doc:`wutta-continuum:index`.

    For a given import model, the source is the "live" table, target
    is the "version" table - both in the same :term:`app database`.

    When reading data from the target side, it only grabs the "latest"
    (valid) version record for each comparison to source.

    When changes are needed, instead of updating the existing version
    record, it always writes a new version record.

    This handler will dynamically create importers for all versioned
    models in the :term:`app model`; see
    :meth:`make_importer_factory()`.
    """

    target_key = "versions"
    target_title = "Versions"

    continuum_uow = None
    """
    Reference to the
    :class:`sqlalchemy-continuum:`sqlalchemy_continuum.UnitOfWork`
    created (by the SQLAlchemy-Continuum ``versioning_manager``) when
    the transaction begins.

    See also :attr:`continuum_txn` and
    :meth:`begin_target_transaction()`.
    """

    continuum_txn = None
    """
    Reference to the SQLAlchemy-Continuum ``transaction`` record, to
    which any new version records will associate (if needed).

    This transaction will track the effective user responsible for
    the change(s), their client IP, and timestamp.

    This reference is passed along to the importers as well (as
    :attr:`~FromWuttaToVersionBase.continuum_txn`) via
    :meth:`get_importer_kwargs()`.

    See also :attr:`continuum_uow`.
    """

    continuum_comment = None

    def consume_kwargs(self, kwargs):
        kwargs = super().consume_kwargs(kwargs)
        self.continuum_comment = kwargs.pop("comment", None)
        return kwargs

    def begin_target_transaction(self):
        # pylint: disable=line-too-long
        """
        In addition to normal logic, this does some setup for
        SQLAlchemy-Continuum:

        It establishes a "unit of work" by calling
        :meth:`~sqlalchemy-continuum:sqlalchemy_continuum.VersioningManager.unit_of_work()`,
        assigning the result to :attr:`continuum_uow`.

        It then calls
        :meth:`~sqlalchemy-continuum:sqlalchemy_continuum.unit_of_work.UnitOfWork.create_transaction()`
        and assigns that to :attr:`continuum_txn`.

        It also sets the comment for the transaction, if applicable.

        See also docs for parent method:
        :meth:`~wuttasync.importing.handlers.ToSqlalchemyHandler.begin_target_transaction()`
        """
        import sqlalchemy_continuum as continuum  # pylint: disable=import-outside-toplevel

        super().begin_target_transaction()

        self.continuum_uow = continuum.versioning_manager.unit_of_work(
            self.target_session
        )

        self.continuum_txn = self.continuum_uow.create_transaction(self.target_session)

        if self.continuum_comment:
            self.continuum_txn.meta = {"comment": self.continuum_comment}

    def get_importer_kwargs(self, key, **kwargs):
        """
        This modifies the new importer kwargs to add:

        * ``continuum_txn`` - reference to :attr:`continuum_txn`

        See also docs for parent method:
        :meth:`~wuttasync.importing.handlers.ImportHandler.get_importer_kwargs()`
        """
        kwargs = super().get_importer_kwargs(key, **kwargs)
        kwargs["continuum_txn"] = self.continuum_txn
        return kwargs

    # TODO: pylint (correctly) flags this as duplicate code, matching
    # on the wuttasync.importing.csv module - should fix?
    def define_importers(self):
        """
        This overrides typical (manual) importer definition, instead
        generating importers for all versioned models.

        It will inspect the :term:`app model` and call
        :meth:`make_importer_factory()` for each model found, keeping
        only the valid importers.

        See also the docs for parent method:
        :meth:`~wuttasync.importing.handlers.ImportHandler.define_importers()`
        """
        model = self.app.model
        importers = {}

        # pylint: disable=duplicate-code
        # mostly try to make an importer for every data model
        for name in dir(model):
            cls = getattr(model, name)
            if (
                isinstance(cls, type)
                and issubclass(cls, model.Base)
                and cls is not model.Base
            ):
                # only keep "good" importers, i.e. for versioned models
                if factory := self.make_importer_factory(cls, name):
                    importers[name] = factory

        # sort importers according to schema topography
        topo_sortkey = make_topo_sortkey(model)
        importers = OrderedDict(
            [(name, importers[name]) for name in sorted(importers, key=topo_sortkey)]
        )

        return importers

    def make_importer_factory(self, model_class, name):
        """
        Try to generate a new :term:`importer` class for the given
        :term:`data model`.  This is called by
        :meth:`define_importers()`.

        If the provided ``model_class`` is not versioned, this will
        fail and return ``None``.

        For a versioned model, the new importer class will inherit
        from :class:`FromWuttaToVersionBase`.

        Its (target)
        :attr:`~wuttasync.importing.base.Importer.model_class` will be
        set to the **version** model.

        Its
        :attr:`~wuttasync.importing.base.FromSqlalchemy.source_model_class`
        will be set to the **normal** model.

        :param model_class: A (normal, not version) data model class.

        :param name: The "model name" for the importer.  New class
           name will be based on this, so e.g. ``Widget`` model name
           becomes ``WidgetImporter`` class name.

        :returns: The new class, or ``None``
        """
        import sqlalchemy_continuum as continuum  # pylint: disable=import-outside-toplevel

        try:
            version_class = continuum.version_class(model_class)
        except continuum.exc.ClassNotVersioned:
            return None

        return type(
            f"{name}Importer",
            (FromWuttaToVersionBase,),
            {
                "source_model_class": model_class,
                "model_class": version_class,
                "default_keys": list(get_primary_keys(model_class)),
            },
        )


class FromWuttaToVersionBase(FromWuttaMirror, ToWutta):
    """
    Base importer class for Wutta -> Versions.

    This imports from
    :class:`~wuttasync.importing.wutta.FromWuttaMirror` and
    :class:`~wuttasync.importing.model.ToWutta`.

    The import handler will dynamically generate importers using this
    base class; see
    :meth:`~FromWuttaToVersions.make_importer_factory()`.
    """

    continuum_txn = None
    """
    Reference to the handler's attribute of the same name:
    :attr:`~FromWuttaToVersions.continuum_txn`

    This is the SQLAlchemy-Continuum ``transaction`` record, to which
    any new version records will associate (if needed).

    This transaction will track the effective user responsible for
    the change(s), their client IP, and timestamp.
    """

    def get_simple_fields(self):  # pylint: disable=empty-docstring
        """ """
        fields = super().get_simple_fields()
        unwanted = ["transaction_id", "operation_type", "end_transaction_id"]
        fields = [field for field in fields if field not in unwanted]
        return fields

    def get_target_query(self, source_data=None):
        """
        This modifies the normal query to ensure we only get the
        "latest valid" version for each record, for comparison to
        source.

        .. note::

           In some cases, it still may be possible for multiple
           "latest" versions to match for a given record.  This means
           inconsistent data; a warning should be logged if so, and
           you must track it down...

        See also docs for parent method:
        :meth:`~wuttasync.importing.base.ToSqlalchemy.get_target_query()`
        """
        import sqlalchemy_continuum as continuum  # pylint: disable=import-outside-toplevel

        # pylint: disable=singleton-comparison
        return (
            self.target_session.query(self.model_class)
            .filter(self.model_class.end_transaction_id == None)
            .filter(self.model_class.operation_type != continuum.Operation.DELETE)
        )

    def normalize_target_object(self, obj):  # pylint: disable=empty-docstring
        """ """
        data = super().normalize_target_object(obj)

        # we want to add the original version object to normalized
        # data, so we can access it later for updating if needed.  but
        # this method is called for *both* sides (source+target) since
        # this is a "mirrored" importer.  so we must check the type
        # and only cache true versions, ignore "normal" objects.
        if isinstance(  # pylint: disable=isinstance-second-argument-not-valid-type
            obj, self.model_class
        ):
            data["_objref"] = obj

        return data

    def make_version(  # pylint: disable=missing-function-docstring
        self, source_data, operation_type
    ):
        key = self.get_record_key(source_data)
        with self.target_session.no_autoflush:
            version = self.make_empty_object(key)
            self.populate(version, source_data)
            version.transaction = self.continuum_txn
            version.operation_type = operation_type
            self.target_session.add(version)
            return version

    def populate(self, obj, data):  # pylint: disable=missing-function-docstring
        keys = self.get_keys()
        for field in self.get_simple_fields():
            if field not in keys and field in data and field in self.fields:
                setattr(obj, field, data[field])

    def create_target_object(self, key, source_data):  # pylint: disable=empty-docstring
        """ """
        import sqlalchemy_continuum as continuum  # pylint: disable=import-outside-toplevel

        return self.make_version(source_data, continuum.Operation.INSERT)

    def update_target_object(  # pylint: disable=empty-docstring
        self, obj, source_data, target_data=None
    ):
        """ """
        import sqlalchemy_continuum as continuum  # pylint: disable=import-outside-toplevel

        # when we "update" it always involves making a *new* version
        # record.  but that requires actually updating the "previous"
        # version to indicate the new version's transaction.
        prev_version = target_data.pop("_objref")
        prev_version.end_transaction_id = self.continuum_txn.id

        return self.make_version(source_data, continuum.Operation.UPDATE)

    def delete_target_object(self, obj):  # pylint: disable=empty-docstring
        """ """
        import sqlalchemy_continuum as continuum  # pylint: disable=import-outside-toplevel

        # nb. `obj` here is the existing/old version record; we update
        # it to indicate the new version's transaction.
        obj.end_transaction_id = self.continuum_txn.id

        # add new "DELETE" version record.  values should be the same as
        # for "previous" (existing/old) version.
        source_data = self.normalize_target_object(obj)
        return self.make_version(source_data, continuum.Operation.DELETE)
