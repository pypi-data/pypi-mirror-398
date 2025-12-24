import queue
import subprocess
import subprocess
import threading
from typing import Callable, Union


class ProcessLike:
    """A process-like object that can wrap either subprocess.Popen or a Python callable."""
    def __init__(self, process_or_callable: Union[subprocess.Popen, Callable]):
        if isinstance(process_or_callable, subprocess.Popen):
            self._process = process_or_callable
            self._is_callable = False
        else:
            self._callable = process_or_callable
            self._is_callable = True
            self._returncode = None
            self._output_queue = queue.Queue()
            self._thread = None
            self._start_callable()
    
    def _start_callable(self):
        """Start the callable in a thread and capture its output."""
        def run_callable():
            try:
                result = self._callable()
                if isinstance(result, str):
                    # If callable returns a string, treat each line as output
                    for line in result.splitlines():
                        self._output_queue.put(line + "\n")
                elif hasattr(result, '__iter__'):
                    # If callable returns an iterable, yield each item
                    for item in result:
                        self._output_queue.put(str(item) + "\n")
            except Exception as e:
                self._output_queue.put(f"Error: {e}\n")
            finally:
                # Put empty string to signal end of output
                self._output_queue.put("")
                self._returncode = 0
        
        self._thread = threading.Thread(target=run_callable, daemon=True)
        self._thread.start()
    
    def poll(self):
        """Return None if process is running, or returncode if done."""
        if self._is_callable:
            if self._thread and self._thread.is_alive():
                return None
            return self._returncode
        return self._process.poll()
    
    @property
    def stdout(self):
        """Return a file-like object for stdout."""
        if self._is_callable:
            return CallableFileLike(self._output_queue)
        return self._process.stdout
    
    @property
    def stderr(self):
        """Return a file-like object for stderr."""
        if self._is_callable:
            return CallableFileLike(self._output_queue)
        return self._process.stderr
    
    @property
    def returncode(self):
        """Return the process return code."""
        if self._is_callable:
            return self._returncode
        return self._process.returncode
    
    def terminate(self):
        """Terminate the process."""
        if self._is_callable:
            # For callables, we can't really terminate, but we can set returncode
            self._returncode = -1
        else:
            self._process.terminate()


class CallableFileLike:
    """A file-like object that reads from a queue."""
    
    # Sentinel to distinguish "no data yet" from "end of stream"
    _NO_DATA = object()
    
    def __init__(self, output_queue: queue.Queue):
        self._queue = output_queue
        self._closed = False
    
    def readline(self):
        """Read a line from the queue. Blocks until data available or EOF."""
        if self._closed:
            return ""
        try:
            # Block until we get actual data (with a reasonable timeout to allow checking)
            while not self._closed:
                try:
                    line = self._queue.get(timeout=0.5)
                    if line == "":  # Empty string signals end
                        self._closed = True
                        return ""
                    return line
                except queue.Empty:
                    # No data yet, keep waiting (don't return "" which would stop iteration)
                    continue
            return ""
        except Exception:
            return ""
    
    def close(self):
        """Close the file-like object."""
        self._closed = True


def create_process(launch_command_or_callable: Union[str, Callable]) -> ProcessLike:
    """Create a process-like object from either a command string or a Python callable."""
    if isinstance(launch_command_or_callable, str):
        # It's a command string - use subprocess
        process = subprocess.Popen(
            launch_command_or_callable.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1,
        )
        return ProcessLike(process)
    else:
        # It's a callable - wrap it
        return ProcessLike(launch_command_or_callable)