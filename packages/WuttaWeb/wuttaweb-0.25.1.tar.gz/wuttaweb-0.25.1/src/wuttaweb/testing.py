# -*- coding: utf-8; -*-
################################################################################
#
#  wuttaweb -- Web App for Wutta Framework
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
WuttaWeb - test utilities
"""

import sys
from unittest.mock import MagicMock

import fanstatic
import pytest
from pyramid import testing

from wuttjamaican.testing import DataTestCase
from wuttjamaican.db.model.base import metadata

from wuttaweb import subscribers
from wuttaweb.conf import WuttaWebConfigExtension


class WebTestCase(DataTestCase):
    """
    Base class for test suites requiring a full (typical) web app.
    """

    def setUp(self):  # pylint: disable=empty-docstring
        """ """
        self.setup_web()

    def setup_web(self):
        """
        Perform setup for the testing web app.
        """
        self.setup_db()
        self.request = self.make_request()
        self.pyramid_config = testing.setUp(
            request=self.request,
            settings={
                "wutta_config": self.config,
                "mako.directories": ["wuttaweb:templates"],
                "pyramid_deform.template_search_path": "wuttaweb:templates/deform",
            },
        )

        # init web
        self.pyramid_config.include("pyramid_deform")
        self.pyramid_config.include("pyramid_mako")
        self.pyramid_config.add_directive(
            "add_wutta_permission_group", "wuttaweb.auth.add_permission_group"
        )
        self.pyramid_config.add_directive(
            "add_wutta_permission", "wuttaweb.auth.add_permission"
        )
        self.pyramid_config.add_subscriber(
            "wuttaweb.subscribers.before_render", "pyramid.events.BeforeRender"
        )
        self.pyramid_config.include("wuttaweb.static")

        # nb. mock out fanstatic env..good enough for now to avoid errors..
        needed = fanstatic.init_needed()
        self.request.environ[fanstatic.NEEDED] = needed

        # setup new request w/ anonymous user
        event = MagicMock(request=self.request)
        subscribers.new_request(event)

        def user_getter(request, **kwargs):  # pylint: disable=unused-argument
            pass

        subscribers.new_request_set_user(
            event, db_session=self.session, user_getter=user_getter
        )

    def tearDown(self):
        self.teardown_web()

    def teardown_web(self):
        """
        Perform teardown for the testing web app.
        """
        testing.tearDown()
        self.teardown_db()

    def make_request(self):
        """
        Make and return a new dummy request object.
        """
        return testing.DummyRequest(client_addr="127.0.0.1")


@pytest.mark.versioned
class VersionWebTestCase(WebTestCase):
    """
    Base class for test suites requiring a full (typical) web app,
    with Continuum versioning support.
    """

    def setUp(self):
        self.setup_versioning()

    def setup_versioning(self):
        """
        Perform setup for the testing web app.
        """
        self.setup_web()

    def tearDown(self):
        self.teardown_versioning()

    def teardown_versioning(self):
        """
        Perform teardown for the testing web app.
        """
        import sqlalchemy_continuum as continuum  # pylint: disable=import-outside-toplevel

        continuum.remove_versioning()
        continuum.versioning_manager.transaction_cls = continuum.TransactionFactory()
        self.teardown_web()

    def make_config(self, **kwargs):
        """
        Make and customize the config object.

        We override this to explicitly enable the versioning feature.
        """
        from wutta_continuum.conf import (  # pylint: disable=import-outside-toplevel
            WuttaContinuumConfigExtension,
        )

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

        self.assertNotIn("user_version", metadata.tables)

        ext = WuttaWebConfigExtension()
        ext.configure(config)

        ext = WuttaContinuumConfigExtension()
        ext.startup(config)

        return config
