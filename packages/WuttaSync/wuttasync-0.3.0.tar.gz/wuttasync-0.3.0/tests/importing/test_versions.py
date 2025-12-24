# -*- coding: utf-8; -*-

from sqlalchemy import orm
import sqlalchemy_continuum as continuum

from wuttjamaican.util import make_true_uuid
from wutta_continuum.testing import VersionTestCase

from wuttasync.importing import versions as mod, Importer


class TestFromWuttaToVersions(VersionTestCase):

    def make_handler(self, **kwargs):
        return mod.FromWuttaToVersions(self.config, **kwargs)

    def test_consume_kwargs(self):

        # no comment by default
        handler = self.make_handler()
        kw = handler.consume_kwargs({})
        self.assertEqual(kw, {})
        self.assertIsNone(handler.continuum_comment)

        # but can provide one
        handler = self.make_handler()
        kw = handler.consume_kwargs({"comment": "yeehaw"})
        self.assertEqual(kw, {})
        self.assertEqual(handler.continuum_comment, "yeehaw")

    def test_begin_target_transaction(self):
        model = self.app.model
        txncls = continuum.transaction_class(model.User)

        # basic / defaults
        handler = self.make_handler()
        self.assertIsNone(handler.continuum_uow)
        self.assertIsNone(handler.continuum_txn)
        handler.begin_target_transaction()
        self.assertIsInstance(handler.continuum_uow, continuum.UnitOfWork)
        self.assertIsInstance(handler.continuum_txn, txncls)
        # nb. no comment
        self.assertIsNone(handler.continuum_txn.meta.get("comment"))

        # with comment
        handler = self.make_handler()
        handler.continuum_comment = "yeehaw"
        handler.begin_target_transaction()
        self.assertIn("comment", handler.continuum_txn.meta)
        self.assertEqual(handler.continuum_txn.meta["comment"], "yeehaw")

    def test_get_importer_kwargs(self):
        handler = self.make_handler()
        handler.begin_target_transaction()

        kw = handler.get_importer_kwargs("User")
        self.assertIn("continuum_txn", kw)
        self.assertIs(kw["continuum_txn"], handler.continuum_txn)

    def test_make_importer_factory(self):
        model = self.app.model
        handler = self.make_handler()

        # versioned class
        factory = handler.make_importer_factory(model.User, "User")
        self.assertTrue(issubclass(factory, mod.FromWuttaToVersionBase))
        self.assertIs(factory.source_model_class, model.User)
        self.assertIs(factory.model_class, continuum.version_class(model.User))

        # non-versioned
        factory = handler.make_importer_factory(model.Upgrade, "Upgrade")
        self.assertIsNone(factory)

    def test_define_importers(self):
        handler = self.make_handler()

        importers = handler.define_importers()
        self.assertIn("User", importers)
        self.assertIn("Person", importers)
        self.assertNotIn("Upgrade", importers)


class TestFromWuttaToVersionBase(VersionTestCase):

    def make_importer(self, model_class=None, **kwargs):
        imp = mod.FromWuttaToVersionBase(self.config, **kwargs)
        if model_class:
            imp.model_class = model_class
        return imp

    def test_get_simple_fields(self):
        model = self.app.model
        vercls = continuum.version_class(model.User)

        # first confirm what a "normal" importer would do
        imp = Importer(self.config, model_class=vercls)
        fields = imp.get_simple_fields()
        self.assertIn("username", fields)
        self.assertIn("person_uuid", fields)
        self.assertIn("transaction_id", fields)
        self.assertIn("operation_type", fields)
        self.assertIn("end_transaction_id", fields)

        # now test what the "version" importer does
        imp = self.make_importer(model_class=vercls)
        fields = imp.get_simple_fields()
        self.assertIn("username", fields)
        self.assertIn("person_uuid", fields)
        self.assertNotIn("transaction_id", fields)
        self.assertNotIn("operation_type", fields)
        self.assertNotIn("end_transaction_id", fields)

    def test_get_target_query(self):
        model = self.app.model
        vercls = continuum.version_class(model.User)
        imp = self.make_importer(model_class=vercls, target_session=self.session)

        # TODO: not sure what else to test here..
        query = imp.get_target_query()
        self.assertIsInstance(query, orm.Query)

    def test_normalize_target_object(self):
        model = self.app.model
        vercls = continuum.version_class(model.User)
        imp = self.make_importer(model_class=vercls)

        user = model.User(username="fred")
        self.session.add(user)
        self.session.commit()
        version = user.versions[0]

        # version object should be embedded in data dict
        data = imp.normalize_target_object(version)
        self.assertIsInstance(data, dict)
        self.assertIn("_objref", data)
        self.assertIs(data["_objref"], version)

        # but normal object is not embedded
        data = imp.normalize_target_object(user)
        self.assertIsInstance(data, dict)
        self.assertNotIn("_version", data)

    def test_make_version(self):
        model = self.app.model
        vercls = continuum.version_class(model.User)

        user = model.User(username="fred")
        self.session.add(user)
        self.session.commit()

        handler = mod.FromWuttaToVersions(self.config)
        handler.begin_target_transaction()
        handler.target_session.close()
        handler.target_session = self.session

        imp = self.make_importer(
            model_class=vercls,
            fields=["uuid", "username"],
            keys=("uuid",),
            target_session=self.session,
            continuum_txn=handler.continuum_txn,
        )

        data = {"uuid": user.uuid, "username": "freddie"}
        version = imp.make_version(data, continuum.Operation.UPDATE)
        self.assertIsInstance(version, vercls)
        self.assertEqual(version.uuid, user.uuid)
        self.assertEqual(version.username, "freddie")
        self.assertIn(version, self.session)
        self.assertIs(version.transaction, imp.continuum_txn)
        self.assertEqual(version.operation_type, continuum.Operation.UPDATE)

    def test_create_target_object(self):
        model = self.app.model
        vercls = continuum.version_class(model.User)

        handler = mod.FromWuttaToVersions(self.config)
        handler.begin_target_transaction()
        handler.target_session.close()
        handler.target_session = self.session

        imp = self.make_importer(
            model_class=vercls,
            fields=["uuid", "username"],
            keys=("uuid",),
            target_session=self.session,
            continuum_txn=handler.continuum_txn,
        )

        source_data = {"uuid": make_true_uuid(), "username": "bettie"}
        self.assertEqual(self.session.query(vercls).count(), 0)
        version = imp.create_target_object((source_data["uuid"], 1), source_data)
        self.assertEqual(self.session.query(vercls).count(), 1)
        self.assertEqual(version.transaction_id, imp.continuum_txn.id)
        self.assertEqual(version.operation_type, continuum.Operation.INSERT)
        self.assertIsNone(version.end_transaction_id)

    def test_update_target_object(self):
        model = self.app.model
        vercls = continuum.version_class(model.User)

        user = model.User(username="fred")
        self.session.add(user)
        self.session.commit()
        version1 = user.versions[0]

        handler = mod.FromWuttaToVersions(self.config)
        handler.begin_target_transaction()
        handler.target_session.close()
        handler.target_session = self.session

        imp = self.make_importer(
            model_class=vercls,
            fields=["uuid", "username"],
            keys=("uuid",),
            target_session=self.session,
            continuum_txn=handler.continuum_txn,
        )

        source_data = {"uuid": user.uuid, "username": "freddie"}
        target_data = imp.normalize_target_object(version1)
        self.assertEqual(self.session.query(vercls).count(), 1)
        self.assertIsNone(version1.end_transaction_id)
        version2 = imp.update_target_object(
            version1, source_data, target_data=target_data
        )
        self.assertEqual(self.session.query(vercls).count(), 2)
        self.assertEqual(version1.end_transaction_id, imp.continuum_txn.id)
        self.assertEqual(version2.transaction_id, imp.continuum_txn.id)
        self.assertEqual(version2.operation_type, continuum.Operation.UPDATE)
        self.assertIsNone(version2.end_transaction_id)

    def test_delete_target_object(self):
        model = self.app.model
        vercls = continuum.version_class(model.User)

        user = model.User(username="fred")
        self.session.add(user)
        self.session.commit()
        version1 = user.versions[0]

        handler = mod.FromWuttaToVersions(self.config)
        handler.begin_target_transaction()
        handler.target_session.close()
        handler.target_session = self.session

        imp = self.make_importer(
            model_class=vercls,
            fields=["uuid", "username"],
            keys=("uuid",),
            target_session=self.session,
            continuum_txn=handler.continuum_txn,
        )

        self.assertEqual(self.session.query(vercls).count(), 1)
        self.assertIsNone(version1.end_transaction_id)
        version2 = imp.delete_target_object(version1)
        self.assertEqual(self.session.query(vercls).count(), 2)
        self.assertEqual(version1.end_transaction_id, imp.continuum_txn.id)
        self.assertEqual(version2.transaction_id, imp.continuum_txn.id)
        self.assertEqual(version2.operation_type, continuum.Operation.DELETE)
        self.assertIsNone(version2.end_transaction_id)
