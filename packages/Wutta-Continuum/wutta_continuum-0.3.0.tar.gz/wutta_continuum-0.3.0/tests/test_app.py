# -*- coding: utf-8; -*-

from wuttjamaican.testing import DataTestCase

from wutta_continuum import app as mod


class TestWuttaContinuumAppProvider(DataTestCase):

    def make_provider(self):
        return mod.WuttaContinuumAppProvider(self.config)

    def test_continuum_is_enabled(self):

        # off by default
        provider = self.make_provider()
        self.assertFalse(provider.continuum_is_enabled())

        # but can be turned on
        self.config.setdefault("wutta_continuum.enable_versioning", "true")
        self.assertTrue(provider.continuum_is_enabled())
