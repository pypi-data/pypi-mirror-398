# -*- coding: utf-8; -*-

import inspect
from unittest import TestCase
from unittest.mock import patch

from wuttasync.cli import base as mod
from wuttjamaican.testing import DataTestCase


class TestImportCommandHandler(DataTestCase):

    def make_handler(self, **kwargs):
        return mod.ImportCommandHandler(self.config, **kwargs)

    def test_import_handler(self):

        # none
        handler = self.make_handler()
        self.assertIsNone(handler.import_handler)

        FromCsvToWutta = self.app.load_object("wuttasync.importing.csv:FromCsvToWutta")

        # as spec
        handler = self.make_handler(import_handler=FromCsvToWutta.get_spec())
        self.assertIsInstance(handler.import_handler, FromCsvToWutta)

        # as factory
        handler = self.make_handler(import_handler=FromCsvToWutta)
        self.assertIsInstance(handler.import_handler, FromCsvToWutta)

        # as instance
        myhandler = FromCsvToWutta(self.config)
        handler = self.make_handler(import_handler=myhandler)
        self.assertIs(handler.import_handler, myhandler)

        # as key
        handler = self.make_handler(key="import.to_wutta.from_csv")
        self.assertIsInstance(handler.import_handler, FromCsvToWutta)

    def test_run(self):
        handler = self.make_handler(
            import_handler="wuttasync.importing.csv:FromCsvToWutta"
        )

        with patch.object(handler, "list_models") as list_models:
            handler.run({"list_models": True})
            list_models.assert_called_once_with({"list_models": True})

        with patch.object(handler, "import_handler") as import_handler:
            handler.run({"models": []})
            import_handler.process_data.assert_called_once_with()

    def test_list_models(self):
        handler = self.make_handler(
            import_handler="wuttasync.importing.csv:FromCsvToWutta"
        )

        with patch.object(mod, "sys") as sys:
            handler.list_models({})
            # just test a few random things we expect to see
            self.assertTrue(sys.stdout.write.has_call("ALL MODELS:\n"))
            self.assertTrue(sys.stdout.write.has_call("Person"))
            self.assertTrue(sys.stdout.write.has_call("User"))
            self.assertTrue(sys.stdout.write.has_call("Upgrade"))


class TestImporterCommand(TestCase):

    def test_basic(self):
        def myfunc(ctx, **kwargs):
            pass

        sig1 = inspect.signature(myfunc)
        self.assertIn("kwargs", sig1.parameters)
        self.assertNotIn("dry_run", sig1.parameters)
        wrapt = mod.import_command(myfunc)
        sig2 = inspect.signature(wrapt)
        self.assertNotIn("kwargs", sig2.parameters)
        self.assertIn("dry_run", sig2.parameters)


class TestFileImporterCommand(TestCase):

    def test_basic(self):
        def myfunc(ctx, **kwargs):
            pass

        sig1 = inspect.signature(myfunc)
        self.assertIn("kwargs", sig1.parameters)
        self.assertNotIn("dry_run", sig1.parameters)
        self.assertNotIn("input_file_path", sig1.parameters)
        wrapt = mod.file_import_command(myfunc)
        sig2 = inspect.signature(wrapt)
        self.assertNotIn("kwargs", sig2.parameters)
        self.assertIn("dry_run", sig2.parameters)
        self.assertIn("input_file_path", sig2.parameters)
