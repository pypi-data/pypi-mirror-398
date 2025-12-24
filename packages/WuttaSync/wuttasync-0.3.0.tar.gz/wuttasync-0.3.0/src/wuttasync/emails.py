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
:term:`Email Settings <email setting>` for WuttaSync
"""

import datetime
import re
from uuid import UUID

from wuttjamaican.email import EmailSetting
from wuttjamaican.diffs import Diff


class ImportExportWarning(EmailSetting):
    """
    Base class for import/export diff warnings; sent when unexpected
    changes occur.

    This inherits from :class:`~wuttjamaican.email.EmailSetting`.
    """

    fallback_key = "import_export_warning"
    ""  # suppress docs

    import_handler_spec = None
    import_handler_key = None

    def get_description(self):  # pylint: disable=empty-docstring
        """ """
        handler = self.get_import_handler()
        return f"Diff warning email for {handler.actioning} {handler.get_title()}"

    def get_default_subject(self):  # pylint: disable=empty-docstring
        """ """
        handler = self.get_import_handler()
        return f"Changes for {handler.get_title()}"

    def get_import_handler(self):  # pylint: disable=missing-function-docstring

        # prefer explicit spec, if set
        if self.import_handler_spec:
            return self.app.load_object(self.import_handler_spec)(self.config)

        # next try spec lookup, if key set
        if self.import_handler_key:
            return self.app.get_import_handler(self.import_handler_key, require=True)

        # or maybe try spec lookup basd on setting class name
        class_name = self.__class__.__name__
        if match := re.match(
            r"^(?P<action>import|export)_to_(?P<target>\S+)_from_(?P<source>\S+)_warning$",
            class_name,
        ):
            key = f"{match['action']}.to_{match['target']}.from_{match['source']}"
            return self.app.get_import_handler(key, require=True)

        raise ValueError(
            "must set import_handler_spec (or import_handler_key) "
            f"for email setting: {class_name}"
        )

    # nb. this is just used for sample data
    def make_diff(self, *args, **kwargs):  # pylint: disable=missing-function-docstring
        return Diff(self.config, *args, **kwargs)

    def sample_data(self):  # pylint: disable=empty-docstring
        """ """
        model = self.app.model
        handler = self.get_import_handler()

        alice = model.User(username="alice")
        bob = model.User(username="bob")
        charlie = model.User(username="charlie")

        runtime = datetime.timedelta(seconds=30)
        return {
            "handler": handler,
            "title": handler.get_title(),
            "source_title": handler.get_source_title(),
            "target_title": handler.get_target_title(),
            "runtime": runtime,
            "runtime_display": "30 seconds",
            "dry_run": True,
            "argv": [
                "bin/wutta",
                "import-foo",
                "User",
                "--delete",
                "--dry-run",
                "-W",
            ],
            "changes": {
                "User": (
                    [
                        (
                            alice,
                            {
                                "uuid": UUID("06946d64-1ebf-79db-8000-ce40345044fe"),
                                "username": "alice",
                            },
                        ),
                    ],
                    [
                        (
                            bob,
                            {
                                "uuid": UUID("06946d64-1ebf-7a8c-8000-05d78792b084"),
                                "username": "bob",
                            },
                            {
                                "uuid": UUID("06946d64-1ebf-7a8c-8000-05d78792b084"),
                                "username": "bobbie",
                            },
                        ),
                    ],
                    [
                        (
                            charlie,
                            {
                                "uuid": UUID("06946d64-1ebf-7ad4-8000-1ba52f720c48"),
                                "username": "charlie",
                            },
                        ),
                    ],
                ),
            },
            "make_diff": self.make_diff,
            "max_diffs": 15,
        }


class import_to_versions_from_wutta_warning(  # pylint: disable=invalid-name
    ImportExportWarning
):
    """
    Diff warning for Wutta → Versions import.
    """


class import_to_wutta_from_csv_warning(  # pylint: disable=invalid-name
    ImportExportWarning
):
    """
    Diff warning for CSV → Wutta import.
    """
