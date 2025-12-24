from ._EmbeddedAPIServerDev import EmbeddedAPIServerDev

from IPython import get_ipython
import socket
import os
import psutil

class EmbeddedAPIServerLab(EmbeddedAPIServerDev):
    def __init__(self, *args, show_kernel_info: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.show_kernel_info = show_kernel_info

    def status(self) -> dict:
        info = super().status()

        if not self.show_kernel_info:
            return info

        # IPython kernel info
        ipy = get_ipython()
        shell_class = ipy.__class__.__name__ if ipy else None
        shell_module = ipy.__class__.__module__ if ipy else None
        process = psutil.Process(os.getpid())

        # Network
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except:
            local_ip = "Unavailable"

        # Try get Jupyter info from env
        jupyter_env = {
            k: v for k, v in os.environ.items()
            if k.startswith("JPY_") or k.startswith("JUPYTER") or k in ("VIRTUAL_ENV", "CONDA_DEFAULT_ENV")
        }

        return {
            **info,
            "kernel": {
                "pid": os.getpid(),
                "parent_pid": process.ppid(),
                "shell_class": shell_class,
                "shell_module": shell_module,
            },
            "jupyter_env": jupyter_env,
        }
