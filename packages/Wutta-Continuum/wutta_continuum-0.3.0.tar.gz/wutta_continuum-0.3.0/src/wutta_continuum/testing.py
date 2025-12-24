# -*- coding: utf-8; -*-
################################################################################
#
#  Wutta-Continuum -- SQLAlchemy Versioning for Wutta Framework
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
Testing utilities
"""

import sys

import sqlalchemy_continuum as continuum

from wuttjamaican.testing import DataTestCase

from wutta_continuum.conf import WuttaContinuumConfigExtension


class VersionTestCase(DataTestCase):
    """
    Base class for test suites requiring the SQLAlchemy-Continuum
    versioning feature.

    This inherits from
    :class:`~wuttjamaican:wuttjamaican.testing.DataTestCase`.
    """

    def setUp(self):
        self.setup_versioning()

    def setup_versioning(self):
        """
        Do setup tasks relating to this class, as well as its parent(s):

        * call :meth:`wuttjamaican:wuttjamaican.testing.DataTestCase.setup_db()`

          * this will in turn call :meth:`make_config()`
        """
        self.setup_db()

    def tearDown(self):
        self.teardown_versioning()

    def teardown_versioning(self):
        """
        Do teardown tasks relating to this class, as well as its parent(s):

        * call :func:`sqlalchemy-continuum:sqlalchemy_continuum.remove_versioning()`
        * call :meth:`wuttjamaican:wuttjamaican.testing.DataTestCase.teardown_db()`
        """
        continuum.remove_versioning()
        continuum.versioning_manager.transaction_cls = continuum.TransactionFactory()
        self.teardown_db()

    def make_config(self, **kwargs):
        """
        Make and customize the config object.

        We override this to explicitly enable the versioning feature.
        """
        config = super().make_config(**kwargs)
        config.setdefault("wutta_continuum.enable_versioning", "true")

        # nb. must purge model classes from sys.modules, so they will
        # be reloaded and sqlalchemy-continuum can reconfigure
        if "wuttjamaican.db.model" in sys.modules:
            del sys.modules["wuttjamaican.db.model.batch"]
            del sys.modules["wuttjamaican.db.model.upgrades"]
            del sys.modules["wuttjamaican.db.model.auth"]
            del sys.modules["wuttjamaican.db.model.base"]
            del sys.modules["wuttjamaican.db.model"]

        ext = WuttaContinuumConfigExtension()
        ext.startup(config)
        return config
