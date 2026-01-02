import atexit
import logging
import os
import sys
import time

from python_agent import __legacy_mode__ as is_legacy_mode
from python_agent.common.agent_events.agent_events_manager import AgentEventsManager
from python_agent.common.constants import AGENT_TYPE_TEST_LISTENER
from python_agent.common.http.backend_proxy import BackendProxy
from python_agent.packages.six import add_metaclass
from python_agent.test_listener.integrations.pytest_xdist_helper import (
    override_xdist_exit_timeout,
)
from python_agent.test_listener.managers.events_manager import EventsManager
from python_agent.test_listener.managers.tia_manager import TIAManager
from python_agent.test_listener.state_tracker import StateTracker
from python_agent.test_listener.utils import Singleton

log = logging.getLogger(__name__)

if is_legacy_mode:
    from python_agent.test_listener.managers.footprints_manager import FootprintsManager
else:
    from python_agent.test_listener.managers.footprints_manager_v6 import (
        FootprintsManager,
    )


@add_metaclass(Singleton)
class AgentManager(object):
    def __init__(self, config_data=None, is_master=True):
        log.info("Initializing... Is Master? %s" % is_master)
        if not config_data:
            raise Exception("'config_data' must be provided")
        self.config_data = config_data
        self.config_data.agentType = AGENT_TYPE_TEST_LISTENER
        self.is_master = is_master
        self.pid = os.getpid()
        self.backend_proxy = BackendProxy(config_data)
        self.state_tracker = StateTracker(config_data)
        self.agents_events_manager = AgentEventsManager(config_data=config_data)
        self.agents_events_manager.send_agent_start(
            lab_id=config_data.labId, test_stage=config_data.testStage
        )
        self.footprints_manager = FootprintsManager(
            config_data, self.backend_proxy, self.agents_events_manager
        )
        self.events_manager = EventsManager(
            config_data, self.backend_proxy, self.agents_events_manager
        )
        self.tia_manager = TIAManager(config_data)
        self.footprints_manager.start()
        self.events_manager.start()

        atexit.register(self.shutdown)
        self.agent_started()
        self.register_integrations()
        # self.register_uwsgi_at_exit()

    def get_excluded_tests(self):
        return self.tia_manager.get_excluded_tests()

    def create_execution_id(self):
        if self.footprints_manager is None:
            raise Exception(
                "Footprints Manager is not initialized, cannot create execution id"
            )
        return self.footprints_manager.get_current_execution_id()

    def push_event(self, event):
        event["timestamp"] = int(round(time.time() * 1000))
        self.events_manager.push_event(event)

    def send_all(self):
        self.events_manager.send_all()
        self.footprints_manager.send_footprints_task()

    def shutdown(self):
        if self.pid == os.getpid():
            log.info("Shutting down Sealights Agent...")
            self.events_manager.shutdown()
            self.footprints_manager.shutdown(self.is_master)
            self.agents_events_manager.send_agent_stop()
            log.info("Sealights Agent has been shut down.")

    def get_trace_function(self):
        return self.footprints_manager.get_trace_function()

    def agent_started(self):
        self.push_event({"type": "agentStarted"})

    def register_integrations(self):
        override_xdist_exit_timeout()

    def register_uwsgi_at_exit(self):
        if "uwsgi" in sys.modules:
            import uwsgi

            uwsgi_original_atexit_callback = getattr(uwsgi, "atexit", None)

            def uwsgi_atexit_callback():
                self.shutdown()
                if uwsgi_original_atexit_callback:
                    uwsgi_original_atexit_callback()

            uwsgi.atexit = uwsgi_atexit_callback
