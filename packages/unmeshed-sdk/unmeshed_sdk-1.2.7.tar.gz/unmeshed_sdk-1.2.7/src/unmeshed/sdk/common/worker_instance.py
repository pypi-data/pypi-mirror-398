from dataclasses import dataclass

from ..apis.workers.worker import Worker


@dataclass
class WorkerInstance:
    worker: 'Worker'  # Type hinting with a forward declaration since Worker is not defined here

    def get_worker(self) -> 'Worker':
        return self.worker

    def set_worker(self, worker: 'Worker'):
        self.worker = worker
