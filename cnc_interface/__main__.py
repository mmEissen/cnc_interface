from os import path
from typing import Optional
import subprocess
import sys

from watchdog import observers
from watchdog import events


PYTHON_EXTENSION = ".py"
PROCESS: Optional[subprocess.Popen] = None


def stop_current_process() -> None:
    global PROCESS
    if PROCESS is None:
        return
    PROCESS.terminate()
    try:
        PROCESS.wait(3)
    except subprocess.TimeoutExpired:
        pass
    else:
        PROCESS = None
        return
    PROCESS.kill()
    PROCESS.wait()
    PROCESS = None


def start_new_process() -> None:
    global PROCESS
    if PROCESS is not None:
        return
    PROCESS = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "cnc_interface.main",
        ]
    )


class EventHandler(events.FileSystemEventHandler):
    def _on_file_change(self, event: events.FileSystemEvent) -> None:
        _, extension = path.splitext(event.src_path)
        if extension != PYTHON_EXTENSION:
            return
        print("File changes detected, terminatig...")
        stop_current_process()
        print("Restarting...\n\n\n")
        start_new_process()
    
    on_created = _on_file_change
    on_deleted = _on_file_change
    on_modified = _on_file_change
    on_moved = _on_file_change


event_handler = EventHandler()

observer = observers.Observer()
observer.schedule(event_handler, path.dirname(__file__), recursive=True)
observer.start()
start_new_process()

try:
    while observer.is_alive():
        observer.join(1)
finally:
    observer.stop()
    observer.join()
