import logging
import os
import threading
from typing import Dict, List

import python_agent
from python_agent.common import constants
from python_agent.packages.coverage import Coverage, CoverageData

log = logging.getLogger(__name__)


class CodeCoverageManager(object):
    def __init__(self, config_data):
        self.config_data = config_data
        self.save_cov_report = bool(self.config_data.covReport)
        self.coverage_lock = threading.Lock()
        self.coverage_file_name = f".coverage.sl.{os.getpid()}"
        self.coverage = self.init_coverage()

    def get_coverage_file_line(self) -> [Dict[str, List[int]], None]:
        file_lines = {}
        with self.coverage_lock:
            if constants.IN_TEST:
                # save coverage data that can be later be converted to footprints before reset
                self.coverage.save()
            # get_data creates or updates coverage.data with the CoverageData object and clears counters on the
            # collector but not on the coverage object
            coverage_object: CoverageData = self.coverage.get_data()
            if not coverage_object:
                return None
            for filename in coverage_object.measured_files():
                normalized_filename = filename.replace("\\", "/")
                covered_lines = sorted(
                    [line for line in coverage_object.lines(filename) if line != 0]
                )
                if covered_lines:
                    file_lines[normalized_filename] = covered_lines

            if not self.save_cov_report:
                coverage_object.erase()
        return file_lines

    def shutdown(self, is_master):
        self.coverage.stop()
        if constants.IN_TEST:
            # save coverage data that can be later be converted to footprints
            self.coverage.save()
        if self.config_data.covReport:
            self.generate_report(is_master)
        if os.path.exists(self.coverage_file_name):
            os.remove(self.coverage_file_name)

    def get_trace_function(self):
        return self.coverage._collector._installation_trace

    def init_coverage(self):
        self.config_data.include = self.config_data.include or []
        self.config_data.include.append(
            "*%s*" % os.path.abspath(self.config_data.workspacepath)
        )
        if constants.IN_TEST:
            # coverage.py ignores "include" if source is given so, in order to include python agent coverage
            # we move workspacepath to include, include python_agent, remove exclude and add "data_suffix=True" so
            # coverage files will be saved each time with a unique suffix so we won't loose coverage after each reset
            self.config_data.include.append("*%s*" % python_agent.__name__)
            coverage = Coverage(
                source=None,
                include=self.config_data.include,
                omit=None,
                data_suffix=True,
                branch=False,
            )
        else:
            data_file = None
            if self.save_cov_report:
                data_file = self.coverage_file_name
            coverage = Coverage(
                source=None,
                include=self.config_data.include,
                omit=self.config_data.exclude,
                branch=False,
                data_file=data_file,
            )
        if getattr(coverage, "_warn_no_data", False):
            coverage._warn_no_data = False
        if self.config_data.isOfflineMode:
            # no actual tracing is done here
            # we're loading the raw coverage data from the .coverage file
            # so coverage.get_data() will return it and we'll convert it to footprints
            coverage.load()
        else:
            coverage.start()

        return coverage

    def generate_report(self, is_master):
        self.coverage.save()
        if not is_master:
            # in case of xdist, we have multiple agent instances, only the master will load, combine all coverage files
            # and generated the xml report
            return
        self.coverage.load()
        self.coverage.combine()
        try:
            self.coverage.xml_report(
                ignore_errors=True, outfile=self.config_data.covReport
            )
            log.info("Coverage report created in %s" % self.config_data.covReport)
        except Exception as e:
            log.error("Failed creating report. error=%s" % e)
