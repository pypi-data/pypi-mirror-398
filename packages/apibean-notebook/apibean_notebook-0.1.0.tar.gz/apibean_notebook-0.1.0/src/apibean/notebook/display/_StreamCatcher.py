import threading
from collections import deque
from contextlib import redirect_stdout, redirect_stderr

from ._DisplayWriter import DisplayWriter
from ._StreamToDeque import StreamToDeque

class StreamCatcher:
    def __init__(self, max_lines=100, refresh_change=True,
                stdout_prefix='',
                stderr_prefix='',
                redirect_stderr_to_stdout=True):
        self.max_lines = max_lines
        self.redirect_stderr_to_stdout = redirect_stderr_to_stdout

        self._writer = DisplayWriter()

        self._stdout_lock = threading.Lock()
        self._stderr_lock = threading.Lock()

        self.stdout_buffer = deque(maxlen=max_lines)
        self.stderr_buffer = deque(maxlen=max_lines) if not redirect_stderr_to_stdout else \
                self.stdout_buffer

        self._stdout_stream = StreamToDeque(self.stdout_buffer, self._stdout_lock, self._writer,
                max_lines=max_lines,
                refresh_change=refresh_change,
                prefix=stdout_prefix,
                stream_type='stdout')
        self._stderr_stream = StreamToDeque(self.stderr_buffer, self._stderr_lock, self._writer,
                max_lines=max_lines,
                refresh_change=refresh_change,
                prefix=stderr_prefix,
                stream_type='stderr') if not redirect_stderr_to_stdout else self._stdout_stream

        self._stdout_redirect = redirect_stdout(self._stdout_stream)
        self._stderr_redirect = redirect_stderr(self._stderr_stream)

    def __enter__(self):
        self._stdout_redirect.__enter__()
        self._stderr_redirect.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stderr_redirect.__exit__(exc_type, exc_val, exc_tb)
        self._stdout_redirect.__exit__(exc_type, exc_val, exc_tb)

    def get_output(self):
        return list(self.stdout_buffer), list(self.stderr_buffer)


from apibean.notebook._example import assign_example

assign_example(StreamCatcher, '''
import threading
import time

from apibean.notebook.display import StreamCatcher

def example_loop():
    with StreamCatcher(max_lines=8):
        for i in range(20):
            print(f"Printed line {i}")
            time.sleep(0.5)

# Chạy trong thread để không chặn notebook
threading.Thread(target=example_loop, daemon=True).start()
''')
