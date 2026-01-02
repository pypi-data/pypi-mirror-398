import json
import logging
import os

from python_agent import __package_name__ as PACKAGE_NAME
from python_agent import __version__ as VERSION
from python_agent.common.build_session.build_session_data import BuildSessionData
from python_agent.common.http.requests_wrapper import Requests
from python_agent.common.http.sl_metadata import SLMetadata
from python_agent.common.http.sl_routes import SLRoutes
import requests
from requests import HTTPError

log = logging.getLogger(__name__)


class BackendProxy(object):
    def __init__(self, config_data):
        self.requests = Requests(config_data)
        self.config_data = config_data
        self.debug_calls = os.environ.get("SL_DEBUG_CALLS", False)

    def get_build_session(self, config_data, build_session_id):
        try:
            sl_metadata = SLMetadata().from_config_data(config_data)
            sl_metadata.buildSessionId = build_session_id
            response = self.requests.get(
                SLRoutes.build_session_v2(build_session_id),
                sl_metadata=sl_metadata,
            )
            response.raise_for_status()
            build_session_dict = response.json()
            return self._create_build_session_data(build_session_dict)
        except Exception as e:
            log.error("Failed getting Build Session Id. Error: %s" % str(e))
            raise ConnectionError("Failed Getting Build Session Id. Error: %s" % str(e))

    def create_build_session_id(self, config_data, build_session_data):
        try:
            sl_metadata = SLMetadata().from_config_data(config_data)

            sl_metadata.buildSessionId = build_session_data.buildSessionId
            response = self.requests.post(
                SLRoutes.build_session_v2(),
                data=json.dumps(build_session_data, default=lambda m: m.__dict__),
                sl_metadata=sl_metadata,
            )
            response.raise_for_status()
            build_session_id = response.json()
            return build_session_id
        except Exception as e:
            raise ConnectionError(
                "Failed Creating Build Session Id. Error: %s" % str(e)
            )

    def create_pr_build_session_id(self, config_data, build_session_data):
        try:
            sl_metadata = SLMetadata().from_config_data(config_data)
            sl_metadata.buildSessionId = build_session_data.buildSessionId
            response = self.requests.post(
                SLRoutes.pr_build_session_v2(),
                data=json.dumps(build_session_data, default=lambda m: m.__dict__),
                sl_metadata=sl_metadata,
            )
            response.raise_for_status()
            build_session_id = response.json()
            return build_session_id
        except Exception as e:
            log.error("Failed Creating Build Session Id for PR. Error: %s" % str(e))
            return None

    def submit_build_mapping(self, config_data, build_mapping):
        try:
            response = self.requests.post(
                SLRoutes.build_mapping_v5(),
                data=json.dumps(build_mapping, default=lambda m: m.__dict__),
                sl_metadata=SLMetadata().from_config_data(config_data),
            )
            response.raise_for_status()
            log.info("Scanned build map submitted successfully")
        except HTTPError as e:
            if e.response.status_code == 409:
                log.error(
                    "Scanned build map already exists for the current build session id. No new scann was submitted"
                )
            else:
                raise ConnectionError(
                    "Failed Submitting Build Mapping. Error: %s" % str(e)
                )
        except Exception as e:
            raise ConnectionError("Failed Submitting Build Mapping. Error: %s" % str(e))

    def send_footprints(self, config_data, footprints):
        response = self.requests.post(
            SLRoutes.footprints_v5(),
            data=json.dumps(footprints, default=lambda m: m.__dict__),
            sl_metadata=SLMetadata().from_config_data(config_data),
        )
        response.raise_for_status()

    def send_footprints_v6(
        self,
        config_data,
        footprints,
        execution_build_session_id: str,
        test_stage: str,
        execution_id: str,
    ):
        sl_metadata = SLMetadata().from_config_data(config_data)
        sl_metadata.buildSessionId = execution_build_session_id
        sl_metadata.executionId = execution_id
        response = self.requests.post(
            SLRoutes.footprints_v6(
                execution_build_session_id, test_stage, config_data.buildSessionId
            ),
            data=footprints,
            sl_metadata=sl_metadata,
        )
        response.raise_for_status()

    def send_events(self, config_data, events, execution_id):
        sl_metadata = SLMetadata().from_config_data(config_data)
        sl_metadata.executionId = execution_id
        response = self.requests.post(
            SLRoutes.events_v2(),
            data=json.dumps(events, default=lambda m: m.__dict__),
            sl_metadata=sl_metadata,
        )
        response.raise_for_status()

    def start_execution(self, config_data, start_execution_request):
        sl_metadata = SLMetadata().from_config_data(config_data)
        if hasattr(start_execution_request, "executionId"):
            sl_metadata.executionId = start_execution_request.executionId

        response = self.requests.post(
            SLRoutes.test_execution_v3(),
            data=json.dumps(start_execution_request, default=lambda m: m.__dict__),
        )
        response.raise_for_status()

    def end_execution(self, config_data, lab_id, test_group_id, execution_id=None):
        params = {
            "labId": lab_id,
        }
        if execution_id:
            params["executionId"] = execution_id
        if test_group_id:
            params["testGroupId"] = test_group_id
        sl_metadata = SLMetadata().from_config_data(config_data)
        sl_metadata.executionId = execution_id
        sl_metadata.labId = lab_id
        response = self.requests.delete(
            SLRoutes.test_execution_v3(), params=params, sl_metadata=sl_metadata
        )
        response.raise_for_status()

    def upload_reports(self, upload_reports_request, config_data):
        response = self.requests.post(
            SLRoutes.external_data_v3(),
            files=upload_reports_request.__dict__,
            patch_content_type=False,
            sl_metadata=SLMetadata().from_config_data(config_data),
        )
        response.raise_for_status()

    def has_active_execution(self, customer_id, labid, config_data):
        params = {"customerId": customer_id, "labId": labid, "environment": labid}
        try:
            sl_metadata = SLMetadata().from_config_data(config_data)
            sl_metadata.labId = labid
            response = self.requests.get(
                SLRoutes.test_execution_v3(), params=params, sl_metadata=sl_metadata
            )
            parsed_response = {}
            if response.content:
                parsed_response = response.json()
            status = parsed_response.get("status")
            if status in ["pendingDelete", "created"]:
                return True
            if response.status_code == requests.codes.not_found:
                return False
        except Exception as e:
            log.exception("Error while trying to send request. Error: %s" % str(e))
            return False

    def has_active_execution_v4(self, config_data):
        try:
            sl_metadata = SLMetadata().from_config_data(config_data)
            response = self.requests.get(
                SLRoutes.test_execution_v4(config_data.labId), sl_metadata=sl_metadata
            )
            parsed_response = {}
            if response.content:
                parsed_response = response.json()
            execution = parsed_response.get("execution")
            if not execution:
                return {}
            execution_response = {
                "executionId": execution.get("executionId"),
                "status": execution.get("status"),
                "testStage": execution.get("testStage"),
                "executionBuildSessionId": execution.get("buildSessionId"),
            }
            return execution_response

        except Exception as e:
            log.exception("Error while trying to send request. Error: %s" % str(e))
            return False

    def submit_logs(self, config_data, logs_request):
        response = self.requests.post(
            SLRoutes.logsubmission_v2(),
            data=json.dumps(logs_request, default=lambda m: m.__dict__),
            sl_metadata=SLMetadata().from_config_data(config_data),
        )
        response.raise_for_status()

    def get_recommended_version(self, config_data):
        status_code = None
        try:
            response = self.requests.get(
                SLRoutes.recommended_v2(),
                sl_metadata=SLMetadata().from_config_data(config_data),
            )
            status_code = response.status_code
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if status_code == 404:
                log.info("Not upgrading agent")
            else:
                log.warning("Failed Getting Recommended Version. Error: %s" % str(e))
            return {}

    def check_version_exists_in_pypi(self, version):
        url = "https://pypi.python.org/pypi/%s/%s" % (PACKAGE_NAME, version)
        try:
            response = self.requests.get(url)
            response.raise_for_status()
            return True
        except Exception as e:
            log.warning(
                "Version: %s Doesn't exist. URL: %s. Error: %s" % (version, url, str(e))
            )
            return False

    def get_remote_configuration(self, config_data):
        try:
            url = SLRoutes.configuration_v2(
                config_data.customerId,
                config_data.appName,
                config_data.branchName,
                config_data.testStage,
                PACKAGE_NAME,
                VERSION,
            )
            response = self.requests.get(
                url, sl_metadata=SLMetadata().from_config_data(config_data)
            )
            response.raise_for_status()
            response = response.json()
            config_as_json = response["config"]
            if (config_as_json is not None) and (config_as_json != ""):
                log.info(
                    "Server returned The following configuration: '%s'" % config_as_json
                )
                config = json.loads(config_as_json)
                return config
        except HTTPError as e:
            if e.response.status_code == 404:
                log.debug("Server returned 404 (Not Found) for remote configuration. ")
            else:
                log.error("Failed getting remote configuration. Error: %s" % str(e))
        except Exception as e:
            log.error("Failed getting remote configuration. Error: %s" % str(e))
        return {}

    def try_get_recommendations(self, config_data):
        url = SLRoutes.test_exclusions(
            config_data.buildSessionId, config_data.testStage, config_data.testGroupId
        )
        try:
            response = self.requests.get(
                url, sl_metadata=SLMetadata().from_config_data(config_data)
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            log.warning(
                "failed get recommendation tests from server URL: %s. Error: %s"
                % (url, str(e))
            )
            return {}

    def get_build_session_from_labid(self, labid, config_data):
        url = SLRoutes.lab_ids_active_build_session_v1(labid)
        try:
            sl_metadata = SLMetadata().from_config_data(config_data)
            sl_metadata.labId = labid
            response = self.requests.get(url, sl_metadata=sl_metadata)
            response.raise_for_status()
            build_session_dict = response.json()
            return self._create_build_session_data(build_session_dict)
        except Exception as e:
            log.warning(
                "Failed getting active build session from lab id: %s. Error: %s"
                % (labid, str(e))
            )
            return None

    def _create_build_session_data(self, build_session_dict):
        return BuildSessionData(
            build_session_dict["appName"],
            build_session_dict["buildName"],
            build_session_dict["branchName"],
            build_session_dict["buildSessionId"],
            additional_params=build_session_dict.get("additionalParams"),
        )

    def send_agent_event(self, agent_event, config_data):
        sl_metadata = SLMetadata().from_config_data(config_data)
        if hasattr(agent_event, "message_type"):
            sl_metadata.messageType = agent_event.message_type
        if hasattr(agent_event, "agentType"):
            sl_metadata.agentType = agent_event.agentType
        if hasattr(agent_event, "labId"):
            sl_metadata.labId = agent_event.labId
        if hasattr(agent_event, "buildSessionId"):
            sl_metadata.buildSessionId = agent_event.buildSessionId
        if hasattr(agent_event, "agentId"):
            sl_metadata.agentId = agent_event.agentId

        response = self.requests.post(
            SLRoutes.agent_events_v3(),
            data=json.dumps(agent_event, default=lambda m: m.__dict__),
            sl_metadata=sl_metadata,
        )
        response.raise_for_status()

    def _format_response(self, response):
        """
        Formats the response for logging, handling different response types.
        """
        if response is None:
            return "No Response"

        # Try to get a JSON response
        try:
            json_response = response.json()
            return json.dumps(
                json_response,
                default=lambda m: m.__dict__ if hasattr(m, "__dict__") else str(m),
                indent=4,
            )
        except ValueError:
            pass

        # If response is not JSON, try to decode bytes to string
        try:
            return response.content.decode()
        except AttributeError:
            pass

        # If it's neither JSON nor bytes, use json.dumps to serialize
        try:
            return json.dumps(
                response,
                default=lambda m: m.__dict__ if hasattr(m, "__dict__") else str(m),
                indent=4,
            )
        except TypeError:
            pass

        # Fallback for other types not handled above
        return str(response)
