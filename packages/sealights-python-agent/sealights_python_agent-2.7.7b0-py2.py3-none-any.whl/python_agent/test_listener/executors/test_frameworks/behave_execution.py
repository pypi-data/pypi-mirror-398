import logging
import os
import sys

from python_agent.test_listener.executors.test_frameworks.agent_execution import (
    AgentExecution,
)
from python_agent.test_listener.sealights_api import SeaLightsAPI
from python_agent.utils import create_md5

log = logging.getLogger(__name__)
is_behave_installed = False

try:
    from behave.runner import ModelRunner
    from behave.__main__ import main as behave_main
    from behave.model import Scenario
    from behave.model_core import Status

    is_behave_installed = True
except ImportError:
    pass


class BehaveAgentExecution(AgentExecution):
    def __init__(
        self,
        config_data,
        labid,
        test_stage,
        cov_report,
        per_test,
        interval,
        test_group_id,
        args,
    ):
        config_data.isInitialColor = False
        self.args = args
        self.excluded_set = {}
        self.is_sealights_agent_ready = False
        self.feature_file_content_cache = {}
        try:
            super(BehaveAgentExecution, self).__init__(
                config_data,
                labid,
                test_stage,
                cov_report=cov_report,
                per_test=per_test,
                interval=interval,
                test_group_id=test_group_id,
            )
            self.execution_id = SeaLightsAPI.create_execution_id()
            self.set_test_exclude_set()
            self.is_sealights_agent_ready = True
        except Exception as e:
            log.error("Failed initializing AgentExecution. Error: %s" % str(e))

    def execute(self):
        if not is_behave_installed:
            log.error(
                "Behave is not installed. Please install it using: pip install behave"
            )
            return
        sys.path.insert(0, os.getcwd())
        if not self.is_sealights_agent_ready:
            log.warning("Sealights agent is disabled")
        else:
            self.add_sealights_hooks()
        if len(self.args) >= 1:
            behave_main(self.args)
        else:
            behave_main()

    def add_sealights_hooks(self):
        behave_run_hook = ModelRunner.run_hook
        this = self

        def run_hook(self, name, context, *args):
            if name == "before_all":
                this.run_before_all()
                behave_run_hook(self, name, context, *args)
            elif name == "after_all":
                behave_run_hook(self, name, context, *args)
                this.run_after_all()
            elif name == "before_scenario":
                scenario = getattr(context, "scenario", None)
                if scenario is not None and isinstance(scenario, Scenario):
                    this.run_before_scenario(scenario)

                behave_run_hook(self, name, context, *args)
            elif name == "after_scenario":
                behave_run_hook(self, name, context, *args)
                scenario = getattr(context, "scenario", None)
                if scenario is not None and isinstance(scenario, Scenario):
                    this.run_before_scenario(scenario)
                this.run_after_scenario(scenario)

        ModelRunner.run_hook = run_hook
        log.debug("Added SeaLights hooks to behave")

    def set_test_exclude_set(self):
        try:
            self.excluded_set = set(
                [t.get("name", "") for t in SeaLightsAPI.get_excluded_tests()]
            )
        except Exception as e:
            log.exception("failed getting excluded tests. error: %s" % str(e))

    def run_before_all(self):
        try:
            SeaLightsAPI.notify_execution_start(self.execution_id)
            self.is_execution_ready = True
            log.debug("Sealights execution started")
        except Exception as e:
            log.exception(
                "failed sending execution start form behave. error: %s" % str(e)
            )

    def run_after_all(self):
        try:
            SeaLightsAPI.notify_execution_end(self.execution_id)
            self.is_execution_ready = False
            log.debug("Sealights execution ended")
        except Exception as e:
            log.exception("failed sending execution end from nose. error: %s" % str(e))

    def run_before_scenario(self, scenario):
        test_name = f"{scenario.feature.name}:{scenario.name}"
        test_checksum = self.get_test_checksum(scenario)
        SeaLightsAPI.notify_test_start(self.execution_id, test_name, test_checksum)
        log.debug("send test start for scenario: %s" % test_name)
        if test_name in self.excluded_set:
            SeaLightsAPI.notify_test_end(self.execution_id, test_name, 1, "skipped")
            log.debug("send test end for scenario: %s which is excluded" % test_name)
            scenario.skip()

    def run_after_scenario(self, scenario):
        test_status = getattr(scenario, "status", None)
        if test_status is None:
            log.error("scenario.status is not defined")
            return
        if test_status == Status.passed:
            test_status_str = "passed"
        elif test_status == Status.failed:
            test_status_str = "failed"
        elif test_status == Status.skipped:
            test_status_str = "skipped"
        else:
            log.error("scenario.status is not valid")
            return
        test_name = f"{scenario.feature.name}:{scenario.name}"
        test_checksum = self.get_test_checksum(scenario)
        test_duration = getattr(scenario, "duration", 1)
        SeaLightsAPI.notify_test_end(
            self.execution_id, test_name, test_duration, test_status_str, test_checksum
        )
        log.debug(
            "send test end for scenario: %s status: %s" % (test_name, test_status_str)
        )

    def get_test_checksum(self, scenario):
        if scenario.filename not in self.feature_file_content_cache:
            try:
                with open(scenario.filename, "r") as file:
                    self.feature_file_content_cache[scenario.filename] = (
                        file.readlines()
                    )
            except FileNotFoundError:
                log.debug("feature file not found: %s" % scenario.filename)
                return ""
        try:
            line_content = self.feature_file_content_cache[scenario.filename][
                scenario.line - 1
            ]
            line_content = "".join(line_content.split())
        except IndexError:
            log.debug("line number not found: %s" % scenario.line)
            return ""
        checksum = create_md5()
        checksum.update(line_content.encode())
        return checksum.hexdigest()
