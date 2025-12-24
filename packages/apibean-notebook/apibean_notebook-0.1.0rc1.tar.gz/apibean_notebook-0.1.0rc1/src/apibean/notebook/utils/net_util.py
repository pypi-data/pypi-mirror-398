import socket

def is_port_available(port: int, host: str="0.0.0.0") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def get_process_using_port(port: int):
    import psutil
    for conn in psutil.net_connections(kind="inet"):
        if conn.laddr.port == port:
            return psutil.Process(conn.pid).name() if conn.pid else None
    return None
