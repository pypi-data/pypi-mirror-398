# -*- coding: utf-8; -*-

from collections import OrderedDict
from unittest.mock import patch
from uuid import UUID

from wuttjamaican.testing import DataTestCase

from wuttasync.importing import handlers as mod, Importer, ToSqlalchemy


class FromFooToBar(mod.ImportHandler):
    source_key = "foo"
    target_key = "bar"


class TestImportHandler(DataTestCase):

    def make_handler(self, **kwargs):
        return mod.ImportHandler(self.config, **kwargs)

    def test_str(self):
        handler = self.make_handler()
        self.assertEqual(str(handler), "None → None")

        handler.source_title = "CSV"
        handler.target_title = "Wutta"
        self.assertEqual(str(handler), "CSV → Wutta")

    def test_actioning(self):
        handler = self.make_handler()
        self.assertEqual(handler.actioning, "importing")

        handler.orientation = mod.Orientation.EXPORT
        self.assertEqual(handler.actioning, "exporting")

    def test_get_key(self):
        handler = self.make_handler()
        self.assertEqual(handler.get_key(), "import.to_None.from_None")

        with patch.multiple(mod.ImportHandler, source_key="csv", target_key="wutta"):
            self.assertEqual(handler.get_key(), "import.to_wutta.from_csv")

    def test_get_spec(self):
        handler = self.make_handler()
        self.assertEqual(
            handler.get_spec(), "wuttasync.importing.handlers:ImportHandler"
        )

    def test_get_title(self):
        handler = self.make_handler()
        self.assertEqual(handler.get_title(), "None → None")

        handler.source_title = "CSV"
        handler.target_title = "Wutta"
        self.assertEqual(handler.get_title(), "CSV → Wutta")

    def test_get_source_title(self):
        handler = self.make_handler()

        # null by default
        self.assertIsNone(handler.get_source_title())

        # which is really using source_key as fallback
        handler.source_key = "csv"
        self.assertEqual(handler.get_source_title(), "csv")

        # can also use (defined) generic fallback
        handler.generic_source_title = "CSV"
        self.assertEqual(handler.get_source_title(), "CSV")

        # or can set explicitly
        handler.source_title = "XXX"
        self.assertEqual(handler.get_source_title(), "XXX")

    def test_get_target_title(self):
        handler = self.make_handler()

        # null by default
        self.assertIsNone(handler.get_target_title())

        # which is really using target_key as fallback
        handler.target_key = "wutta"
        self.assertEqual(handler.get_target_title(), "wutta")

        # can also use (defined) generic fallback
        handler.generic_target_title = "Wutta"
        self.assertEqual(handler.get_target_title(), "Wutta")

        # or can set explicitly
        handler.target_title = "XXX"
        self.assertEqual(handler.get_target_title(), "XXX")

    def test_process_data(self):
        model = self.app.model
        handler = self.make_handler()

        # empy/no-op should commit (not fail)
        with patch.object(handler, "commit_transaction") as commit_transaction:
            handler.process_data()
            commit_transaction.assert_called_once_with()

        # do that again with no patch, just for kicks
        handler.process_data()

        # dry-run should rollback
        with patch.object(handler, "commit_transaction") as commit_transaction:
            with patch.object(handler, "rollback_transaction") as rollback_transaction:
                handler.process_data(dry_run=True)
                self.assertFalse(commit_transaction.called)
                rollback_transaction.assert_called_once_with()

        # and do that with no patch, for kicks
        handler.process_data(dry_run=True)

        # outright error should cause rollback
        with patch.object(handler, "commit_transaction") as commit_transaction:
            with patch.object(handler, "rollback_transaction") as rollback_transaction:
                with patch.object(handler, "get_importer", side_effect=RuntimeError):
                    self.assertRaises(RuntimeError, handler.process_data, "BlahBlah")
                    self.assertFalse(commit_transaction.called)
                    rollback_transaction.assert_called_once_with()

        # fake importer class/data
        mock_source_objects = [{"name": "foo", "value": "bar"}]

        class SettingImporter(ToSqlalchemy):
            model_class = model.Setting
            target_session = self.session

            def get_source_objects(self):
                return mock_source_objects

        # now for a "normal" one
        handler.importers["Setting"] = SettingImporter
        self.assertEqual(self.session.query(model.Setting).count(), 0)
        handler.process_data("Setting")
        self.assertEqual(self.session.query(model.Setting).count(), 1)

        # then add another mock record
        mock_source_objects.append({"name": "foo2", "value": "bar2"})
        handler.process_data("Setting")
        self.assertEqual(self.session.query(model.Setting).count(), 2)

        # nb. even if dry-run, record is added
        # (rollback would happen later in that case)
        mock_source_objects.append({"name": "foo3", "value": "bar3"})
        handler.process_data("Setting", dry_run=True)
        self.assertEqual(self.session.query(model.Setting).count(), 3)

    def test_consume_kwargs(self):
        handler = self.make_handler()

        # kwargs are returned as-is
        kw = {}
        result = handler.consume_kwargs(kw)
        self.assertIs(result, kw)
        self.assertEqual(result, {})

        # dry_run (not consumed)
        self.assertFalse(handler.dry_run)
        kw["dry_run"] = True
        result = handler.consume_kwargs(kw)
        self.assertIs(result, kw)
        self.assertIn("dry_run", kw)
        self.assertTrue(kw["dry_run"])
        self.assertTrue(handler.dry_run)

        # warnings (consumed)
        self.assertFalse(handler.warnings)
        kw["warnings"] = True
        result = handler.consume_kwargs(kw)
        self.assertIs(result, kw)
        self.assertNotIn("warnings", kw)
        self.assertTrue(handler.warnings)

        # warnings_recipients (consumed)
        self.assertIsNone(handler.warnings_recipients)
        kw["warnings_recipients"] = "bob@example.com"
        result = handler.consume_kwargs(kw)
        self.assertIs(result, kw)
        self.assertNotIn("warnings_recipients", kw)
        self.assertEqual(handler.warnings_recipients, ["bob@example.com"])

        # warnings_max_diffs (consumed)
        self.assertEqual(handler.warnings_max_diffs, 15)
        kw["warnings_max_diffs"] = 30
        result = handler.consume_kwargs(kw)
        self.assertIs(result, kw)
        self.assertNotIn("warnings_max_diffs", kw)
        self.assertEqual(handler.warnings_max_diffs, 30)

    def test_define_importers(self):
        handler = self.make_handler()
        importers = handler.define_importers()
        self.assertEqual(importers, {})
        self.assertIsInstance(importers, OrderedDict)

    def test_get_importer(self):
        model = self.app.model
        handler = self.make_handler()

        # normal
        handler.importers["Setting"] = Importer
        importer = handler.get_importer("Setting", model_class=model.Setting)
        self.assertIsInstance(importer, Importer)

        # specifying empty keys
        handler.importers["Setting"] = Importer
        importer = handler.get_importer("Setting", model_class=model.Setting, keys=None)
        self.assertIsInstance(importer, Importer)
        importer = handler.get_importer("Setting", model_class=model.Setting, keys="")
        self.assertIsInstance(importer, Importer)
        importer = handler.get_importer("Setting", model_class=model.Setting, keys=[])
        self.assertIsInstance(importer, Importer)

        # key not found
        self.assertRaises(
            KeyError, handler.get_importer, "BunchOfNonsense", model_class=model.Setting
        )

    def test_get_warnings_email_key(self):
        handler = FromFooToBar(self.config)

        # default
        key = handler.get_warnings_email_key()
        self.assertEqual(key, "import_to_bar_from_foo_warning")

        # override
        handler.warnings_email_key = "from_foo_to_bar"
        key = handler.get_warnings_email_key()
        self.assertEqual(key, "from_foo_to_bar")

    def test_process_changes(self):
        model = self.app.model
        handler = self.make_handler()
        email_handler = self.app.get_email_handler()

        handler.process_started = self.app.localtime()

        alice = model.User(username="alice")
        bob = model.User(username="bob")
        charlie = model.User(username="charlie")

        changes = {
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
        }

        # no email if not in warnings mode
        self.assertFalse(handler.warnings)
        with patch.object(self.app, "send_email") as send_email:
            handler.process_changes(changes)
            send_email.assert_not_called()

        # email sent (to default recip) if in warnings mode
        handler.warnings = True
        self.config.setdefault("wutta.email.default.to", "admin@example.com")
        with patch.object(email_handler, "deliver_message") as deliver_message:
            handler.process_changes(changes)
            deliver_message.assert_called_once()
            args, kwargs = deliver_message.call_args
            self.assertEqual(kwargs, {"recips": None})
            self.assertEqual(len(args), 1)
            msg = args[0]
            self.assertEqual(msg.to, ["admin@example.com"])

        # can override email recip
        handler.warnings_recipients = ["bob@example.com"]
        with patch.object(email_handler, "deliver_message") as deliver_message:
            handler.process_changes(changes)
            deliver_message.assert_called_once()
            args, kwargs = deliver_message.call_args
            self.assertEqual(kwargs, {"recips": None})
            self.assertEqual(len(args), 1)
            msg = args[0]
            self.assertEqual(msg.to, ["bob@example.com"])


class TestFromFileHandler(DataTestCase):

    def make_handler(self, **kwargs):
        return mod.FromFileHandler(self.config, **kwargs)

    def test_process_data(self):
        handler = self.make_handler()
        path = self.write_file("data.txt", "")
        with patch.object(mod.ImportHandler, "process_data") as process_data:

            # bare
            handler.process_data()
            process_data.assert_called_once_with()

            # with file path
            process_data.reset_mock()
            handler.process_data(input_file_path=path)
            process_data.assert_called_once_with(input_file_path=path)

            # with folder
            process_data.reset_mock()
            handler.process_data(input_file_path=self.tempdir)
            process_data.assert_called_once_with(input_file_dir=self.tempdir)


class TestFromSqlalchemyHandler(DataTestCase):

    def make_handler(self, **kwargs):
        return mod.FromSqlalchemyHandler(self.config, **kwargs)

    def test_make_source_session(self):
        handler = self.make_handler()
        self.assertRaises(NotImplementedError, handler.make_source_session)

    def test_begin_source_transaction(self):
        handler = self.make_handler()
        self.assertIsNone(handler.source_session)
        with patch.object(handler, "make_source_session", return_value=self.session):
            handler.begin_source_transaction()
        self.assertIs(handler.source_session, self.session)

    def test_commit_source_transaction(self):
        model = self.app.model
        handler = self.make_handler()
        handler.source_session = self.session
        self.assertEqual(self.session.query(model.User).count(), 0)

        # nb. do not commit this yet
        user = model.User(username="fred")
        self.session.add(user)

        self.assertTrue(self.session.in_transaction())
        self.assertIn(user, self.session)
        handler.commit_source_transaction()
        self.assertIsNone(handler.source_session)
        self.assertFalse(self.session.in_transaction())
        self.assertNotIn(user, self.session)  # hm, surprising?
        self.assertEqual(self.session.query(model.User).count(), 1)

    def test_rollback_source_transaction(self):
        model = self.app.model
        handler = self.make_handler()
        handler.source_session = self.session
        self.assertEqual(self.session.query(model.User).count(), 0)

        # nb. do not commit this yet
        user = model.User(username="fred")
        self.session.add(user)

        self.assertTrue(self.session.in_transaction())
        self.assertIn(user, self.session)
        handler.rollback_source_transaction()
        self.assertIsNone(handler.source_session)
        self.assertFalse(self.session.in_transaction())
        self.assertNotIn(user, self.session)
        self.assertEqual(self.session.query(model.User).count(), 0)

    def test_get_importer_kwargs(self):
        handler = self.make_handler()
        handler.source_session = self.session
        kw = handler.get_importer_kwargs("User")
        self.assertIn("source_session", kw)
        self.assertIs(kw["source_session"], self.session)


class TestFromWuttaHandler(DataTestCase):

    def make_handler(self, **kwargs):
        return mod.FromWuttaHandler(self.config, **kwargs)

    def test_get_source_title(self):
        handler = self.make_handler()

        # uses app title by default
        self.config.setdefault("wutta.app_title", "What About This")
        self.assertEqual(handler.get_source_title(), "What About This")

        # or generic default if present
        handler.generic_source_title = "WHATABOUTTHIS"
        self.assertEqual(handler.get_source_title(), "WHATABOUTTHIS")

        # but prefer specific title if present
        handler.source_title = "what_about_this"
        self.assertEqual(handler.get_source_title(), "what_about_this")

    def test_make_source_session(self):
        handler = self.make_handler()

        # makes "new" (mocked in our case) app session
        with patch.object(self.app, "make_session") as make_session:
            make_session.return_value = self.session
            session = handler.make_source_session()
            make_session.assert_called_once_with()
            self.assertIs(session, self.session)


class TestToSqlalchemyHandler(DataTestCase):

    def make_handler(self, **kwargs):
        return mod.ToSqlalchemyHandler(self.config, **kwargs)

    def test_begin_target_transaction(self):
        handler = self.make_handler()
        with patch.object(handler, "make_target_session") as make_target_session:
            make_target_session.return_value = self.session
            self.assertIsNone(handler.target_session)
            handler.begin_target_transaction()
            make_target_session.assert_called_once_with()

    def test_rollback_target_transaction(self):
        handler = self.make_handler()
        with patch.object(handler, "make_target_session") as make_target_session:
            make_target_session.return_value = self.session
            self.assertIsNone(handler.target_session)
            handler.begin_target_transaction()
            self.assertIs(handler.target_session, self.session)
            handler.rollback_target_transaction()
            self.assertIsNone(handler.target_session)

    def test_commit_target_transaction(self):
        handler = self.make_handler()
        with patch.object(handler, "make_target_session") as make_target_session:
            make_target_session.return_value = self.session
            self.assertIsNone(handler.target_session)
            handler.begin_target_transaction()
            self.assertIs(handler.target_session, self.session)
            handler.commit_target_transaction()
            self.assertIsNone(handler.target_session)

    def test_make_target_session(self):
        handler = self.make_handler()
        self.assertRaises(NotImplementedError, handler.make_target_session)

    def test_get_importer_kwargs(self):
        handler = self.make_handler()
        handler.target_session = self.session
        kw = handler.get_importer_kwargs("Setting")
        self.assertIn("target_session", kw)
        self.assertIs(kw["target_session"], self.session)


class TestToWuttaHandler(DataTestCase):

    def make_handler(self, **kwargs):
        return mod.ToWuttaHandler(self.config, **kwargs)

    def test_get_target_title(self):
        handler = self.make_handler()

        # uses app title by default
        self.config.setdefault("wutta.app_title", "What About This")
        self.assertEqual(handler.get_target_title(), "What About This")

        # or generic default if present
        handler.generic_target_title = "WHATABOUTTHIS"
        self.assertEqual(handler.get_target_title(), "WHATABOUTTHIS")

        # but prefer specific title if present
        handler.target_title = "what_about_this"
        self.assertEqual(handler.get_target_title(), "what_about_this")

    def test_make_target_session(self):
        handler = self.make_handler()

        # makes "new" (mocked in our case) app session
        with patch.object(self.app, "make_session") as make_session:
            make_session.return_value = self.session
            session = handler.make_target_session()
            make_session.assert_called_once_with()
            self.assertIs(session, self.session)
