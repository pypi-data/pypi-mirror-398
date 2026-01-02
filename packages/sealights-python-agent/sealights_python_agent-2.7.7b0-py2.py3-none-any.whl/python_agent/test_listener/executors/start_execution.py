import logging

from python_agent.test_listener.entities.start_execution_request import (
    StartExecutionRequest,
)
from python_agent.test_listener.executors.anonymous_execution import AnonymousExecution
from python_agent.utils import disableable

log = logging.getLogger(__name__)


class StartAnonymousExecution(AnonymousExecution):
    def __init__(self, config_data, test_stage, labid, testgroupid):
        super(StartAnonymousExecution, self).__init__(config_data, labid)
        self.test_stage = test_stage
        self.testgroupid = testgroupid

    @disableable()
    def execute(self):
        start_execution_request = StartExecutionRequest(
            self.config_data.customerId,
            self.config_data.appName,
            self.config_data.branchName,
            self.config_data.buildName,
            self.labid,
            self.test_stage,
            self.testgroupid,
            self.config_data.agentId
        )
        self.backend_proxy.start_execution(self.config_data, start_execution_request)
        log.info(
            "Started execution for labid: %s, testgroupid: %s"
            % (self.labid, self.testgroupid)
        )
