import threading
import time

from ..display import StreamCatcher

class IntervalRunner:
    def __init__(self, func, interval=0.1, max_lines=10):
        self.func = func
        self.interval = interval
        self.max_lines = max_lines
        self._running = False
        self._thread = None

    def _loop(self):
        with StreamCatcher(max_lines=self.max_lines):
            while self._running:
                self.func()
                time.sleep(self.interval)

    def start(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._loop)
            self._thread.daemon = True
            self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()
        self._thread = None
