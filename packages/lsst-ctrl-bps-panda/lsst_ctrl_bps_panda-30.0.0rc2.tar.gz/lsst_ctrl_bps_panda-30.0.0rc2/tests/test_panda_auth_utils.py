# This file is part of ctrl_bps_panda.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This software is dual licensed under the GNU General Public License and also
# under a 3-clause BSD license. Recipients may choose which of these licenses
# to use; please see the files gpl-3.0.txt and/or bsd_license.txt,
# respectively.  If you choose the GPL option then the following text applies
# (but note that there is still no warranty even if you opt for BSD instead):
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Unit tests for PanDA authentication utilities."""

import base64
import json
import os
import unittest
from datetime import UTC, datetime, timedelta
from unittest import mock

from lsst.ctrl.bps.panda import __version__ as version
from lsst.ctrl.bps.panda.panda_auth_utils import (
    TokenExpiredError,
    panda_auth_refresh,
    panda_auth_status,
)


def make_fake_jwt(exp_offset_days):
    """Return a fake id_token that expires in N days."""
    payload = {"exp": int((datetime.now(UTC) + timedelta(days=exp_offset_days)).timestamp())}
    b64_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"header.{b64_payload}.sig"


def fake_token_file(exp_days=3, refresh_token="fake_refresh"):
    """Generate fake token file data"""
    token = make_fake_jwt(exp_days)
    return json.dumps({"id_token": token, "refresh_token": refresh_token})


def fetch_page_side_effect(url):
    """Simulate OpenIdConnect_Utils.fetch_page behavior in tests."""
    if url.endswith("auth_config.json"):
        return True, {
            "client_secret": "secret",
            "audience": "https://iam.example.com",
            "client_id": "cid",
            "oidc_config_url": "https://oidc.example.org/.well-known/openid-configuration",
            "vo": "fake_vo",
            "no_verify": "True",
            "robot_ids": "NONE",
        }
    elif url.endswith("openid-configuration"):
        return True, {"token_endpoint": "https://oidc.example.org/token"}
    return False, {}


class VersionTestCase(unittest.TestCase):
    """Test versioning."""

    def test_version(self):
        # Check that version is defined.
        self.assertIsNotNone(version)


class TestPandaAuthUtils(unittest.TestCase):
    """Simple test of auth utilities."""

    def setUp(self):
        self.test_env = {
            "PANDA_CONFIG_ROOT": "/fake/token",
            "PANDA_URL_SSL": "https://fake.server.com:8443/server/panda",
            "PANDA_URL": "https://fake.server.com:8443/server/panda",
            "PANDACACHE_URL": "https://fake.server.com:8443/server/panda",
            "PANDAMON_URL": "https://fake.monitor.com:8443/",
            "PANDA_AUTH": "oidc",
            "PANDA_VERIFY_HOST": "off",
            "PANDA_AUTH_VO": "fake_vo",
            "PANDA_BEHIND_REAL_LB": "true",
            "PANDA_SYS": "/fake/pandasys",
            "IDDS_CONFIG": "/fake/pandasys/etc/idds/idds.cfg.client.template",
        }

    def testPandaAuthStatusWrongEnviron(self):
        unwanted = {
            "PANDA_AUTH",
            "PANDA_VERIFY_HOST",
            "PANDA_AUTH_VO",
            "PANDA_URL_SSL",
            "PANDA_URL",
        }
        test_environ = {key: val for key, val in os.environ.items() if key not in unwanted}
        with mock.patch.dict(os.environ, test_environ, clear=True):
            with self.assertRaises(OSError):
                panda_auth_status()

    @mock.patch("builtins.print")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("pandaclient.openidc_utils.OpenIdConnect_Utils")
    def test_expired_token(self, mock_oidc, mock_exists, mock_print):
        mock_oidc.return_value.get_token_path.return_value = "/fake/token.json"

        with mock.patch.dict("os.environ", self.test_env):
            with mock.patch("builtins.open", mock.mock_open(read_data=fake_token_file(exp_days=-1))):
                with self.assertRaises(TokenExpiredError):
                    panda_auth_refresh(days=4)

    @mock.patch("builtins.print")
    @mock.patch("lsst.ctrl.bps.panda.panda_auth_utils.panda_auth_status")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("lsst.ctrl.bps.panda.panda_auth_utils.OpenIdConnect_Utils")
    def test_successful_refresh(self, mock_oidc, mock_exists, mock_status, mock_print):
        fake_openid = mock_oidc.return_value
        fake_openid.get_token_path.return_value = "/fake/token.json"
        fake_openid.auth_config_url = "https://fake.server/auth_config.json"

        fake_openid.fetch_page.side_effect = fetch_page_side_effect

        fake_openid.refresh_token.return_value = (True, {"access_token": "new_token"})

        mock_status.return_value = {"exp": int((datetime.now(UTC) + timedelta(seconds=3600)).timestamp())}

        with mock.patch.dict("os.environ", self.test_env):
            token_json = fake_token_file(exp_days=2)
            with mock.patch("builtins.open", mock.mock_open(read_data=token_json)):
                panda_auth_refresh(days=4)

        fake_openid.refresh_token.assert_called_once()
        found = any("Success to refresh token" in str(c[0][0]) for c in mock_print.call_args_list)
        assert found


if __name__ == "__main__":
    unittest.main()
