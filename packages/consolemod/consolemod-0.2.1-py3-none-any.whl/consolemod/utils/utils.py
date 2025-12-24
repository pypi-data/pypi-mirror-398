from datetime import datetime

def timestamp():
    return datetime.now().strftime("[%H:%M:%S]")

def format_message(message: str, prefix: str = "", timestamped: bool = True):
    ts = timestamp() if timestamped else ""
    return f"{ts} {prefix} {message}"

if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")