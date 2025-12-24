# -*- coding: utf-8; -*-

from unittest import TestCase

import sqlalchemy_continuum as continuum

from wutta_continuum import util as mod
from wutta_continuum.testing import VersionTestCase


class TestRenderOperationType(TestCase):

    def test_basic(self):
        self.assertEqual(
            mod.render_operation_type(continuum.Operation.INSERT), "INSERT"
        )
        self.assertEqual(
            mod.render_operation_type(continuum.Operation.UPDATE), "UPDATE"
        )
        self.assertEqual(
            mod.render_operation_type(continuum.Operation.DELETE), "DELETE"
        )


class TestModelTransactionQuery(VersionTestCase):

    def test_basic(self):
        model = self.app.model

        user = model.User(username="fred")
        self.session.add(user)
        self.session.commit()

        query = mod.model_transaction_query(user)
        self.assertEqual(query.count(), 1)
        txn = query.one()

        UserVersion = continuum.version_class(model.User)
        version = self.session.query(UserVersion).one()
        self.assertIs(version.transaction, txn)
