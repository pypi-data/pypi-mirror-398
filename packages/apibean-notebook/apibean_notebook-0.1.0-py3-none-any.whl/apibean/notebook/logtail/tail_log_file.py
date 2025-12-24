import os
import time
from collections import deque
from IPython.display import clear_output

from ..display import DisplayWriter

def _read_last_lines_by_seek(filepath, max_lines=100, encoding='utf-8'):
    """
    Đọc file từ cuối, tìm và trả về max_lines dòng cuối cùng.
    """
    with open(filepath, 'rb') as f:
        f.seek(0, os.SEEK_END)
        pos = f.tell()
        block_size = 1024
        data = bytearray()
        line_count = 0

        while pos > 0 and line_count <= max_lines:
            read_size = min(block_size, pos)
            pos -= read_size
            f.seek(pos)
            block = f.read(read_size)
            data = block + data
            line_count = data.count(b'\n')

        lines = data.split(b'\n')[-max_lines:]
        return [line.decode(encoding, errors='replace') for line in lines]

def _print_deque_buffer(log_buffer, display_writer=None, print_with_join:bool=False):
    if display_writer:
        _print_deque_buffer_to_display(log_buffer, display_writer=display_writer)
        return
    _print_deque_buffer_to_console(log_buffer, print_with_join=print_with_join)

def _print_deque_buffer_to_display(log_buffer, display_writer):
    display_writer.render(log_buffer)

def _print_deque_buffer_to_console(log_buffer, print_with_join:bool=False):
    clear_output(wait=True)
    if print_with_join:
        print("\n".join(log_buffer))
        return
    for line in log_buffer:
        print(line)

def tail_log_file(filepath, max_lines=100, interval=1.0, follow=True,
        encoding='utf-8',
        display_writer=None,
        create_display_writer_if_not_found=True,
        stop_event=None):
    """
    Đọc log như tail -f, có hỗ trợ dừng bằng stop_event (nếu cung cấp).
    """
    try:
        log_buffer = deque(
            _read_last_lines_by_seek(filepath, max_lines, encoding),
            maxlen=max_lines
        )

        if display_writer is None and create_display_writer_if_not_found:
            display_writer = DisplayWriter(title=f"{tail_log_file.__name__}'s output")
        _print_deque_buffer(log_buffer, display_writer=display_writer)

        if not follow:
            return

        with open(filepath, 'r', encoding=encoding, errors='replace') as f:
            f.seek(0, os.SEEK_END)

            while not (stop_event and stop_event.is_set()):
                line = f.readline()
                if line:
                    log_buffer.append(line.rstrip())
                    _print_deque_buffer(log_buffer, display_writer=display_writer)
                else:
                    time.sleep(interval)

        print(f"{tail_log_file.__name__}('{filepath}') ended.")
    except KeyboardInterrupt:
        print(f"{tail_log_file.__name__}('{filepath}') has stopped.")
    except Exception as e:
        print(f"{tail_log_file.__name__} error: {e}")
