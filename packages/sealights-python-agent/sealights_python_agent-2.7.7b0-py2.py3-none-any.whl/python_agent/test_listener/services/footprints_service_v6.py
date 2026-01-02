import json
import logging
import queue
import threading
import time

from typing import List, Dict

from python_agent.common.config_data import ConfigData

log = logging.getLogger(__name__)


class FootprintModel(object):
    def __init__(self, config_data: ConfigData):
        self.formatVersion = "6.0"
        self.meta = {
            "agentId": config_data.agentId,
            "labId": config_data.labId,
            "intervals": {
                "timedFootprintsCollectionIntervalSeconds": config_data.intervalSeconds
            },
        }
        self.methods = []
        self.executions = []
        self._hits = []
        self._total_lines = 0

    def has_hits(self):
        return bool(self._hits)

    def add_hits(
        self, methods: Dict[str, List[int]], is_init_footprint: bool, start, end
    ) -> "FootprintModel":
        methods_indexes = []
        methods_lines: Dict[str, List[int]] = {}
        for method, lines in methods.items():
            lines.sort()
            # log.debug(f"Adding coverage method: {method} with lines: {lines}")
            self._total_lines += len(lines)
            if method not in self.methods:
                self.methods.append(method)
            method_index = self.methods.index(method)
            methods_indexes.append(method_index)
            methods_lines[str(method_index)] = lines
        self._hits.append(
            {
                "start": start,
                "end": end,
                "methods": methods_indexes,
                "methodLines": methods_lines,
                "isInitFootprints": is_init_footprint,
            }
        )
        return self

    def complete(self, execution_id: str) -> "FootprintModel":
        self.executions.append({"executionId": execution_id, "hits": self._hits})
        log.debug(
            f"Footprints completed for lab id: {self.meta['labId']}, execution id: {execution_id}, methods: {len(self.methods)}, lines: {self._total_lines} in {len(self._hits)} hits"
        )
        return self

    def to_json(self):
        return {
            "formatVersion": self.formatVersion,
            "meta": self.meta,
            "methods": self.methods,
            "executions": self.executions,
        }

    def get_current_time_milliseconds(self):
        return int(round(time.time() * 1000))


class FootprintsService(object):
    def __init__(self, config_data, backend_proxy):
        self.config_data = config_data
        self.backend_proxy = backend_proxy
        self.footprints_buffer = []
        self.last_footprint = FootprintModel(self.config_data)

        # No need for multiprocessing manager and lock proxies in a threading context
        self.footprints_buffer_lock = threading.Lock()

        self.task_queue = queue.Queue()  # Thread-safe queue for tasks
        self.workers = []
        self.num_workers = 5  # Number of worker threads

        for _ in range(self.num_workers):
            worker = threading.Thread(target=self._worker, daemon=True)
            self.workers.append(worker)
            worker.start()

    def _worker(self):
        while True:
            task = self.task_queue.get()
            if task is None:  # Using `None` as a signal to stop the worker
                self.task_queue.task_done()
                break
            methods_coverage, is_init_footprint, start, end = task
            self._add_coverage_process(methods_coverage, is_init_footprint, start, end)
            self.task_queue.task_done()  # Mark the task as done

    def _add_coverage_process(self, methods_coverage, is_init_footprint, start, end):
        methods_chunks = self._split_methods_coverage(methods_coverage)
        log.debug(f"Adding {len(methods_chunks)} footprints to buffer")
        footprints_to_add = []
        for chunk in methods_chunks:
            footprint = FootprintModel(self.config_data)
            footprint.add_hits(chunk, is_init_footprint, start, end)
            footprints_to_add.append(footprint)
        with self.footprints_buffer_lock:
            self.footprints_buffer.extend(footprints_to_add)

    def has_coverage_recorded(self):
        with self.footprints_buffer_lock:
            if self.footprints_buffer:
                log.debug(
                    f"Footprints buffer has {len(self.footprints_buffer)} footprints ready to send"
                )
            return bool(self.footprints_buffer)

    def add_coverage(self, methods_coverage, is_init_footprint, start, end):
        task = (methods_coverage, is_init_footprint, start, end)
        self.task_queue.put(task)

    def send(self, execution_id: str, test_stage: str, execution_build_session_id: str):
        """Send recorded footprints to the backend."""
        sending_buffer = []
        with self.footprints_buffer_lock:
            sending_buffer, self.footprints_buffer = self.footprints_buffer, []
        log.debug(f"Sending {len(sending_buffer)} footprints to backend")
        not_sent = []
        for index, footprint_model in enumerate(sending_buffer):
            try:
                log.debug(
                    f"Sending footprint {index + 1}/{len(sending_buffer)} to backend"
                )
                footprint_model.complete(execution_id)
                data = json.dumps(footprint_model.to_json(), indent=4)
                self.backend_proxy.send_footprints_v6(
                    self.config_data,
                    data,
                    execution_build_session_id,
                    test_stage,
                    execution_id,
                )
                log.debug(
                    f"Sent footprint {index + 1}/{len(sending_buffer)} to backend successfully"
                )
            except Exception as e:
                log.error(
                    f"Failed sending footprint {index + 1}/{len(sending_buffer)} to backend. Error: {str(e)}, will try again later."
                )
                not_sent.append(footprint_model)

        if not_sent:
            with self.footprints_buffer_lock:
                log.warning(
                    f"Adding {len(not_sent)} footprints back to buffer for later retry."
                )
                self.footprints_buffer.extend(not_sent)
        else:
            log.debug(f"Sent {len(sending_buffer)} footprints to backend successfully")

    def stop(self):
        """Shuts down the worker process and the manager cleanly."""
        for _ in range(self.num_workers):
            self.task_queue.put(None)  # Send shutdown signal to each worker
        for worker in self.workers:
            worker.join()

    def _split_methods_coverage(
        self, methods_coverage: Dict[str, List[int]]
    ) -> [Dict[str, List[int]]]:
        """Split the methods coverage into chunks of 1000 methods each."""
        methods_coverage_chunks = []
        methods = list(methods_coverage.keys())
        for i in range(0, len(methods), 1000):
            chunk = {
                method: methods_coverage[method] for method in methods[i : i + 1000]
            }
            methods_coverage_chunks.append(chunk)
        return methods_coverage_chunks
