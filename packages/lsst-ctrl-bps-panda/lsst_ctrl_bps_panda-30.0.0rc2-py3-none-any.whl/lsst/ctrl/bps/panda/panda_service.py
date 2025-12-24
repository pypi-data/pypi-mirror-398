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
"""Interface between generic workflow to PanDA/iDDS workflow system."""

__all__ = ["PanDAService", "PandaBpsWmsWorkflow"]


import json
import logging
import os
import pickle
import re

from idds.workflowv2.workflow import Workflow as IDDS_client_workflow

from lsst.ctrl.bps import (
    DEFAULT_MEM_FMT,
    DEFAULT_MEM_UNIT,
    BaseWmsService,
    BaseWmsWorkflow,
    WmsRunReport,
    WmsStates,
)
from lsst.ctrl.bps.panda.constants import (
    PANDA_DEFAULT_MAX_COPY_WORKERS,
    PANDA_DEFAULT_MAX_REQUEST_LENGTH,
)
from lsst.ctrl.bps.panda.utils import (
    add_final_idds_work,
    add_idds_work,
    aggregate_by_basename,
    copy_files_for_distribution,
    create_idds_build_workflow,
    extract_taskname,
    get_idds_client,
    get_idds_result,
    idds_call_with_check,
)
from lsst.resources import ResourcePath
from lsst.utils.timer import time_this

_LOG = logging.getLogger(__name__)


class PanDAService(BaseWmsService):
    """PanDA version of WMS service."""

    def prepare(self, config, generic_workflow, out_prefix=None):
        # Docstring inherited from BaseWmsService.prepare.
        _LOG.debug("out_prefix = '%s'", out_prefix)

        _LOG.info("Starting PanDA prepare stage (creating specific implementation of workflow)")

        with time_this(
            log=_LOG,
            level=logging.INFO,
            prefix=None,
            msg="PanDA prepare stage completed",
            mem_usage=True,
            mem_unit=DEFAULT_MEM_UNIT,
            mem_fmt=DEFAULT_MEM_FMT,
        ):
            workflow = PandaBpsWmsWorkflow.from_generic_workflow(
                config, generic_workflow, out_prefix, f"{self.__class__.__module__}.{self.__class__.__name__}"
            )
            workflow.write(out_prefix)
        return workflow

    def submit(self, workflow, **kwargs):
        config = kwargs["config"] if "config" in kwargs else None
        remote_build = kwargs["remote_build"] if "remote_build" in kwargs else None

        if config and remote_build:
            _LOG.info("remote build")

            idds_build_workflow = create_idds_build_workflow(**kwargs)
            idds_client = get_idds_client(self.config)
            ret = idds_client.submit_build(idds_build_workflow, username=None, use_dataset_name=False)
            _LOG.debug("iDDS client manager submit returned = %s", ret)

            # Check submission success
            status, result, error = get_idds_result(ret)
            if status:
                request_id = int(result)
            else:
                raise RuntimeError(f"Error submitting to PanDA service: {error}")

            _LOG.info("Submitted into iDDs with request id=%s", request_id)
            idds_build_workflow.run_id = request_id
            return idds_build_workflow

        else:
            _, max_request_length = self.config.search(
                "maxRequestLength", opt={"default": PANDA_DEFAULT_MAX_REQUEST_LENGTH}
            )
            _, max_copy_workers = self.config.search(
                "maxCopyWorkers", opt={"default": PANDA_DEFAULT_MAX_COPY_WORKERS}
            )
            file_distribution_uri = self.config["fileDistributionEndPoint"]
            lsst_temp = "LSST_RUN_TEMP_SPACE"
            if lsst_temp in file_distribution_uri and lsst_temp not in os.environ:
                file_distribution_uri = self.config["fileDistributionEndPointDefault"]
            protocol_pattern = re.compile(r"^[a-zA-Z][a-zA-Z\d+\-.]*://")
            if not protocol_pattern.match(file_distribution_uri):
                file_distribution_uri = "file://" + file_distribution_uri

            idds_client = get_idds_client(self.config)
            submit_cmd = workflow.run_attrs.get("bps_iscustom", False)
            if not submit_cmd:
                copy_files_for_distribution(
                    workflow.files_to_pre_stage,
                    ResourcePath(file_distribution_uri, forceDirectory=True),
                    max_copy_workers,
                )

                idds_wf = workflow.idds_client_workflow
                workflow_steps = idds_wf.split_workflow_to_steps(
                    request_cache=self.config["submitPath"], max_request_length=max_request_length
                )
                for wf_step in workflow_steps:
                    ret_step = idds_client.submit(wf_step, username=None, use_dataset_name=False)
                    status, result_step, error = get_idds_result(ret_step)
                    if status and result_step == 0:
                        msg = f"iDDS client manager successfully uploaded workflow step: {wf_step.step_name}"
                        _LOG.info(msg)
                    else:
                        msg = (
                            f"iDDS client manager failed to submit workflow step {wf_step.step_name}: "
                            f"{ret_step}"
                        )
                        raise RuntimeError(msg)

            ret = idds_client.submit(workflow.idds_client_workflow, username=None, use_dataset_name=False)
            _LOG.debug("iDDS client manager submit returned = %s", ret)

            # Check submission success
            status, result, error = get_idds_result(ret)
            if status:
                request_id = int(result)
            else:
                raise RuntimeError(f"Error submitting to PanDA service: {error}")

            _LOG.info("Submitted into iDDs with request id=%s", request_id)
            workflow.run_id = request_id

    def restart(self, wms_workflow_id):
        # Docstring inherited from BaseWmsService.restart.
        idds_client = get_idds_client(self.config)
        ret = idds_client.retry(request_id=wms_workflow_id)
        _LOG.debug("Restart PanDA workflow returned = %s", ret)

        status, result, error = get_idds_result(ret)
        if status:
            _LOG.info("Restarting PanDA workflow %s", result)
            return wms_workflow_id, None, json.dumps(result)

        return None, None, f"Error retry PanDA workflow: {error}"

    def report(
        self,
        wms_workflow_id=None,
        user=None,
        hist=0,
        pass_thru=None,
        is_global=False,
        return_exit_codes=False,
    ):
        # Docstring inherited from BaseWmsService.report.
        message = ""
        run_reports = []

        if not wms_workflow_id:
            message = "Run summary not implemented yet, use 'bps report --id <workflow_id>' instead"
            return run_reports, message

        idds_client = get_idds_client(self.config)
        ret = idds_call_with_check(
            idds_client.get_requests,
            func_name="get workflow status",
            request_id=wms_workflow_id,
            with_detail=True,
        )

        tasks = ret[1][1]
        if not tasks:
            message = f"No records found for workflow id '{wms_workflow_id}'. Hint: double check the id"
            return run_reports, message

        # Create initial WmsRunReport
        head = tasks[0]
        wms_report = WmsRunReport(
            wms_id=str(head["request_id"]),
            operator=head["username"],
            project="",
            campaign="",
            payload="",
            run=head["name"],
            state=WmsStates.UNKNOWN,
            total_number_jobs=0,
            job_state_counts=dict.fromkeys(WmsStates, 0),
            job_summary={},
            run_summary="",
            exit_code_summary={},
        )

        # Define workflow status mapping
        workflow_status = head["status"]["attributes"]["_name_"]
        if workflow_status in ("Finished", "SubFinished"):
            wms_report.state = WmsStates.SUCCEEDED
        elif workflow_status in ("Failed", "Expired"):
            wms_report.state = WmsStates.FAILED
        elif workflow_status == "Cancelled":
            wms_report.state = WmsStates.DELETED
        elif workflow_status == "Suspended":
            wms_report.state = WmsStates.HELD
        else:
            wms_report.state = WmsStates.RUNNING

        # Define state mapping for job aggregation
        # The status of a task is taken from the first item of state_map.
        # The workflow is in status WmsStates.FAILED when:
        #      All tasks have failed.
        # SubFinished tasks has jobs in
        #      output_processed_files: Finished
        #      output_failed_files: Failed
        #      output_missing_files: Missing
        state_map = {
            "Finished": [WmsStates.SUCCEEDED],
            "SubFinished": [WmsStates.SUCCEEDED, WmsStates.FAILED, WmsStates.PRUNED],
            "Transforming": [
                WmsStates.RUNNING,
                WmsStates.SUCCEEDED,
                WmsStates.FAILED,
                # WmsStates.READY,
                WmsStates.UNREADY,
                WmsStates.PRUNED,
            ],
            "Failed": [WmsStates.FAILED, WmsStates.PRUNED],
        }

        file_map = {
            WmsStates.SUCCEEDED: "output_processed_files",
            WmsStates.RUNNING: "output_processing_files",
            WmsStates.FAILED: "output_failed_files",
            # WmsStates.READY: "output_activated_files",
            WmsStates.UNREADY: "input_new_files",
            WmsStates.PRUNED: "output_missing_files",
        }

        # Sort tasks by workload_id or fallback
        try:
            tasks.sort(key=lambda x: x["transform_workload_id"])
        except (KeyError, TypeError):
            tasks.sort(key=lambda x: x["transform_id"])

        exit_codes_all = {}

        # --- Process each task sequentially ---
        for task in tasks:
            if task.get("transform_id") is None:
                # Not created task (It happens because of an outer join
                # between requests table and transforms table).
                continue

            task_name = task.get("transform_name", "")
            tasklabel = extract_taskname(task_name)
            status = task["transform_status"]["attributes"]["_name_"]
            totaljobs = task.get("output_total_files", 0)
            wms_report.total_number_jobs += totaljobs

            # --- If task failed/subfinished, fetch exit codes ---
            if status in ("SubFinished", "Failed") and not task_name.startswith("build_task"):
                transform_workload_id = task.get("transform_workload_id")
                if transform_workload_id:
                    # When there are failed jobs, ctrl_bps check
                    # the number of exit codes
                    nfailed = task.get("output_failed_files", 0)
                    exit_codes_all[tasklabel] = [1] * nfailed
                    if return_exit_codes:
                        new_ret = idds_call_with_check(
                            idds_client.get_contents_output_ext,
                            func_name=f"get task {transform_workload_id} detail",
                            request_id=wms_workflow_id,
                            workload_id=transform_workload_id,
                        )
                        # task_info is a dictionary of len 1 that contains
                        # a list of dicts containing panda job info
                        task_info = new_ret[1][1]
                        if len(task_info) == 1:
                            _, wmsjobs = next(iter(task_info.items()))
                            exit_codes_all[tasklabel] = [
                                j["trans_exit_code"]
                                for j in wmsjobs
                                if j.get("trans_exit_code") not in (None, 0, "0")
                            ]
                            if nfailed > 0 and len(exit_codes_all[tasklabel]) == 0:
                                _LOG.debug(
                                    f"No exit codes in iDDS task info for workload {transform_workload_id}"
                                )
                        else:
                            raise RuntimeError(
                                f"Unexpected iDDS task info for workload {transform_workload_id}: {task_info}"
                            )

            # --- Aggregate job states ---
            taskstatus = {}
            mapped_states = state_map.get(status, [])
            for state in WmsStates:
                njobs = 0
                if state in mapped_states and state in file_map:
                    val = task.get(file_map[state])
                    if val:
                        njobs = val
                    if state == WmsStates.RUNNING:
                        njobs += task.get("output_new_files", 0) - task.get("input_new_files", 0)
                if state != WmsStates.UNREADY:
                    wms_report.job_state_counts[state] += njobs
                taskstatus[state] = njobs

            # Count UNREADY
            unready = WmsStates.UNREADY
            taskstatus[unready] = totaljobs - sum(
                taskstatus[state] for state in WmsStates if state != unready
            )
            wms_report.job_state_counts[unready] += taskstatus[unready]

            # Store task summary
            wms_report.job_summary[tasklabel] = taskstatus
            summary_part = f"{tasklabel}:{totaljobs}"
            if wms_report.run_summary:
                summary_part = f";{summary_part}"
            wms_report.run_summary += summary_part

        # Store all exit codes
        wms_report.exit_code_summary = exit_codes_all

        (
            wms_report.job_summary,
            wms_report.exit_code_summary,
            wms_report.run_summary,
        ) = aggregate_by_basename(
            wms_report.job_summary,
            wms_report.exit_code_summary,
            wms_report.run_summary,
        )

        run_reports.append(wms_report)
        return run_reports, message

    def list_submitted_jobs(self, wms_id=None, user=None, require_bps=True, pass_thru=None, is_global=False):
        # Docstring inherited from BaseWmsService.list_submitted_jobs.
        if wms_id is None and user is not None:
            raise RuntimeError(
                "Error to get workflow status report: wms_id is required"
                " and filtering workflows with 'user' is not supported."
            )

        idds_client = get_idds_client(self.config)
        ret = idds_client.get_requests(request_id=wms_id)
        _LOG.debug("PanDA get workflows returned = %s", ret)

        status, result, error = get_idds_result(ret)
        if status:
            req_ids = [req["request_id"] for req in result]
            return req_ids

        raise RuntimeError(f"Error list PanDA workflow requests: {error}")

    def cancel(self, wms_id, pass_thru=None):
        # Docstring inherited from BaseWmsService.cancel.
        idds_client = get_idds_client(self.config)
        ret = idds_client.abort(request_id=wms_id)
        _LOG.debug("Abort PanDA workflow returned = %s", ret)

        status, result, error = get_idds_result(ret)
        if status:
            _LOG.info("Aborting PanDA workflow %s", result)
            return True, json.dumps(result)

        return False, f"Error abort PanDA workflow: {error}"

    def ping(self, pass_thru=None):
        # Docstring inherited from BaseWmsService.ping.
        idds_client = get_idds_client(self.config)
        ret = idds_client.ping()
        _LOG.debug("Ping PanDA service returned = %s", ret)

        status, result, error = get_idds_result(ret)
        if status:
            if "Status" in result and result["Status"] == "OK":
                return 0, None

            return -1, f"Error ping PanDA service: {result}"

        return -1, f"Error ping PanDA service: {error}"

    def run_submission_checks(self):
        # Docstring inherited from BaseWmsService.run_submission_checks.
        for key in ["PANDA_URL"]:
            if key not in os.environ:
                raise OSError(f"Missing environment variable {key}")

        status, message = self.ping()
        if status != 0:
            raise RuntimeError(message)

    def get_status(
        self,
        wms_workflow_id=None,
        hist=0,
        is_global=False,
    ):
        # Docstring inherited from BaseWmsService.get_status.

        idds_client = get_idds_client(self.config)
        ret = idds_client.get_requests(request_id=wms_workflow_id, with_detail=False)
        _LOG.debug("PanDA get workflow status returned = %s", str(ret))

        request_status = ret[0]
        if request_status != 0:
            state = WmsStates.UNKNOWN
            message = f"Error getting workflow status for id {wms_workflow_id}: ret = {ret}"
        else:
            tasks = ret[1][1]
            if not tasks:
                state = WmsStates.UNKNOWN
                message = f"No records found for workflow id '{wms_workflow_id}'. Hint: double check the id"
            elif not isinstance(tasks[0], dict):
                state = WmsStates.UNKNOWN
                message = f"Error getting workflow status for id {wms_workflow_id}: ret = {ret}"
            else:
                message = ""
                head = tasks[0]
                workflow_status = head["status"]["attributes"]["_name_"]
                if workflow_status in ["Finished"]:
                    state = WmsStates.SUCCEEDED
                elif workflow_status in ["Failed", "Expired", "SubFinished"]:
                    state = WmsStates.FAILED
                elif workflow_status in ["Cancelled"]:
                    state = WmsStates.DELETED
                elif workflow_status in ["Suspended"]:
                    state = WmsStates.HELD
                else:
                    state = WmsStates.RUNNING

        return state, message


class PandaBpsWmsWorkflow(BaseWmsWorkflow):
    """A single Panda based workflow.

    Parameters
    ----------
    name : `str`
        Unique name for Workflow.
    config : `lsst.ctrl.bps.BpsConfig`
        BPS configuration that includes necessary submit/runtime information.
    """

    def __init__(self, name, config=None):
        super().__init__(name, config)
        self.files_to_pre_stage = {}  # src, dest
        self.idds_client_workflow = IDDS_client_workflow(name=name)
        self.run_attrs = {}

    @classmethod
    def from_generic_workflow(cls, config, generic_workflow, out_prefix, service_class):
        # Docstring inherited from BaseWmsWorkflow.from_generic_workflow.
        wms_workflow = cls(generic_workflow.name, config)

        if generic_workflow.run_attrs:
            wms_workflow.run_attrs.update(generic_workflow.run_attrs)

        files, dag_sink_work, task_count = add_idds_work(
            config, generic_workflow, wms_workflow.idds_client_workflow
        )
        wms_workflow.files_to_pre_stage.update(files)

        files = add_final_idds_work(
            config, generic_workflow, wms_workflow.idds_client_workflow, dag_sink_work, task_count + 1, 1
        )
        wms_workflow.files_to_pre_stage.update(files)

        return wms_workflow

    def write(self, out_prefix):
        # Docstring inherited from BaseWmsWorkflow.write.
        with open(os.path.join(out_prefix, "panda_workflow.pickle"), "wb") as fh:
            pickle.dump(self, fh)
