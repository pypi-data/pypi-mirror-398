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
Testing utilities
"""

from wuttjamaican.testing import ConfigTestCase


class ImportExportWarningTestCase(ConfigTestCase):
    """
    Base class for testing the import/export warning email settings.

    This inherits from
    :class:`~wuttjamaican:wuttjamaican.testing.ConfigTestCase`.

    Example usage::

       from wuttasync.testing import ImportExportWarningTestCase

       class TestEmailSettings(ImportExportWarningTestCase):

           def test_import_to_wutta_from_foo_warning(self):
               self.do_test_preview("import_to_wutta_from_foo_warning")

           def test_export_to_foo_from_wutta_warning(self):
               self.do_test_preview("export_to_foo_from_wutta_warning")
    """

    app_title = "Wutta Poser"

    def setUp(self):
        self.setup_config()
        self.config.setdefault("wutta.app_title", self.app_title)

    def make_preview(  # pylint: disable=missing-function-docstring,unused-argument
        self, key, mode="html"
    ):
        handler = self.app.get_email_handler()
        setting = handler.get_email_setting(key)
        context = setting.sample_data()
        return handler.get_auto_html_body(
            setting.key, context, fallback_key=setting.fallback_key
        )

    def do_test_preview(self, key):  # pylint: disable=missing-function-docstring
        body = self.make_preview(key, mode="html")
        self.assertIn("Diff warning for ", body)
