# -*- coding: utf-8; -*-

import csv
import datetime
import decimal
import uuid as _uuid
from unittest import TestCase
from unittest.mock import patch

import sqlalchemy as sa
from sqlalchemy import orm

from wuttjamaican.testing import DataTestCase

from wuttasync.importing import (
    csv as mod,
    ImportHandler,
    ToSqlalchemyHandler,
    ToSqlalchemy,
)


class TestFromCsv(DataTestCase):

    def setUp(self):
        self.setup_db()
        self.handler = ImportHandler(self.config)

        self.data_path = self.write_file(
            "data.txt",
            """\
name,value
foo,bar
foo2,bar2
""",
        )

    def make_importer(self, **kwargs):
        kwargs.setdefault("handler", self.handler)
        return mod.FromCsv(self.config, **kwargs)

    def test_get_input_file_name(self):
        model = self.app.model
        imp = self.make_importer(model_class=model.Setting)

        # name can be guessed
        self.assertEqual(imp.get_input_file_name(), "Setting.csv")

        # name can be explicitly set
        imp.input_file_name = "data.txt"
        self.assertEqual(imp.get_input_file_name(), "data.txt")

    def test_open_input_file(self):
        model = self.app.model
        imp = self.make_importer(model_class=model.Setting)

        # normal operation, input file includes all fields
        imp = self.make_importer(
            model_class=model.Setting, input_file_path=self.data_path
        )
        self.assertEqual(imp.fields, ["name", "value"])
        imp.open_input_file()
        self.assertEqual(imp.input_file.name, self.data_path)
        self.assertIsInstance(imp.input_reader, csv.DictReader)
        self.assertEqual(imp.fields, ["name", "value"])
        imp.input_file.close()

        # this file is missing a field, plus we'll pretend more are
        # supported - but should wind up with just the one field
        missing = self.write_file("missing.txt", "name")
        imp = self.make_importer(model_class=model.Setting, input_file_path=missing)
        imp.fields.extend(["lots", "more"])
        self.assertEqual(imp.fields, ["name", "value", "lots", "more"])
        imp.open_input_file()
        self.assertEqual(imp.fields, ["name"])
        imp.input_file.close()

        # and what happens when no known fields are found
        bogus = self.write_file("bogus.txt", "blarg")
        imp = self.make_importer(model_class=model.Setting, input_file_path=bogus)
        self.assertEqual(imp.fields, ["name", "value"])
        self.assertRaises(ValueError, imp.open_input_file)

    def test_close_input_file(self):
        model = self.app.model
        imp = self.make_importer(model_class=model.Setting)

        imp.input_file_path = self.data_path
        imp.open_input_file()
        imp.close_input_file()
        self.assertIsNone(imp.input_reader)
        self.assertIsNone(imp.input_file)

    def test_get_source_objects(self):
        model = self.app.model
        imp = self.make_importer(model_class=model.Setting)

        imp.input_file_path = self.data_path
        imp.open_input_file()
        objects = imp.get_source_objects()
        imp.close_input_file()
        self.assertEqual(len(objects), 2)
        self.assertEqual(objects[0], {"name": "foo", "value": "bar"})
        self.assertEqual(objects[1], {"name": "foo2", "value": "bar2"})


class MockMixinImporter(mod.FromCsvToSqlalchemyMixin, mod.FromCsv, ToSqlalchemy):
    pass


class TestFromCsvToSqlalchemyMixin(DataTestCase):

    def setUp(self):
        self.setup_db()
        self.handler = ImportHandler(self.config)

    def make_importer(self, **kwargs):
        kwargs.setdefault("handler", self.handler)
        return MockMixinImporter(self.config, **kwargs)

    def test_constructor(self):
        model = self.app.model

        # no coercers
        imp = self.make_importer(model_class=model.Setting)
        self.assertEqual(imp.coercers, {})

        # typical
        imp = self.make_importer(
            model_class=model.Upgrade, coercers=mod.make_coercers(model.Setting)
        )
        self.assertEqual(len(imp.coercers), 2)

    def test_normalize_source_object(self):
        model = self.app.model

        # no uuid keys
        imp = self.make_importer(model_class=model.Setting)
        result = imp.normalize_source_object({"name": "foo", "value": "bar"})
        self.assertEqual(result, {"name": "foo", "value": "bar"})

        # source has proper UUID
        imp = self.make_importer(
            model_class=model.Upgrade,
            fields=["uuid", "description"],
            coercers=mod.make_coercers(model.Upgrade),
        )
        result = imp.normalize_source_object(
            {
                "uuid": "06753693-d892-77f0-8000-ce71bf7ebbba",
                "description": "testing",
            }
        )
        self.assertEqual(
            result,
            {
                "uuid": _uuid.UUID("06753693-d892-77f0-8000-ce71bf7ebbba"),
                "description": "testing",
            },
        )

        # source has string uuid
        imp = self.make_importer(
            model_class=model.Upgrade,
            fields=["uuid", "description"],
            coercers=mod.make_coercers(model.Upgrade),
        )
        result = imp.normalize_source_object(
            {"uuid": "06753693d89277f08000ce71bf7ebbba", "description": "testing"}
        )
        self.assertEqual(
            result,
            {
                "uuid": _uuid.UUID("06753693-d892-77f0-8000-ce71bf7ebbba"),
                "description": "testing",
            },
        )

        # source has boolean true/false
        imp = self.make_importer(
            model_class=model.Upgrade,
            fields=["uuid", "executing"],
            coercers=mod.make_coercers(model.Upgrade),
        )
        result = imp.normalize_source_object(
            {"uuid": "06753693d89277f08000ce71bf7ebbba", "executing": "True"}
        )
        self.assertEqual(
            result,
            {
                "uuid": _uuid.UUID("06753693-d892-77f0-8000-ce71bf7ebbba"),
                "executing": True,
            },
        )
        result = imp.normalize_source_object(
            {"uuid": "06753693d89277f08000ce71bf7ebbba", "executing": "false"}
        )
        self.assertEqual(
            result,
            {
                "uuid": _uuid.UUID("06753693-d892-77f0-8000-ce71bf7ebbba"),
                "executing": False,
            },
        )


class MockMixinHandler(mod.FromCsvToSqlalchemyHandlerMixin, ToSqlalchemyHandler):
    ToImporterBase = ToSqlalchemy


class TestFromCsvToSqlalchemyHandlerMixin(DataTestCase):

    def make_handler(self, **kwargs):
        return MockMixinHandler(self.config, **kwargs)

    def test_get_target_model(self):
        with patch.object(
            mod.FromCsvToSqlalchemyHandlerMixin, "define_importers", return_value={}
        ):
            handler = self.make_handler()
            self.assertRaises(NotImplementedError, handler.get_target_model)

    def test_define_importers(self):
        model = self.app.model
        with patch.object(
            mod.FromCsvToSqlalchemyHandlerMixin, "get_target_model", return_value=model
        ):
            handler = self.make_handler()
            importers = handler.define_importers()
            self.assertIn("Setting", importers)
            self.assertTrue(issubclass(importers["Setting"], mod.FromCsv))
            self.assertTrue(issubclass(importers["Setting"], ToSqlalchemy))
            self.assertIn("User", importers)
            self.assertIn("Person", importers)
            self.assertIn("Role", importers)

    def test_make_importer_factory(self):
        model = self.app.model
        with patch.object(
            mod.FromCsvToSqlalchemyHandlerMixin, "define_importers", return_value={}
        ):
            handler = self.make_handler()
            factory = handler.make_importer_factory(model.Setting, "Setting")
            self.assertTrue(issubclass(factory, mod.FromCsv))
            self.assertTrue(issubclass(factory, ToSqlalchemy))
            self.assertTrue(isinstance(factory.coercers, dict))


class TestFromCsvToWutta(DataTestCase):

    def make_handler(self, **kwargs):
        return mod.FromCsvToWutta(self.config, **kwargs)

    def test_get_target_model(self):
        handler = self.make_handler()
        self.assertIs(handler.get_target_model(), self.app.model)


Base = orm.declarative_base()


class Example(Base):
    __tablename__ = "example"

    id = sa.Column(sa.Integer(), primary_key=True, nullable=False)
    optional_id = sa.Column(sa.Integer(), nullable=True)

    name = sa.Column(sa.String(length=100), nullable=False)
    optional_name = sa.Column(sa.String(length=100), nullable=True)

    flag = sa.Column(sa.Boolean(), nullable=False)
    optional_flag = sa.Column(sa.Boolean(), nullable=True)

    dt = sa.Column(sa.DateTime(), nullable=False)
    optional_dt = sa.Column(sa.DateTime(), nullable=True)

    dec = sa.Column(sa.Numeric(scale=8, precision=2), nullable=False)
    optional_dec = sa.Column(sa.Numeric(scale=8, precision=2), nullable=True)

    flt = sa.Column(sa.Float(), nullable=False)
    optional_flt = sa.Column(sa.Float(), nullable=True)


class TestMakeCoercers(TestCase):

    def test_basic(self):
        coercers = mod.make_coercers(Example)
        self.assertEqual(len(coercers), 12)

        self.assertIs(coercers["id"], mod.coerce_integer)
        self.assertIs(coercers["optional_id"], mod.coerce_integer)
        self.assertIs(coercers["name"], mod.coerce_noop)
        self.assertIs(coercers["optional_name"], mod.coerce_string_nullable)
        self.assertIs(coercers["flag"], mod.coerce_boolean)
        self.assertIs(coercers["optional_flag"], mod.coerce_boolean_nullable)
        self.assertIs(coercers["dt"], mod.coerce_datetime)
        self.assertIs(coercers["optional_dt"], mod.coerce_datetime)
        self.assertIs(coercers["dec"], mod.coerce_decimal)
        self.assertIs(coercers["optional_dec"], mod.coerce_decimal)
        self.assertIs(coercers["flt"], mod.coerce_float)
        self.assertIs(coercers["optional_flt"], mod.coerce_float)


class TestMakeCoercer(TestCase):

    def test_basic(self):
        func = mod.make_coercer(Example.id)
        self.assertIs(func, mod.coerce_integer)

        func = mod.make_coercer(Example.optional_id)
        self.assertIs(func, mod.coerce_integer)

        func = mod.make_coercer(Example.name)
        self.assertIs(func, mod.coerce_noop)

        func = mod.make_coercer(Example.optional_name)
        self.assertIs(func, mod.coerce_string_nullable)

        func = mod.make_coercer(Example.flag)
        self.assertIs(func, mod.coerce_boolean)

        func = mod.make_coercer(Example.optional_flag)
        self.assertIs(func, mod.coerce_boolean_nullable)

        func = mod.make_coercer(Example.dt)
        self.assertIs(func, mod.coerce_datetime)

        func = mod.make_coercer(Example.optional_dt)
        self.assertIs(func, mod.coerce_datetime)

        func = mod.make_coercer(Example.dec)
        self.assertIs(func, mod.coerce_decimal)

        func = mod.make_coercer(Example.optional_dec)
        self.assertIs(func, mod.coerce_decimal)

        func = mod.make_coercer(Example.flt)
        self.assertIs(func, mod.coerce_float)

        func = mod.make_coercer(Example.optional_flt)
        self.assertIs(func, mod.coerce_float)


class TestCoercers(TestCase):

    def test_coerce_boolean(self):
        self.assertTrue(mod.coerce_boolean("true"))
        self.assertTrue(mod.coerce_boolean("1"))
        self.assertTrue(mod.coerce_boolean("yes"))

        self.assertFalse(mod.coerce_boolean("false"))
        self.assertFalse(mod.coerce_boolean("0"))
        self.assertFalse(mod.coerce_boolean("no"))

        self.assertFalse(mod.coerce_boolean(""))

    def test_coerce_boolean_nullable(self):
        self.assertTrue(mod.coerce_boolean_nullable("true"))
        self.assertTrue(mod.coerce_boolean_nullable("1"))
        self.assertTrue(mod.coerce_boolean_nullable("yes"))

        self.assertFalse(mod.coerce_boolean_nullable("false"))
        self.assertFalse(mod.coerce_boolean_nullable("0"))
        self.assertFalse(mod.coerce_boolean_nullable("no"))

        self.assertIsNone(mod.coerce_boolean_nullable(""))

    def test_coerce_datetime(self):
        self.assertIsNone(mod.coerce_datetime(""))

        value = mod.coerce_datetime("2025-10-19 20:56:00")
        self.assertIsInstance(value, datetime.datetime)
        self.assertEqual(value, datetime.datetime(2025, 10, 19, 20, 56))

        value = mod.coerce_datetime("2025-10-19 20:56:00.1234")
        self.assertIsInstance(value, datetime.datetime)
        self.assertEqual(value, datetime.datetime(2025, 10, 19, 20, 56, 0, 123400))

        self.assertRaises(ValueError, mod.coerce_datetime, "XXX")

    def test_coerce_decimal(self):
        self.assertIsNone(mod.coerce_decimal(""))

        value = mod.coerce_decimal("42")
        self.assertIsInstance(value, decimal.Decimal)
        self.assertEqual(value, decimal.Decimal("42.0"))
        self.assertEqual(value, 42)

        value = mod.coerce_decimal("42.0")
        self.assertIsInstance(value, decimal.Decimal)
        self.assertEqual(value, decimal.Decimal("42.0"))
        self.assertEqual(value, 42)

        self.assertRaises(decimal.InvalidOperation, mod.coerce_decimal, "XXX")

    def test_coerce_float(self):
        self.assertEqual(mod.coerce_float("42"), 42.0)
        self.assertEqual(mod.coerce_float("42.0"), 42.0)

        self.assertIsNone(mod.coerce_float(""))

        self.assertRaises(ValueError, mod.coerce_float, "XXX")

    def test_coerce_integer(self):
        self.assertEqual(mod.coerce_integer("42"), 42)
        self.assertRaises(ValueError, mod.coerce_integer, "42.0")

        self.assertIsNone(mod.coerce_integer(""))

        self.assertRaises(ValueError, mod.coerce_integer, "XXX")

    def test_coerce_noop(self):
        self.assertEqual(mod.coerce_noop(""), "")

        self.assertEqual(mod.coerce_noop("42"), "42")
        self.assertEqual(mod.coerce_noop("XXX"), "XXX")

    def test_coerce_string_nullable(self):
        self.assertIsNone(mod.coerce_string_nullable(""))

        self.assertEqual(mod.coerce_string_nullable("42"), "42")
        self.assertEqual(mod.coerce_string_nullable("XXX"), "XXX")

    def test_coerce_uuid(self):
        self.assertIsNone(mod.coerce_uuid(""))

        uuid = mod.coerce_uuid("06753693d89277f08000ce71bf7ebbba")
        self.assertIsInstance(uuid, _uuid.UUID)
        self.assertEqual(uuid, _uuid.UUID("06753693d89277f08000ce71bf7ebbba"))
        self.assertEqual(uuid.hex, "06753693d89277f08000ce71bf7ebbba")

        uuid = mod.coerce_uuid("06753693-d892-77f0-8000-ce71bf7ebbba")
        self.assertIsInstance(uuid, _uuid.UUID)
        self.assertEqual(uuid, _uuid.UUID("06753693-d892-77f0-8000-ce71bf7ebbba"))
        self.assertEqual(str(uuid), "06753693-d892-77f0-8000-ce71bf7ebbba")
        self.assertEqual(uuid.hex, "06753693d89277f08000ce71bf7ebbba")
