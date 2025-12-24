import threading

from .tail_log_file import tail_log_file

class TailFileService:
    def __init__(self, filepath, max_lines=100, interval=1.0, display_writer=None):
        self.filepath = filepath
        self.max_lines = max_lines
        self.interval = interval
        self._thread = None
        self._display_writer = display_writer
        self._stop_event = threading.Event()

    def _run(self):
        tail_log_file(
            self.filepath,
            max_lines=self.max_lines,
            interval=self.interval,
            display_writer=self._display_writer,
            stop_event=self._stop_event
        )

    def _print(self, msg):
        print(msg)

    def start(self, filepath=None, max_lines=None, interval=None):
        if self._thread and self._thread.is_alive():
            self._print(f"{self.__class__.__name__} is already running.")
            return

        if filepath is not None:
            self.filepath = filepath
        if max_lines is not None:
            self.max_lines = max_lines
        if interval is not None:
            self.interval = interval

        if self.filepath is None:
            self._print(f"{self.__class__.__name__} is not ready (filepath is None)")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._print(f"{self.__class__.__name__} started.")

    def stop(self):
        if not self._thread:
            self._print(f"{self.__class__.__name__} is not running.")
            return

        self._stop_event.set()
        self._thread.join()
        self._thread = None
        self._print(f"{self.__class__.__name__} stopped.")
