# -*- coding: utf-8; -*-

from unittest import TestCase

from wuttasync import util as mod


class TestDataDiffs(TestCase):

    def test_source_missing_field(self):
        source = {"foo": "bar"}
        target = {"baz": "xyz", "foo": "bar"}
        self.assertRaises(KeyError, mod.data_diffs, source, target)

    def test_target_missing_field(self):
        source = {"foo": "bar", "baz": "xyz"}
        target = {"baz": "xyz"}
        self.assertRaises(
            KeyError, mod.data_diffs, source, target, fields=["foo", "baz"]
        )

    def test_no_diffs(self):
        source = {"foo": "bar", "baz": "xyz"}
        target = {"baz": "xyz", "foo": "bar"}
        self.assertFalse(mod.data_diffs(source, target))

    def test_with_diffs(self):
        source = {"foo": "bar", "baz": "xyz"}
        target = {"baz": "xyz", "foo": "BAR"}
        result = mod.data_diffs(source, target)
        self.assertEqual(result, ["foo"])
