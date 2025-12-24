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
Importing from CSV
"""

import csv
import datetime
import decimal
import logging
import uuid as _uuid
from collections import OrderedDict

import sqlalchemy as sa
from sqlalchemy_utils.functions import get_primary_keys

from wuttjamaican.db.util import make_topo_sortkey, UUID
from wuttjamaican.util import parse_bool

from .base import FromFile
from .handlers import FromFileHandler, ToWuttaHandler
from .model import ToWutta


log = logging.getLogger(__name__)


class FromCsv(FromFile):  # pylint: disable=abstract-method
    """
    Base class for importer/exporter using CSV file as data source.

    Note that this assumes a particular "format" for the CSV files.
    If your needs deviate you should override more methods, e.g.
    :meth:`open_input_file()`.

    The default logic assumes CSV file is mostly "standard" - e.g.
    comma-delimited, UTF-8-encoded etc.  But it also assumes the first
    line/row in the file contains column headers, and all subsequent
    lines are data rows.

    .. attribute:: input_reader

       While the input file is open, this will reference a
       :class:`python:csv.DictReader` instance.
    """

    input_reader = None

    csv_encoding = "utf_8"
    """
    Encoding used by the CSV input file.

    You can specify an override if needed when calling
    :meth:`~wuttasync.importing.handlers.ImportHandler.process_data()`.
    """

    def get_input_file_name(self):
        """
        By default this returns the importer/exporter model name plus
        CSV file extension, e.g. ``Widget.csv``

        It calls
        :meth:`~wuttasync.importing.base.Importer.get_model_title()`
        to obtain the model name.
        """
        if hasattr(self, "input_file_name"):
            return self.input_file_name

        model_title = self.get_model_title()
        return f"{model_title}.csv"

    def open_input_file(self):
        """
        Open the input file for reading, using a CSV parser.

        This tracks the file handle via
        :attr:`~wuttasync.importing.base.FromFile.input_file` and the
        CSV reader via :attr:`input_reader`.

        It also updates the effective
        :attr:`~wuttasync.importing.base.Importer.fields` list per the
        following logic:

        First get the current effective field list, e.g. as defined by
        the class and/or from caller params.  Then read the column
        header list from CSV file, and discard any which are not found
        in the first list.  The result becomes the new effective field
        list.
        """
        path = self.get_input_file_path()
        log.debug("opening input file: %s", path)
        self.input_file = open(  # pylint: disable=consider-using-with
            path, "rt", encoding=self.csv_encoding
        )
        self.input_reader = csv.DictReader(self.input_file)

        # nb. importer may have all supported fields by default, so
        # must prune to the subset also present in the input file
        fields = self.get_fields()
        orientation = self.orientation.value
        log.debug(f"supported fields for {orientation}: %s", fields)
        self.fields = [f for f in self.input_reader.fieldnames or [] if f in fields]
        log.debug("fields present in source data: %s", self.fields)
        if not self.fields:
            self.input_file.close()
            raise ValueError("input file has no recognized fields")

    def close_input_file(self):  # pylint: disable=empty-docstring
        """ """
        self.input_file.close()
        del self.input_reader
        del self.input_file

    def get_source_objects(self):
        """
        This returns a list of data records "as-is" from the CSV
        source file (via :attr:`input_reader`).

        Since this uses :class:`python:csv.DictReader` by default,
        each record will be a dict with key/value for each column in
        the file.
        """
        return list(self.input_reader)


class FromCsvToSqlalchemyMixin:  # pylint: disable=too-few-public-methods
    """
    Mixin class for CSV → SQLAlchemy ORM :term:`importers <importer>`.

    Such importers are generated automatically by
    :class:`FromCsvToSqlalchemyHandlerMixin`, so you won't typically
    reference this mixin class directly.

    This mixin adds data type coercion for each field value read from
    the CSV file; see :meth:`normalize_source_object()`.

    .. attribute:: coercers

       Dict of coercer functions, keyed by field name.  This is an
       empty dict by default; however typical usage does not require
       you to set it, as it's auto-provided from
       :func:`make_coercers()`.

       Each coercer function should accept a single value, and return
       the coerced value, e.g.::

          def coerce_int(val):
              return int(val)
    """

    coercers = {}

    def normalize_source_object(self, obj):
        """
        Normalize a source record from CSV input file.  See also the
        parent docs for
        :meth:`wuttasync.importing.base.Importer.normalize_source_object()`.

        This will invoke the appropriate coercer function for each
        field, according to :attr:`coercers`.

        :param obj: Raw data record (dict) from CSV reader.

        :returns: Final data dict for the record.
        """
        data = {}
        for field in self.fields:
            value = obj[field]
            if field in self.coercers:
                value = self.coercers[field](value)
            data[field] = value
        return data


class FromCsvToSqlalchemyHandlerMixin:
    """
    Mixin class for CSV → SQLAlchemy ORM :term:`import handlers
    <import handler>`.

    This knows how to dynamically generate :term:`importer` classes to
    target the particular ORM involved.  Such classes will inherit
    from :class:`FromCsvToSqlalchemyMixin`, in addition to whatever
    :attr:`FromImporterBase` and :attr:`ToImporterBase` reference.

    This all happens within :meth:`define_importers()`.
    """

    source_key = "csv"
    generic_source_title = "CSV"

    FromImporterBase = FromCsv
    """
    This must be set to a valid base class for the CSV source side.
    Default is :class:`FromCsv` which should typically be fine; you
    can change if needed.
    """

    # nb. subclass must define this
    ToImporterBase = None
    """
    For a handler to use this mixin, this must be set to a valid base
    class for the ORM target side.  The :meth:`define_importers()`
    logic will use this as base class when dynamically generating new
    importer/exporter classes.
    """

    def get_target_model(self):
        """
        This should return the :term:`app model` or a similar module
        containing data model classes for the target side.

        The target model is used to dynamically generate a set of
        importers (e.g. one per table in the target DB) which can use
        CSV file as data source.  See also :meth:`define_importers()`.

        Subclass must override this if needed; default behavior is not
        implemented.
        """
        raise NotImplementedError

    # TODO: pylint (correctly) flags this as duplicate code, matching
    # on the wuttasync.importing.versions module - should fix?
    def define_importers(self):
        """
        This mixin overrides typical (manual) importer definition, and
        instead dynamically generates a set of importers, e.g. one per
        table in the target DB.

        It does this based on the target model, as returned by
        :meth:`get_target_model()`.  It calls
        :meth:`make_importer_factory()` for each model class found.
        """
        importers = {}
        model = self.get_target_model()

        # pylint: disable=duplicate-code
        # mostly try to make an importer for every data model
        for name in dir(model):
            cls = getattr(model, name)
            if (
                isinstance(cls, type)
                and issubclass(cls, model.Base)
                and cls is not model.Base
            ):
                importers[name] = self.make_importer_factory(cls, name)

        # sort importers according to schema topography
        topo_sortkey = make_topo_sortkey(model)
        importers = OrderedDict(
            [(name, importers[name]) for name in sorted(importers, key=topo_sortkey)]
        )

        return importers

    def make_importer_factory(self, model_class, name):
        """
        Generate and return a new :term:`importer` class, targeting
        the given :term:`data model` class.

        The newly-created class will inherit from:

        * :class:`FromCsvToSqlalchemyMixin`
        * :attr:`FromImporterBase`
        * :attr:`ToImporterBase`

        And :attr:`~FromCsvToSqlalchemyMixin.coercers` will be set on
        the class, to the result of :func:`make_coercers()`.

        :param model_class: A data model class.

        :param name: The "model name" for the importer/exporter.  New
           class name will be based on this, so e.g. ``Widget`` model
           name becomes ``WidgetImporter`` class name.

        :returns: The new class, meant to process import/export
           targeting the given data model.
        """
        return type(
            f"{name}Importer",
            (FromCsvToSqlalchemyMixin, self.FromImporterBase, self.ToImporterBase),
            {
                "model_class": model_class,
                "key": list(get_primary_keys(model_class)),
                "coercers": make_coercers(model_class),
            },
        )


class FromCsvToWutta(FromCsvToSqlalchemyHandlerMixin, FromFileHandler, ToWuttaHandler):
    """
    Handler for CSV → Wutta :term:`app database` import.

    This uses :class:`FromCsvToSqlalchemyHandlerMixin` for most of the
    heavy lifting.
    """

    ToImporterBase = ToWutta

    def get_target_model(self):  # pylint: disable=empty-docstring
        """ """
        return self.app.model


##############################
# coercion utilities
##############################


def make_coercers(model_class):
    """
    Returns a dict of coercer functions for use by
    :meth:`~FromCsvToSqlalchemyMixin.normalize_source_object()`.

    This is called automatically by
    :meth:`~FromCsvToSqlalchemyHandlerMixin.make_importer_factory()`,
    in which case the result is assigned to
    :attr:`~FromCsvToSqlalchemyMixin.coercers` on the importer class.

    It will iterate over all mapped fields, and call
    :func:`make_coercer()` for each.

    :param model_class: SQLAlchemy mapped class, e.g.
       :class:`wuttjamaican:wuttjamaican.db.model.base.Person`.

    :returns: Dict of coercer functions, keyed by field name.
    """
    mapper = sa.inspect(model_class)
    fields = list(mapper.columns.keys())

    coercers = {}
    for field in fields:
        attr = getattr(model_class, field)
        coercers[field] = make_coercer(attr)

    return coercers


def make_coercer(attr):  # pylint: disable=too-many-return-statements
    """
    Returns a coercer function suitable for use by
    :meth:`~FromCsvToSqlalchemyMixin.normalize_source_object()`.

    This is typically called from :func:`make_coercers()`.  The
    resulting function will coerce values to the data type defined by
    the given attribute, e.g.::

       def coerce_int(val):
           return int(val)

    :param attr: SQLAlchemy mapped attribute, e.g.
       :attr:`wuttjamaican:wuttjamaican.db.model.upgrades.Upgrade.exit_code`.

    :returns: Coercer function based on mapped attribute data type.
    """
    assert len(attr.prop.columns) == 1
    column = attr.prop.columns[0]

    # UUID
    if isinstance(attr.type, UUID):
        return coerce_uuid

    # Boolean
    if isinstance(attr.type, sa.Boolean):
        if column.nullable:
            return coerce_boolean_nullable
        return coerce_boolean

    # DateTime
    if isinstance(attr.type, sa.DateTime) or (
        hasattr(attr.type, "impl") and isinstance(attr.type.impl, sa.DateTime)
    ):
        return coerce_datetime

    # Float
    # nb. check this before decimal, since Numeric inherits from Float
    if isinstance(attr.type, sa.Float):
        return coerce_float

    # Decimal
    if isinstance(attr.type, sa.Numeric):
        return coerce_decimal

    # Integer
    if isinstance(attr.type, sa.Integer):
        return coerce_integer

    # String
    if isinstance(attr.type, sa.String):
        if column.nullable:
            return coerce_string_nullable

    # do not coerce
    return coerce_noop


def coerce_boolean(value):  # pylint: disable=missing-function-docstring
    return parse_bool(value)


def coerce_boolean_nullable(value):  # pylint: disable=missing-function-docstring
    if value == "":
        return None
    return coerce_boolean(value)


def coerce_datetime(value):  # pylint: disable=missing-function-docstring
    if value == "":
        return None

    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")


def coerce_decimal(value):  # pylint: disable=missing-function-docstring
    if value == "":
        return None
    return decimal.Decimal(value)


def coerce_float(value):  # pylint: disable=missing-function-docstring
    if value == "":
        return None
    return float(value)


def coerce_integer(value):  # pylint: disable=missing-function-docstring
    if value == "":
        return None
    return int(value)


def coerce_noop(value):  # pylint: disable=missing-function-docstring
    return value


def coerce_string_nullable(value):  # pylint: disable=missing-function-docstring
    if value == "":
        return None
    return value


def coerce_uuid(value):  # pylint: disable=missing-function-docstring
    if value == "":
        return None
    return _uuid.UUID(value)
