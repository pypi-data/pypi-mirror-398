from ipamd.public.shared_data import config
import os
import sys
from rich.console import Console
from multiprocessing import Process
import signal
import time

def in_notebook():
    return 'ipykernel' in sys.modules

class OutputLevel:
    VERBOSE = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
output_level = config.get('output_level')
console = Console()
def verbose(message):
    if output_level <= OutputLevel.VERBOSE:
        console.print(f'{message}', style='bright_black')
def info(message):
    if output_level <= OutputLevel.INFO:
        console.print(f'{message}')
def warning(message):
    if output_level <= OutputLevel.WARNING:
        console.print(f'Warning: {message}', style='yellow')
def error(message):
    if output_level <= OutputLevel.ERROR:
        console.print(f'Error: {message}', style='red')
def output(message):
    console.print(f'{message}')

def captured(func):
    def wrapper(*args, **kwargs):
        read_fd, write_fd = os.pipe()
        original_stdout_fd = os.dup(sys.stdout.fileno())
        original_stderr_fd = os.dup(sys.stderr.fileno())
        try:
            os.dup2(write_fd, sys.stdout.fileno())
            os.dup2(write_fd, sys.stderr.fileno())
            result = func(*args, **kwargs)
            os.close(write_fd)
            captured_output = os.read(read_fd, 1024).decode()
        finally:
            os.dup2(original_stdout_fd, sys.stdout.fileno())
            os.dup2(original_stderr_fd, sys.stderr.fileno())
            os.close(read_fd)
            os.close(original_stdout_fd)
            os.close(original_stderr_fd)
        return result, captured_output

    def wrapper_notebook(*args, **kwargs):
        result = func(*args, **kwargs)
        return result, ''
    if in_notebook():
        return wrapper_notebook
    else:
        return wrapper


def captured_async(parent_conn, timeout=1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            read_fd, write_fd = os.pipe()
            original_stdout_fd = os.dup(sys.stdout.fileno())
            original_stderr_fd = os.dup(sys.stderr.fileno())
            try:
                os.dup2(write_fd, sys.stdout.fileno())
                os.dup2(write_fd, sys.stderr.fileno())

                def sender(conn):
                    def cleanup(signum, frame):
                        conn.close()
                        sys.exit(0)

                    signal.signal(signal.SIGTERM, cleanup)
                    buffer = ''
                    while True:
                        new_data = os.read(read_fd, 1024).decode()
                        buffer += new_data
                        position_of_last_nl = buffer.rfind('\n')
                        if position_of_last_nl != -1:
                            content = buffer[:position_of_last_nl]
                            conn.send(content)
                            buffer = buffer[position_of_last_nl + 1:]
                        time.sleep(timeout)

                process = Process(target=sender, args=(parent_conn,))
                def cleanup(signum, frame):
                    process.terminate()
                signal.signal(signal.SIGTERM, cleanup)
                process.start()
                result = func(*args, **kwargs)
                time.sleep(timeout + 1)
                cleanup(0, 0)
                process.join()
                os.close(write_fd)
            finally:
                os.dup2(original_stdout_fd, sys.stdout.fileno())
                os.dup2(original_stderr_fd, sys.stderr.fileno())
                os.close(read_fd)
                os.close(original_stdout_fd)
                os.close(original_stderr_fd)
            return result
        return wrapper
    return decorator