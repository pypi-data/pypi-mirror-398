import logging

from python_agent.common.build_session.build_session_data import BuildSessionData
from python_agent.common.constants import BUILD_SESSION_ID_FILE
from python_agent.common.http.backend_proxy import BackendProxy
from python_agent.utils import disableable

log = logging.getLogger(__name__)


class Config(object):
    def __init__(
        self,
        config_data,
        app_name,
        branch_name,
        build_name,
        build_session_id,
        workspacepath,
        include,
        exclude,
    ):
        self.config_data = config_data
        self.config_data.appName = app_name
        self.config_data.buildName = build_name
        self.config_data.branchName = branch_name
        self.config_data.buildSessionId = build_session_id
        self.config_data.workspacepath = workspacepath
        self.config_data.include = include
        self.config_data.exclude = exclude
        self.backend_proxy = BackendProxy(config_data)

    @disableable()
    def execute(self):
        additional_params = {
            "workspacepath": self.config_data.workspacepath,
            "include": self.config_data.include,
            "exclude": self.config_data.exclude,
        }
        build_session_data = BuildSessionData(
            self.config_data.appName,
            self.config_data.buildName,
            self.config_data.branchName,
            self.config_data.buildSessionId,
            additional_params=additional_params,
            pull_request_params=None,
        )
        try:
            log.info("Creating Build Session Id")
            build_session_id = self.backend_proxy.create_build_session_id(
                self.config_data,
                build_session_data,
            )
            Config.write_build_session_to_file(build_session_id)
            log.info(
                "Creating Build Session Id completed with Build Session Id: %s"
                % build_session_id
            )
        except Exception as e:
            log.error(str(e))

    @staticmethod
    def write_build_session_to_file(build_session_id):
        try:
            with open(BUILD_SESSION_ID_FILE, "w") as f:
                build_session_id = build_session_id.replace('"', "")
                f.write(build_session_id)
        except Exception as e:
            log.error(
                "Failed Saving Build Session Id File to: %s. Error: %s"
                % (BUILD_SESSION_ID_FILE, str(e))
            )
