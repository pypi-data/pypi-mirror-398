# -*- coding: utf-8; -*-

from wuttjamaican.testing import ConfigTestCase

from wuttasync import emails as mod
from wuttasync.importing import ImportHandler
from wuttasync.testing import ImportExportWarningTestCase


class FromFooToWutta(ImportHandler):
    pass


class TestImportExportWarning(ConfigTestCase):

    def make_setting(self, factory=None):
        if not factory:
            factory = mod.ImportExportWarning
        setting = factory(self.config)
        return setting

    def test_get_description(self):
        self.config.setdefault("wutta.app_title", "Wutta Poser")
        setting = self.make_setting()
        setting.import_handler_key = "import.to_wutta.from_csv"
        self.assertEqual(
            setting.get_description(),
            "Diff warning email for importing CSV → Wutta Poser",
        )

    def test_get_default_subject(self):
        self.config.setdefault("wutta.app_title", "Wutta Poser")
        setting = self.make_setting()
        setting.import_handler_key = "import.to_wutta.from_csv"
        self.assertEqual(setting.get_default_subject(), "Changes for CSV → Wutta Poser")

    def test_get_import_handler(self):

        # nb. typical name pattern
        class import_to_wutta_from_foo_warning(mod.ImportExportWarning):
            pass

        # nb. name does not match spec pattern
        class import_to_wutta_from_bar_blah(mod.ImportExportWarning):
            pass

        # register our import handler
        self.config.setdefault(
            "wuttasync.importing.import.to_wutta.from_foo.handler",
            "tests.test_emails:FromFooToWutta",
        )

        # error if spec/key not discoverable
        setting = self.make_setting(import_to_wutta_from_bar_blah)
        self.assertRaises(ValueError, setting.get_import_handler)

        # can lookup by name (auto-spec)
        setting = self.make_setting(import_to_wutta_from_foo_warning)
        handler = setting.get_import_handler()
        self.assertIsInstance(handler, FromFooToWutta)

        # can lookup by explicit spec
        setting = self.make_setting(import_to_wutta_from_bar_blah)
        setting.import_handler_spec = "tests.test_emails:FromFooToWutta"
        handler = setting.get_import_handler()
        self.assertIsInstance(handler, FromFooToWutta)

        # can lookup by explicit key
        setting = self.make_setting(import_to_wutta_from_bar_blah)
        setting.import_handler_key = "import.to_wutta.from_foo"
        handler = setting.get_import_handler()
        self.assertIsInstance(handler, FromFooToWutta)


class TestEmailSettings(ImportExportWarningTestCase):

    def test_import_to_versions_from_wutta_warning(self):
        self.do_test_preview("import_to_versions_from_wutta_warning")

    def test_import_to_wutta_from_csv_warning(self):
        self.do_test_preview("import_to_wutta_from_csv_warning")
