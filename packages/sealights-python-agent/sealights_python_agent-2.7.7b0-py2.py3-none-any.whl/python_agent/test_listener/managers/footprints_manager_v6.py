import logging
import threading
import time
import uuid

from python_agent.common import constants
from python_agent.common.config_data import ConfigData
from python_agent.common.schduler.scheduler import SchedulerManager
from python_agent.test_listener.entities.build_mapper import BuildMapper
from python_agent.test_listener.managers.code_coverage_manager_v6 import (
    CodeCoverageManager,
)
from python_agent.test_listener.services.footprints_service_v6 import FootprintsService

log = logging.getLogger(__name__)


class FootprintsManager(object):
    def __init__(self, config_data: ConfigData, backend_proxy, agent_events_manager):
        self.config_data = config_data
        self.backend_proxy = backend_proxy
        self.build_mapping: BuildMapper = BuildMapper(
            config_data
        ).scan_files_and_calculate_metrics()
        self.footprints_service = FootprintsService(self.config_data, backend_proxy)
        self.code_coverage_manager = CodeCoverageManager(config_data)
        self.auto_execution = config_data.auto_execution
        self.send_footprints_interval = config_data.intervalSeconds
        self.check_active_execution_interval = (
            constants.ACTIVE_EXECUTION_INTERVAL_IN_MILLISECONDS / 1000
        )
        self._add_coverage_interval = 1
        self.scheduler_manager = SchedulerManager()
        self.scheduler_manager.add_job(
            self.send_footprints_task, self.send_footprints_interval
        )
        self.scheduler_manager.add_job(
            self.add_coverage_task, self._add_coverage_interval
        )
        if not self.auto_execution:
            self.scheduler_manager.add_job(
                self.get_active_execution, self.check_active_execution_interval
            )
            log.debug(
                "Anonymous execution is enabled, will check for active execution every %d seconds"
                % (int(self.check_active_execution_interval))
            )
        else:
            log.debug(
                "Anonymous execution is disabled, will open and close execution manually"
            )
        self._agent_events_manager = agent_events_manager
        self._current_execution = None
        self._add_coverage_lock = threading.Lock()
        self._send_footprints_lock = threading.Lock()
        self._current_execution_lock = threading.Lock()
        self._current_execution_id = str(uuid.uuid4())
        self._current_execution_id_lock = threading.Lock()
        self._coverage_counter = 0
        self._last_collection_time = self.get_current_time_milliseconds()

    def add_coverage_task(self, *args, **kwargs):
        with self._add_coverage_lock:
            start = self._last_collection_time
            end = self.get_current_time_milliseconds()
            self._last_collection_time = end
            coverage_data: dict[str, list[int]] = {}
            file_lines_coverage = self.code_coverage_manager.get_coverage_file_line()
            if file_lines_coverage:
                self._coverage_counter += len(file_lines_coverage)
                log.debug(
                    f"Collected {len(file_lines_coverage)} files of coverage data"
                )
                for file_name, lines in file_lines_coverage.items():
                    if not self.build_mapping.has_file(file_name):
                        log.debug(
                            f"File: {file_name} not found in build context, ignoring lines: {lines}"
                        )
                        continue
                    for line in lines:
                        unique_id = self.build_mapping.get_method_unique_id(
                            file_name, line
                        )
                        if not unique_id:
                            continue
                        coverage_data.setdefault(unique_id, []).append(line)
            if coverage_data:
                log.debug(
                    f"Created coverage data for {len(coverage_data)} methods for footprints processing"
                )
                has_active_execution = self.has_active_execution()
                if self.config_data.drop_init_footprints:
                    log.info(
                        f"Dropping init footprints is active, will ignore {len(coverage_data)} methods"
                    )
                else:
                    self.footprints_service.add_coverage(
                        coverage_data, not has_active_execution, start, end
                    )

    def send_footprints_task(self, *args, **kwargs):
        with self._send_footprints_lock:
            (
                execution_is_active,
                execution_id,
                test_stage,
                execution_build_session_id,
            ) = self.get_execution_data()
            has_coverage_recorded = self.footprints_service.has_coverage_recorded()
            # log.info(self._coverage_counter)
            if not execution_is_active:
                if has_coverage_recorded:
                    log.debug(
                        "Coverage is recorded but no execution is active. Will not send footprints"
                    )
                return
            try:
                if has_coverage_recorded:
                    log.info("Execution is active, sending footprints...")
                    log.info(self.build_mapping.get_coverage_metrics())
                    self.footprints_service.send(
                        execution_id, test_stage, execution_build_session_id
                    )
                else:
                    log.debug(
                        "Execution is active but no coverage is recorded. Will not send footprints"
                    )
            except Exception as e:
                log.exception(f"Failed Sending Footprints. Error: {str(e)}")
                if self._agent_events_manager:
                    self._agent_events_manager.send_agent_test_event_error(e)

    def start(self):
        log.info("Starting Footprints Manager")
        try:
            self.scheduler_manager.start()
            if not self.auto_execution:
                self.get_active_execution()
            else:
                self.start_execution()
            log.info("Started Footprints Manager")
        except Exception as e:
            log.exception("Failed Starting Footprints Manager. Error: %s" % str(e))

    def shutdown(self, is_master):
        log.info("Shutting Down Footprints Manager")
        try:
            log.debug("Shutting down scheduler manager")
            self.scheduler_manager.shutdown()
            log.debug("Shutting down footprints service workers")
            self.footprints_service.stop()
            log.debug(
                "Checking if execution is active and sending pending footprints if needed"
            )
            execution_is_active, _, _, _ = self.get_execution_data()
            if not execution_is_active:
                self.get_active_execution()
            log.debug("Collecting last coverage data and sending footprints if needed")
            self.add_coverage_task()
            self.send_footprints_task()
            log.debug("Shutting down code coverage manager")
            self.code_coverage_manager.shutdown(is_master)
            if self.auto_execution:
                self.end_execution()
            log.info("Finished Shutting Down Footprints Manager")
        except Exception as e:
            log.exception("Failed Shutting Down Footprints Manager. Error: %s" % str(e))

    def get_active_execution(self):
        execution_response = self.backend_proxy.has_active_execution_v4(
            self.config_data
        )
        send_now = False
        with self._current_execution_lock:
            if not self._current_execution and execution_response:
                log.debug(
                    "Execution is now active, Details: %s, pending coverage data will be sent now."
                    % execution_response
                )
                send_now = True
            if self._current_execution and not execution_response:
                log.debug(
                    "Execution is not active anymore, new coverage data will be kept until next active execution"
                )
            self._current_execution = execution_response
        if send_now:
            self.send_footprints_task()

    def get_current_time_milliseconds(self):
        return int(round(time.time() * 1000))

    def get_execution_data(self):
        with self._current_execution_lock:
            if not self._current_execution:
                return False, None, None, None
            status = self._current_execution.get("status", None)
            if status not in ["pendingDelete", "created"]:
                return False, None, None, None
            execution_id = self._current_execution.get("executionId", None)
            test_stage = self._current_execution.get("testStage", None)
            execution_build_session_id = self._current_execution.get("executionBuildSessionId", None)

        return True, execution_id, test_stage, execution_build_session_id

    def start_execution(self):
        with self._current_execution_id_lock:
            execution_request = {
                "executionId": self._current_execution_id,
                "labId": self.config_data.labId,
                "testStage": self.config_data.testStage,
                "testGroupId": self.config_data.testGroupId,
                "appName": self.config_data.appName,
                "branchName": self.config_data.branchName,
                "buildName": self.config_data.buildName,
            }
        self.backend_proxy.start_execution(self.config_data, execution_request)
        with self._current_execution_lock:
            self._current_execution = {
                "status": "created",
                "executionId": execution_request["executionId"],
                "testStage": self.config_data.testStage,
                "executionBuildSessionId": self.config_data.buildSessionId,
            }
        log.debug(
            "Started execution for labid: %s, testgroupid: %s"
            % (self.config_data.labId, self.config_data.testGroupId)
        )

    def end_execution(self):
        with self._current_execution_id_lock:
            execution_id = self._current_execution_id
        self.backend_proxy.end_execution(
            self.config_data,
            self.config_data.labId,
            self.config_data.testGroupId,
            execution_id,
        )
        with self._current_execution_lock:
            self._current_execution = None
        log.debug(
            "Ended execution for labid: %s, testgroupid: %s"
            % (self.config_data.labId, self.config_data.testGroupId)
        )

    def has_active_execution(self):
        with self._current_execution_lock:
            if not self._current_execution:
                return False
            return self._current_execution.get("executionId", None) is not None

    def get_trace_function(self):
        return self.code_coverage_manager.get_trace_function()

    def get_current_execution_id(self):
        with self._current_execution_id_lock:
            return self._current_execution_id
