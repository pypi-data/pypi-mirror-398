import threading

class StepQueuePollState:
    def __init__(self, total_count):
        self._in_progress = 0  # Initialize local value with 0
        self.total_count = total_count
        self._lock = threading.Lock()

    def max_available(self):
        return self.total_count - self._in_progress

    def acquire_max_available(self):
        with self._lock:
            available = self.total_count - self._in_progress
            self._in_progress = self._in_progress + available
            return available

    def release(self, count):
        with self._lock:
            self._in_progress = max(0, self._in_progress - count)