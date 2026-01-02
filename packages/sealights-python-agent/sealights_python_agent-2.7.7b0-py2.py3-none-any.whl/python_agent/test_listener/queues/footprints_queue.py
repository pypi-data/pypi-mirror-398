import logging

from queue import Queue

from python_agent.packages.blinker import signal

log = logging.getLogger(__name__)


class FootprintsQueue(Queue, object):
    def __init__(self, maxsize=0):
        super(FootprintsQueue, self).__init__(maxsize=maxsize)

    def put(self, item, block=True, timeout=None):
        super(FootprintsQueue, self).put(item, block=block, timeout=timeout)
        if self.full():
            footprints_queue_full = signal("footprints_queue_full")
            log.info("Footprints Queue is Full. Signaling...")
            footprints_queue_full.send()

    def get_all(self):
        test_coverage_items = []
        while not self.empty():
            test_coverage_item = self.get()
            test_coverage_items.append(test_coverage_item)
        return test_coverage_items

    def put_all(self, footprint_items):
        for footprint_item in footprint_items:
            self.put(footprint_item)
