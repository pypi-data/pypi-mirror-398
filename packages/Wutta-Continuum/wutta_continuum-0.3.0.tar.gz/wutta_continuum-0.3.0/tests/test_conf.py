# -*- coding: utf-8; -*-

import socket

from unittest.mock import patch, Mock

from wuttjamaican.testing import ConfigTestCase, DataTestCase

from wutta_continuum import conf as mod


class TestWuttaContinuumConfigExtension(ConfigTestCase):

    def make_extension(self):
        return mod.WuttaContinuumConfigExtension()

    def test_startup_without_versioning(self):
        ext = self.make_extension()
        with patch.object(mod, "make_versioned") as make_versioned:
            with patch.object(mod, "configure_mappers") as configure_mappers:
                ext.startup(self.config)
                make_versioned.assert_not_called()
                configure_mappers.assert_not_called()

    def test_startup_with_versioning(self):
        ext = self.make_extension()
        with patch.object(mod, "make_versioned") as make_versioned:
            with patch.object(mod, "configure_mappers") as configure_mappers:
                self.config.setdefault("wutta_continuum.enable_versioning", "true")
                ext.startup(self.config)
                make_versioned.assert_called_once()
                configure_mappers.assert_called_once_with()

    def test_startup_with_error(self):
        ext = self.make_extension()
        with patch.object(mod, "make_versioned") as make_versioned:
            with patch.object(mod, "configure_mappers") as configure_mappers:
                self.config.setdefault("wutta_continuum.enable_versioning", "true")
                # nb. it is an error for the model to be loaded prior to
                # calling make_versioned() for sqlalchemy-continuum
                self.app.get_model()
                self.assertRaises(RuntimeError, ext.startup, self.config)
                make_versioned.assert_not_called()
                configure_mappers.assert_not_called()


class TestWuttaContinuumPlugin(DataTestCase):

    def make_plugin(self):
        return mod.WuttaContinuumPlugin()

    def test_remote_addr(self):
        plugin = self.make_plugin()
        with patch.object(socket, "gethostbyname", return_value="127.0.0.1"):
            self.assertEqual(plugin.get_remote_addr(None, self.session), "127.0.0.1")

    def test_user_id(self):
        plugin = self.make_plugin()
        self.assertIsNone(plugin.get_user_id(None, self.session))

    def test_transaction_args(self):
        plugin = self.make_plugin()
        with patch.object(socket, "gethostbyname", return_value="127.0.0.1"):
            self.assertEqual(
                plugin.transaction_args(None, self.session),
                {"remote_addr": "127.0.0.1"},
            )

            with patch.object(plugin, "get_user_id", return_value="some-random-uuid"):
                self.assertEqual(
                    plugin.transaction_args(None, self.session),
                    {"remote_addr": "127.0.0.1", "user_id": "some-random-uuid"},
                )

    def test_before_flush(self):
        plugin = self.make_plugin()

        meta = {}
        txn = Mock(meta=meta)
        uow = Mock(current_transaction=txn)

        # no comment in session or transaction
        plugin.before_flush(uow, self.session)
        self.assertNotIn("comment", meta)

        # transaction comment matches session
        self.session.info["continuum_comment"] = "whaddyaknow"
        plugin.before_flush(uow, self.session)
        self.assertIn("comment", meta)
        self.assertEqual(meta["comment"], "whaddyaknow")
