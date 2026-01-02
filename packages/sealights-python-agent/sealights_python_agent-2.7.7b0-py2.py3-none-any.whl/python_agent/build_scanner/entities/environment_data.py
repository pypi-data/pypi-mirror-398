import os
import platform
import socket
import subprocess
import sys
import traceback
import uuid

from python_agent import __version__ as VERSION


class EnvironmentData(object):
    agentId = None

    def __init__(self, lab_id, test_stage, test_group_id):
        self.labId = lab_id
        self.testStage = test_stage
        self.testGroupId = test_group_id
        if not EnvironmentData.agentId:
            EnvironmentData.agentId = str(uuid.uuid4())
        self.agentId = EnvironmentData.agentId
        self.agentType = "python"
        self.agentVersion = VERSION
        self.machineName = socket.gethostname()
        self.platform = platform.platform()
        self.os = platform.system()
        self.osVersion = platform.release()
        self.arch = platform.machine()
        self.processId = os.getpid()
        self.dependencies = self.get_dependencies()
        self.compiler = platform.python_compiler()
        self.interpreter = platform.python_implementation()
        self.runtime = platform.python_version()

    def get_dependencies(self):
        dependencies = {}
        try:
            return self.try_get_dependencies_from_pkg_resources()
        except Exception as e:
            dependencies["pkg_resources_error"] = str(e)
            dependencies["pkg_resources_traceback"] = traceback.format_exc()

        try:
            return self.try_get_dependencies_from_pip()
        except Exception as e:
            dependencies["pip_error"] = str(e)
            dependencies["pip_traceback"] = traceback.format_exc()

    def try_get_dependencies_from_pkg_resources(self):
        import pkg_resources

        dependencies = {}
        for dependency_name, dependency_object in list(
            pkg_resources.working_set.by_key.items()
        ):
            dependencies[dependency_name] = dependency_object.version
        return dependencies

    def try_get_dependencies_from_pip(self):
        dependencies = {}
        raw_dependencies = subprocess.check_output(
            [sys.executable, "-m", "pip", "freeze"]
        ).split("\n")
        raw_dependencies = raw_dependencies[:-1]  # remove last empty string
        for raw_dependency in raw_dependencies:
            dependencies_parts = raw_dependency.split("==")
            dependencies[dependencies_parts[0]] = (
                dependencies_parts[1]
                if len(dependencies_parts) == 2
                else dependencies_parts[0]
            )
        return dependencies
