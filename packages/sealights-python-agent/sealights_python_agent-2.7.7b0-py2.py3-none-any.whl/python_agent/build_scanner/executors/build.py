import logging

from python_agent.build_scanner import app as build_scanner
from python_agent.common.agent_events.agent_events_manager import AgentEventsManager
from python_agent.common.constants import AGENT_TYPE_BUILD_SCANNER
from python_agent.utils import disableable

log = logging.getLogger(__name__)


class Build(object):
    def __init__(self, config_data):
        self.config_data = config_data
        self.config_data.agentType = AGENT_TYPE_BUILD_SCANNER
        self.workspacepath = self.config_data.additionalParams.get("workspacepath")
        self.include = self.config_data.additionalParams.get("include") or None
        self.exclude = self.config_data.additionalParams.get("exclude") or None
        self.agent_manager = AgentEventsManager(config_data=config_data)

    @disableable()
    def execute(self):
        log.info("Starting Build Scan")
        self.agent_manager.send_agent_start(lab_id="", test_stage="")
        try:
            build_scanner.main(
                config_data=self.config_data,
                workspacepath=self.workspacepath,
                include=self.include,
                exclude=self.exclude,
            )

        except Exception as e:
            log.exception("Build Scan Failed. Error: %s" % str(e))
            self.agent_manager.send_agent_build_scan_error(e)

        self.agent_manager.send_agent_stop()
        log.info("Build Scan Finished")
