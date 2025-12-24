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
See also: :ref:`wutta-import-csv`
"""

import typer

from wuttjamaican.cli import wutta_typer

from .base import file_import_command, ImportCommandHandler


@wutta_typer.command()
@file_import_command
def import_csv(ctx: typer.Context, **kwargs):  # pylint: disable=unused-argument
    """
    Import data from CSV file(s) to Wutta DB
    """
    config = ctx.parent.wutta_config
    handler = ImportCommandHandler(config, key="import.to_wutta.from_csv")
    handler.run(ctx.params)
