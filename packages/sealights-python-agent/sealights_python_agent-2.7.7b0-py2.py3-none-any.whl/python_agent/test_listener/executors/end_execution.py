import logging

from python_agent.test_listener.executors.anonymous_execution import AnonymousExecution
from python_agent.utils import disableable

log = logging.getLogger(__name__)


class EndAnonymousExecution(AnonymousExecution):
    def __init__(self, config_data, labid, testgroupid):
        super(EndAnonymousExecution, self).__init__(config_data, labid)
        self.testgroupid = testgroupid

    @disableable()
    def execute(self):
        self.backend_proxy.end_execution(self.config_data, self.labid, self.testgroupid)
        log.info(
            "Finished execution for labid: %s, testgroupid: %s"
            % (self.labid, self.testgroupid)
        )
