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

"""Unit tests for ctrl_bps_panda panda_service module."""

import logging
import unittest

from idds.common.constants import WorkStatus

from lsst.ctrl.bps import BpsConfig, WmsStates
from lsst.ctrl.bps.panda import panda_service

_LOG = logging.getLogger(__name__)


class MockClient:
    """Mock idds client."""

    def __init__(self):
        _LOG.debug("Called mock client init")

    def get_requests(self, request_id, with_detail):
        _LOG.debug("Called mock client get_requests with %s", request_id)
        status = None
        match request_id:
            case "1000":  # GetRequestsFailure
                requests = (1, "PanDA error message")
            case "1001":
                status = WorkStatus.Finished
            case "1002":
                status = WorkStatus.SubFinished
            case "1003":
                status = WorkStatus.Failed
            case "1004":
                status = WorkStatus.Cancelled
            case "1005":
                status = WorkStatus.Suspended
            case "1006":
                status = WorkStatus.Running
            case "1007":
                status = WorkStatus.Transforming
            case "1008":
                requests = (0, [True, [False, "An unknown IDDS exception occurred."]])
            case _:  # Unknown ID
                requests = (0, [True, []])

        if status:
            workflow_name = "FAKE_WORKFLOW_NAME_20250515T213417Z"
            requests = (
                0,
                [
                    True,
                    [
                        {
                            "name": workflow_name,
                            "request_id": request_id,
                            "status": {
                                "attributes": {
                                    "_value_": status.value,
                                    "_name_": status.name,
                                    "_sort_order_": status.value,
                                }
                            },
                        }
                    ],
                ],
            )

        return requests


class TestPanDAService(unittest.TestCase):
    """Test PanDAService class methods."""

    def setUp(self):
        config = BpsConfig({}, wms_service_class_fqn="lsst.ctrl.bps.panda.PanDAService")
        self.service = panda_service.PanDAService(config)

    @unittest.mock.patch("lsst.ctrl.bps.panda.panda_service.get_idds_client")
    def testGetStatusGetRequestsFailure(self, mock_get):
        mock_get.return_value = MockClient()
        status, message = self.service.get_status("1000")

        self.assertEqual(status, WmsStates.UNKNOWN)
        self.assertEqual(
            message, "Error getting workflow status for id 1000: ret = (1, 'PanDA error message')"
        )

    @unittest.mock.patch("lsst.ctrl.bps.panda.panda_service.get_idds_client")
    def testGetStatusUnknownID(self, mock_get):
        mock_get.return_value = MockClient()
        status, message = self.service.get_status("9999")

        self.assertEqual(status, WmsStates.UNKNOWN)
        self.assertEqual(message, "No records found for workflow id '9999'. Hint: double check the id")

    @unittest.mock.patch("lsst.ctrl.bps.panda.panda_service.get_idds_client")
    def testGetStatusFinished(self, mock_get):
        mock_get.return_value = MockClient()
        status, message = self.service.get_status("1001")

        self.assertEqual(status, WmsStates.SUCCEEDED)
        self.assertEqual(message, "")

    @unittest.mock.patch("lsst.ctrl.bps.panda.panda_service.get_idds_client")
    def testGetStatusSubFinished(self, mock_get):
        mock_get.return_value = MockClient()
        status, message = self.service.get_status("1002")

        self.assertEqual(status, WmsStates.FAILED)
        self.assertEqual(message, "")

    @unittest.mock.patch("lsst.ctrl.bps.panda.panda_service.get_idds_client")
    def testGetStatusFailed(self, mock_get):
        mock_get.return_value = MockClient()
        status, message = self.service.get_status("1003")

        self.assertEqual(status, WmsStates.FAILED)
        self.assertEqual(message, "")

    @unittest.mock.patch("lsst.ctrl.bps.panda.panda_service.get_idds_client")
    def testGetStatusCancelled(self, mock_get):
        mock_get.return_value = MockClient()
        status, message = self.service.get_status("1004")

        self.assertEqual(status, WmsStates.DELETED)
        self.assertEqual(message, "")

    @unittest.mock.patch("lsst.ctrl.bps.panda.panda_service.get_idds_client")
    def testGetStatusSuspended(self, mock_get):
        mock_get.return_value = MockClient()
        status, message = self.service.get_status("1005")

        self.assertEqual(status, WmsStates.HELD)
        self.assertEqual(message, "")

    @unittest.mock.patch("lsst.ctrl.bps.panda.panda_service.get_idds_client")
    def testGetStatusRunning(self, mock_get):
        mock_get.return_value = MockClient()
        status, message = self.service.get_status("1006")

        self.assertEqual(status, WmsStates.RUNNING)
        self.assertEqual(message, "")

    @unittest.mock.patch("lsst.ctrl.bps.panda.panda_service.get_idds_client")
    def testGetStatusTransforming(self, mock_get):
        mock_get.return_value = MockClient()
        status, message = self.service.get_status("1007")

        self.assertEqual(status, WmsStates.RUNNING)
        self.assertEqual(message, "")

    @unittest.mock.patch("lsst.ctrl.bps.panda.panda_service.get_idds_client")
    def testGetStatusUnknownIDDSException(self, mock_get):
        # Test example unknown IDDS exception similar to what occurs
        # if give path to ctrl_bps_panda's get_status.
        mock_get.return_value = MockClient()
        status, message = self.service.get_status("1008")

        self.assertEqual(status, WmsStates.UNKNOWN)
        self.assertEqual(
            message,
            "Error getting workflow status for id 1008: ret = "
            "(0, [True, [False, 'An unknown IDDS exception occurred.']])",
        )


if __name__ == "__main__":
    unittest.main()
