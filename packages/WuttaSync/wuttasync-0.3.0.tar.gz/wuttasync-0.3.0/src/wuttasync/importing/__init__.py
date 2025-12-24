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
Data Import / Export Framework

This namespace exposes the following:

* :enum:`~wuttasync.importing.handlers.Orientation`

And some :term:`import handler` base classes:

* :class:`~wuttasync.importing.handlers.ImportHandler`
* :class:`~wuttasync.importing.handlers.FromFileHandler`
* :class:`~wuttasync.importing.handlers.ToSqlalchemyHandler`
* :class:`~wuttasync.importing.handlers.ToWuttaHandler`

And some :term:`importer` base classes:

* :class:`~wuttasync.importing.base.Importer`
* :class:`~wuttasync.importing.base.FromFile`
* :class:`~wuttasync.importing.base.ToSqlalchemy`
* :class:`~wuttasync.importing.model.ToWutta`
"""

from .handlers import (
    Orientation,
    ImportHandler,
    FromFileHandler,
    ToSqlalchemyHandler,
    ToWuttaHandler,
)
from .base import Importer, FromFile, ToSqlalchemy
from .model import ToWutta
