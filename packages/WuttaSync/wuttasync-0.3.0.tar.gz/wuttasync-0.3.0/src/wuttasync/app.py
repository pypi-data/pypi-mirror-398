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
App handler supplement for WuttaSync
"""

from collections import OrderedDict

from wuttjamaican.app import AppProvider
from wuttjamaican.util import load_entry_points


class WuttaSyncAppProvider(AppProvider):
    """
    The :term:`app provider` for WuttaSync.

    This adds some methods to the :term:`app handler`, which are
    specific to import/export.

    It also declares some :term:`email modules <email module>` and
    :term:`email templates <email template>` for the app.

    We have two concerns when doing lookups etc. for import/export
    handlers:

    * which handlers are *available* - i.e. they exist and are
      discoverable
    * which handlers are *designated* - only one designated handler
      per key

    All "available" handlers will have a key, but some keys may be
    referenced by multiple handlers.  For each key, only one handler
    can be "designated" - there is a default, but config can override.
    """

    email_modules = ["wuttasync.emails"]
    email_templates = ["wuttasync:email-templates"]

    def get_all_import_handlers(self):
        """
        Returns *all* :term:`import/export handler <import handler>`
        *classes* which are known to exist, i.e.  are discoverable.

        See also :meth:`get_import_handler()` and
        :meth:`get_designated_import_handlers()`.

        The discovery process is as follows:

        * load handlers from registered entry points
        * check config for designated handlers

        Checking for designated handler config is not a reliable way
        to discover handlers, but it's done just in case any new ones
        might be found.

        Registration via entry points is the only way to ensure a
        handler is discoverable.  The entry point group name is always
        ``wuttasync.importing`` regardless of :term:`app name`;
        entries are like ``"handler_key" = "handler_spec"``.  For
        example:

        .. code-block:: toml

           [project.entry-points."wuttasync.importing"]
           "export.to_csv.from_poser" = "poser.exporting.csv:FromPoserToCsv"
           "import.to_poser.from_csv" = "poser.importing.csv:FromCsvToPoser"

        :returns: List of all import/export handler classes
        """
        # first load all "registered" Handler classes
        factories = load_entry_points("wuttasync.importing", ignore_errors=True)

        # organize registered classes by spec
        specs = {factory.get_spec(): factory for factory in factories.values()}

        # many handlers may not be registered per se, but may be
        # designated via config.  so try to include those too
        for factory in factories.values():
            spec = self.get_designated_import_handler_spec(factory.get_key())
            if spec and spec not in specs:
                specs[spec] = self.app.load_object(spec)

        # flatten back to simple list of classes
        factories = list(specs.values())
        return factories

    def get_designated_import_handler_spec(self, key, require=False):
        """
        Returns the designated import/export handler :term:`spec`
        string for the given type key.

        This just checks config for the designated handler, using the
        ``wuttasync.importing`` prefix regardless of :term:`app name`.
        For instance:

        .. code-block:: ini

           [wuttasync.importing]
           export.to_csv.from_poser.handler = poser.exporting.csv:FromPoserToCsv
           import.to_poser.from_csv.handler = poser.importing.csv:FromCsvToPoser

        See also :meth:`get_designated_import_handlers()` and
        :meth:`get_import_handler()`.

        :param key: Unique key indicating the type of import/export
           handler.

        :param require: Flag indicating whether an error should be raised if no
           handler is found.

        :returns: Spec string for the designated handler.  If none is
           configured, then ``None`` is returned *unless* the
           ``require`` param is true, in which case an error is
           raised.
        """
        spec = self.config.get(f"wuttasync.importing.{key}.handler")
        if spec:
            return spec

        spec = self.config.get(f"wuttasync.importing.{key}.default_handler")
        if spec:
            return spec

        if require:
            raise ValueError(f"Cannot locate import handler spec for key: {key}")
        return None

    def get_designated_import_handlers(self):
        """
        Returns all *designated* import/export handler *instances*.

        Each import/export handler has a "key" which indicates the
        "type" of import/export job it performs.  For instance the CSV
        → Wutta import has the key: ``import.to_wutta.from_csv``

        More than one handler can be defined for that key; however
        only one such handler will be "designated" for each key.

        This method first loads *all* available import handlers, then
        organizes them by key, and tries to determine which handler
        should be designated for each key.

        See also :meth:`get_all_import_handlers()` and
        :meth:`get_designated_import_handler_spec()`.

        :returns: List of designated import/export handler instances
        """
        grouped = OrderedDict()
        for factory in self.get_all_import_handlers():
            key = factory.get_key()
            grouped.setdefault(key, []).append(factory)

        def find_designated(key, group):
            spec = self.get_designated_import_handler_spec(key)
            if spec:
                for factory in group:
                    if factory.get_spec() == spec:
                        return factory
            if len(group) == 1:
                return group[0]
            return None

        designated = []
        for key, group in grouped.items():
            factory = find_designated(key, group)
            if factory:
                handler = factory(self.config)
                designated.append(handler)

        return designated

    def get_import_handler(self, key, require=False, **kwargs):
        """
        Returns the designated :term:`import/export handler <import
        handler>` instance for the given :term:`import/export key`.

        See also :meth:`get_all_import_handlers()` and
        :meth:`get_designated_import_handlers()`.

        :param key: Key indicating the type of import/export handler,
           e.g. ``"import.to_wutta.from_csv"``

        :param require: Set this to true if you want an error raised
           when no handler is found.

        :returns: The import/export handler instance.  If no handler
           is found, then ``None`` is returned, unless ``require``
           param is true, in which case error is raised.
        """
        # first try to fetch the handler per designated spec
        spec = self.get_designated_import_handler_spec(key, **kwargs)
        if spec:
            factory = self.app.load_object(spec)
            return factory(self.config)

        # nothing was designated, so leverage logic which already
        # sorts out which handler is "designated" for given key
        designated = self.get_designated_import_handlers()
        for handler in designated:
            if handler.get_key() == key:
                return handler

        if require:
            raise ValueError(f"Cannot locate import handler for key: {key}")
        return None
