# -*- coding: utf-8; -*-
################################################################################
#
#  WuttaSync -- Wutta Framework for data import/export and real-time sync
#  Copyright © 2024 Lance Edgar
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
Data Utilities
"""


def data_diffs(source_data, target_data, fields=None):
    """
    Find all (relevant) fields with differing values between the two
    data records, source and target.

    :param source_data: Dict of normalized record from source data.

    :param target_data: Dict of normalized record from target data.

    :param fields: Optional list of fields to check.  If not
       specified, all fields present in ``target_data`` will be
       checked.

    :returns: Possibly empty list of field names which were found to
       differ between source and target record.
    """
    if fields is None:
        fields = list(target_data)

    diffs = []
    for field in fields:

        if field not in target_data:
            raise KeyError(f"field '{field}' is missing from target_data")
        if field not in source_data:
            raise KeyError(f"field '{field}' is missing from source_data")

        target_value = target_data[field]
        source_value = source_data[field]
        if target_value != source_value:
            diffs.append(field)

    return diffs
