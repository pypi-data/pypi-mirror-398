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
See also: :ref:`wutta-import-versions`
"""

import sys

import rich
import typer
from typing_extensions import Annotated

from wuttjamaican.cli import wutta_typer

from .base import import_command, ImportCommandHandler


@wutta_typer.command()
@import_command
def import_versions(  # pylint: disable=unused-argument
    ctx: typer.Context,
    comment: Annotated[
        str,
        typer.Option("--comment", "-m", help="Comment to set on the transaction."),
    ] = "import catch-up versions",
    **kwargs,
):
    """
    Import latest data to version tables, for Wutta DB
    """
    config = ctx.parent.wutta_config
    app = config.get_app()

    # warn/exit if libs are not installed
    try:
        import wutta_continuum  # pylint: disable=import-outside-toplevel,unused-import
    except ImportError:  # pragma: no cover
        rich.print(
            "\n\t[bold yellow]Wutta-Continum is not installed![/bold yellow]\n"
            "\n\tIf you want it, run:   pip install Wutta-Continuum\n"
        )
        sys.exit(1)

    # warn/exit if feature disabled
    if not app.continuum_is_enabled():  # pragma: no cover
        rich.print(
            "\n\t[bold yellow]Wutta-Continum is not enabled![/bold yellow]\n"
            "\n\tIf you want it, see:   https://docs.wuttaproject.org/wutta-continuum/\n"
        )
        sys.exit(1)

    handler = ImportCommandHandler(config, key="import.to_versions.from_wutta")
    handler.run(ctx.params)
