import os

from python_agent.common import constants
from python_agent.test_listener.managers.agent_manager import AgentManager
from python_agent.utils import disableable


class AgentExecution(object):
    def __init__(
        self,
        config_data,
        labid,
        test_stage=None,
        cov_report=None,
        per_test=True,
        interval=constants.INTERVAL_IN_MILLISECONDS,
        init_agent=True,
        test_group_id=None,
    ):
        self.config_data = config_data
        if self.config_data.get_is_disabled():
            return
        self.labid = self.resolve_lab_id(labid)
        if cov_report:
            self.config_data.covReport = cov_report
        if test_stage:
            self.config_data.testStage = test_stage
        if self.config_data.testStage is None:
            self.config_data.testStage = constants.DEFAULT_ENV

        if test_group_id:
            self.config_data.testGroupId = test_group_id

        self.config_data.labId = self.labid
        self.config_data.workspacepath = self.config_data.additionalParams.get(
            "workspacepath", constants.DEFAULT_WORKSPACEPATH
        )
        self.config_data.include = self.config_data.additionalParams.get("include")
        self.config_data.exclude = self.config_data.additionalParams.get("exclude")
        self.config_data.perTest = per_test
        self.config_data.interval = interval
        self.config_data.intervalSeconds = interval / 1000
        if init_agent:
            self.init_agent()

    def resolve_lab_id(self, labid):
        if labid is not None:
            return labid
        labid_from_env = os.environ.get("SL_LAB_ID", None)
        if labid_from_env is not None:
            return labid_from_env
        return (
            self.config_data.buildSessionId
            or self.config_data.appName
            or constants.DEFAULT_LAB_ID
        )

    @disableable(fail_silently=True)
    def init_agent(self):
        AgentManager(config_data=self.config_data)
