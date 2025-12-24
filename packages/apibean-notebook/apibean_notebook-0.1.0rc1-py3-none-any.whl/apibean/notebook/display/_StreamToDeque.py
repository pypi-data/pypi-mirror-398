from collections import deque

class StreamToDeque:
    def __init__(self, buffer: deque, lock, writer, max_lines=10, refresh_change=True, prefix='', stream_type='stdout'):
        self.buffer = buffer
        self.lock = lock
        self.writer = writer
        self.max_lines = max_lines
        self.refresh_change = refresh_change
        self.prefix = prefix
        self.stream_type = stream_type

    def write(self, message):
        with self.lock:
            lines = message.splitlines()
            for line in lines:
                if line.strip():
                    self.buffer.append(f"{self.prefix}{line}")
            if self.refresh_change:
                self._refresh_output()

    def flush(self):
        pass

    def _refresh_output(self):
        self.writer.render(self.buffer, stream_type=self.stream_type)
