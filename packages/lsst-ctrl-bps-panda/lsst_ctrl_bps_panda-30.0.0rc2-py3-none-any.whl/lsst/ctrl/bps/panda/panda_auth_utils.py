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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Functions for each panda_auth subcommand."""

__all__ = [
    "panda_auth_clean",
    "panda_auth_expiration",
    "panda_auth_refresh",
    "panda_auth_setup",
    "panda_auth_status",
    "panda_auth_update",
]


import base64
import json
import logging
import os
from datetime import UTC, datetime, timedelta

import idds.common.utils as idds_utils
import pandaclient.idds_api
from pandaclient.openidc_utils import OpenIdConnect_Utils

from lsst.ctrl.bps.panda.panda_exceptions import (
    AuthConfigError,
    PandaAuthError,
    TokenExpiredError,
    TokenNotFoundError,
    TokenRefreshError,
    TokenTooEarlyError,
)

_LOG = logging.getLogger(__name__)


def panda_auth_clean():
    """Clean up token and token cache files."""
    open_id = panda_auth_setup()
    open_id.cleanup()


def panda_auth_expiration():
    """Get number of seconds until token expires.

    Returns
    -------
    expiration : `int`
        Number of seconds until token expires.
    """
    expiration = 0
    ret = panda_auth_status()
    if ret:
        expiration = ret[-1]["exp"]
    return expiration


def panda_auth_setup():
    """Initialize auth object used by various auth functions.

    Returns
    -------
    open_id : `pandaclient.openidc_utils.OpenIdConnect_Utils`
        Auth object which can interact with auth token.
    """
    for key in [
        "PANDA_AUTH",
        "PANDA_VERIFY_HOST",
        "PANDA_AUTH_VO",
        "PANDA_URL_SSL",
        "PANDA_URL",
    ]:
        if key not in os.environ:
            raise OSError(f"Missing environment variable {key}")

    # OpenIdConnect_Utils have a verbose flag that filters
    # some debugging messages.  If user chose debug, just
    # turn on all of the messages.
    verbose = False
    if _LOG.isEnabledFor(logging.DEBUG):
        verbose = True

    open_id = OpenIdConnect_Utils(None, log_stream=_LOG, verbose=verbose)
    return open_id


def panda_auth_status():
    """Gather information about a token if it exists.

    Returns
    -------
    status : `dict`
        Status information about a token if it exists.
        Includes filename and expiration epoch.
    """
    status = None
    open_id = panda_auth_setup()
    ret = open_id.check_token()
    if ret and ret[0]:
        # get_token_path will return the path even if a token doesn't
        # currently exist.  So check for token first via check_token, then
        # add path.
        status = {"filename": open_id.get_token_path()}
        status.update(ret[-1])
    return status


def panda_auth_update(idds_server=None, reset=False):
    """Get new auth token if needed or reset is True.

    Parameters
    ----------
    idds_server : `str`, optional
        URL for the iDDS server.  Defaults to None which means that the
        underlying functions use any value in the panda relay service.
    reset : `bool`, optional
        Whether to first clean up any previous token.  Defaults to False.
    """
    if reset:
        panda_auth_clean()

    # Create client manager
    # (There is a function in OpenIdConnect_Utils, but it takes several
    #  parameters.  Letting the client manager do it is currently easiest
    #  way to match what happens when the workflow is actually submitted.)
    cm = pandaclient.idds_api.get_api(
        idds_utils.json_dumps, idds_host=idds_server, compress=True, manager=True, verbose=False
    )

    # Must call some function to actually check auth
    # https://panda-wms.readthedocs.io/en/latest/client/notebooks/jupyter_setup.html#Get-an-OIDC-ID-token
    ret = cm.get_status(request_id=0, with_detail=False)
    _LOG.debug("get_status results: %s", ret)

    # Check success
    # https://panda-wms.readthedocs.io/en/latest/client/rest_idds.html
    if ret[0] == 0 and ret[1][0]:
        # The success keys from get_status currently do not catch if invalid
        # idds server given.  So for now, check result string for keywords.
        if "request_id" not in ret[1][-1] or "status" not in ret[1][-1]:
            raise RuntimeError(f"Error contacting PanDA service: {ret}")


def panda_auth_refresh(days=4, verbose=False):
    """
    Refresh the current valid IAM OpenID authentication token.

    This function checks the expiration time of the existing token stored
    in the local token file and attempts to refresh it if it is close to
    expiring (within a specified number of days).

    Parameters
    ----------
    days : `int`, optional
        The minimum number of days before token expiration to trigger a
        refresh. If the token expires in more than this number of days,
        the refresh is skipped. Default is 4.
    verbose : `bool`, optional
        If True, enables verbose output for debugging or logging.
        Default is False.

    Returns
    -------
    status: `dict`
        A dictionary containing the refreshed token status
    """
    panda_url = os.environ.get("PANDA_URL")
    panda_auth_vo = os.environ.get("PANDA_AUTH_VO")

    if not panda_url or not panda_auth_vo:
        raise PandaAuthError("Missing required environment variables: PANDA_URL or PANDA_AUTH_VO")

    url_prefix = panda_url.split("/server", 1)[0]
    auth_url = f"{url_prefix}/auth/{panda_auth_vo}_auth_config.json"
    open_id = OpenIdConnect_Utils(auth_url, log_stream=_LOG, verbose=verbose)

    token_file = open_id.get_token_path()
    if not os.path.exists(token_file):
        raise TokenNotFoundError("Cannot find token file. Use 'panda_auth reset' to obtain a new token.")

    with open(token_file) as f:
        data = json.load(f)
    enc = data["id_token"].split(".")[1]
    enc += "=" * (-len(enc) % 4)
    dec = json.loads(base64.urlsafe_b64decode(enc.encode()))
    exp_time = datetime.fromtimestamp(dec["exp"], tz=UTC)
    delta = exp_time - datetime.now(UTC)
    minutes = delta.total_seconds() / 60
    print(f"Token will expire in {minutes} minutes.")
    print(f"Token expiration time : {exp_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    if delta < timedelta(minutes=0):
        raise TokenExpiredError("Token already expired. Cannot refresh.")
    elif delta > timedelta(days=days):
        raise TokenTooEarlyError(
            f"Too early to refresh. More than {days} day(s) until expiration.\n"
            f"Use '--days' option to adjust threshold, e.g.:\n"
            f"  panda_auth refresh --days 10"
        )

    refresh_token_string = data["refresh_token"]

    s, auth_config = open_id.fetch_page(open_id.auth_config_url)
    if not s:
        raise AuthConfigError("Failed to get Auth configuration.")

    s, endpoint_config = open_id.fetch_page(auth_config["oidc_config_url"])
    if not s:
        raise AuthConfigError("Failed to get endpoint configuration.")

    s, o = open_id.refresh_token(
        endpoint_config["token_endpoint"],
        auth_config["client_id"],
        auth_config["client_secret"],
        refresh_token_string,
    )

    if not s:
        raise TokenRefreshError("Failed to refresh token.")

    status = panda_auth_status()
    if status:
        exp_time = datetime.fromtimestamp(status["exp"], tz=UTC)
        print(f"{'New expiration time:':23} {exp_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("Success to refresh token")
    return status
