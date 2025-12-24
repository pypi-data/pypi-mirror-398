import threading
import time
from collections import deque
from IPython.utils.capture import capture_output

from ..display import StreamToDeque, DisplayWriter
from ._IntervalRunner_StreamCatcher import IntervalRunner as OriginIntervalRunner

class IntervalRunner(OriginIntervalRunner):
    def __init__(self, *args, max_lines=10, **kwargs):
        super().__init__(*args, max_lines=max_lines, **kwargs)
        self.stdout_buffer = deque(maxlen=max_lines)
        self._stdout_lock = threading.Lock()
        self.writer = DisplayWriter(title="IntervalRunner's output")
        self.stream = StreamToDeque(self.stdout_buffer, self._stdout_lock, self.writer,
                max_lines=max_lines,
                refresh_change=True,
                prefix='',
                stream_type=None)

    def _loop(self):
        while self._running:
            with capture_output() as captured:
                self.func()
            lines = captured.stdout.strip().splitlines()
            for line in lines:
                self.stream.write(line)
            '''
            IOPub message rate exceeded.
            The Jupyter server will temporarily stop sending output
            to the client in order to avoid crashing it.
            To change this limit, set the config variable
            `--ServerApp.iopub_msg_rate_limit`.

            Current values:
            ServerApp.iopub_msg_rate_limit=1000.0 (msgs/sec)
            ServerApp.rate_limit_window=3.0 (secs)
            '''
            if self.interval > 0:
                time.sleep(self.interval)

    def clear(self):
        if self.writer:
            self.writer.clear()


from apibean.notebook._example import assign_example

assign_example(IntervalRunner, '''
import random

from apibean.notebook.runners import IntervalRunner

counter = 0

def my_func():
    global counter
    counter += 1
    print(f"[{counter}] Random number: {random.randint(1, 100)}")

runner = IntervalRunner(my_func, interval=0.7, max_lines=10)

# <- Press [ Ctrl + Shift + - ] to split cells
runner.start()

# <- Press [ Ctrl + Shift + - ] to split cells
runner.stop()
''')
