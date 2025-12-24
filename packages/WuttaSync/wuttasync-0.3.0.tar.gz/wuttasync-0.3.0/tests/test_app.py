# -*- coding: utf-8; -*-

from wuttjamaican.testing import ConfigTestCase

from wuttasync import app as mod
from wuttasync.importing import ImportHandler
from wuttasync.importing.csv import FromCsvToWutta


class FromFooToBar(ImportHandler):
    source_key = "foo"
    target_key = "bar"


class FromCsvToPoser(FromCsvToWutta):
    pass


class TestWuttaSyncAppProvider(ConfigTestCase):

    def test_get_all_import_handlers(self):

        # by default our custom handler is not found
        handlers = self.app.get_all_import_handlers()
        self.assertIn(FromCsvToWutta, handlers)
        self.assertNotIn(FromFooToBar, handlers)

        # make sure if we configure a custom handler, it is found
        self.config.setdefault(
            "wuttasync.importing.import.to_wutta.from_csv.handler",
            "tests.test_app:FromFooToBar",
        )
        handlers = self.app.get_all_import_handlers()
        self.assertIn(FromCsvToWutta, handlers)
        self.assertIn(FromFooToBar, handlers)

    def test_get_designated_import_handler_spec(self):

        # fetch of unknown key returns none
        spec = self.app.get_designated_import_handler_spec("test01")
        self.assertIsNone(spec)

        # unless we require it, in which case, error
        self.assertRaises(
            ValueError,
            self.app.get_designated_import_handler_spec,
            "test01",
            require=True,
        )

        # we configure one for whatever key we like
        self.config.setdefault(
            "wuttasync.importing.test02.handler", "tests.test_app:FromBarToFoo"
        )
        spec = self.app.get_designated_import_handler_spec("test02")
        self.assertEqual(spec, "tests.test_app:FromBarToFoo")

        # we can also define a "default" designated handler
        self.config.setdefault(
            "wuttasync.importing.test03.default_handler",
            "tests.test_app:FromBarToFoo",
        )
        spec = self.app.get_designated_import_handler_spec("test03")
        self.assertEqual(spec, "tests.test_app:FromBarToFoo")

    def test_get_designated_import_handlers(self):

        # some designated handlers exist, but not our custom handler
        handlers = self.app.get_designated_import_handlers()
        csv_handlers = [
            h for h in handlers if h.get_key() == "import.to_wutta.from_csv"
        ]
        self.assertEqual(len(csv_handlers), 1)
        csv_handler = csv_handlers[0]
        self.assertIsInstance(csv_handler, FromCsvToWutta)
        self.assertFalse(isinstance(csv_handler, FromCsvToPoser))
        self.assertFalse(
            any([h.get_key() == "import.to_bar.from_foo" for h in handlers])
        )
        self.assertFalse(any([isinstance(h, FromFooToBar) for h in handlers]))
        self.assertFalse(any([isinstance(h, FromCsvToPoser) for h in handlers]))
        self.assertTrue(
            any([h.get_key() == "import.to_versions.from_wutta" for h in handlers])
        )

        # but we can make custom designated
        self.config.setdefault(
            "wuttasync.importing.import.to_wutta.from_csv.handler",
            "tests.test_app:FromCsvToPoser",
        )
        handlers = self.app.get_designated_import_handlers()
        csv_handlers = [
            h for h in handlers if h.get_key() == "import.to_wutta.from_csv"
        ]
        self.assertEqual(len(csv_handlers), 1)
        csv_handler = csv_handlers[0]
        self.assertIsInstance(csv_handler, FromCsvToWutta)
        self.assertIsInstance(csv_handler, FromCsvToPoser)
        self.assertTrue(
            any([h.get_key() == "import.to_versions.from_wutta" for h in handlers])
        )

    def test_get_import_handler(self):

        # make sure a basic fetch works
        handler = self.app.get_import_handler("import.to_wutta.from_csv")
        self.assertIsInstance(handler, FromCsvToWutta)
        self.assertFalse(isinstance(handler, FromCsvToPoser))

        # and make sure custom override works
        self.config.setdefault(
            "wuttasync.importing.import.to_wutta.from_csv.handler",
            "tests.test_app:FromCsvToPoser",
        )
        handler = self.app.get_import_handler("import.to_wutta.from_csv")
        self.assertIsInstance(handler, FromCsvToWutta)
        self.assertIsInstance(handler, FromCsvToPoser)

        # unknown importer cannot be found
        handler = self.app.get_import_handler("bogus")
        self.assertIsNone(handler)

        # and if we require it, error will raise
        self.assertRaises(
            ValueError, self.app.get_import_handler, "bogus", require=True
        )
