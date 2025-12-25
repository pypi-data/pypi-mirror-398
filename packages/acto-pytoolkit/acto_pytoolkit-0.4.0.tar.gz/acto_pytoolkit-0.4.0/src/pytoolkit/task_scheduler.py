import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class ScheduledTask:
    """Represents a scheduled job with a fixed interval."""

    interval: float
    function: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    _next_run: float = field(default_factory=lambda: time.time())
    _cancelled: bool = False

    def cancel(self) -> None:
        self._cancelled = True


class TaskScheduler:
    """Very small in process scheduler for recurring tasks.

    It is based on a background thread that periodically runs due tasks.
    This is intended for simple setups and does not replace a robust external scheduler.
    """

    def __init__(self, tick: float = 0.5, logger: Optional[logging.Logger] = None) -> None:
        self.tick = tick
        self._tasks: dict[str, ScheduledTask] = {}
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    def start(self) -> None:
        """Start the scheduler thread if it is not already running."""
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the scheduler thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join()

    def add_task(
        self,
        name: str,
        interval: float,
        function: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> ScheduledTask:
        """Add or replace a scheduled task.

        Parameters
        ----------
        name:
            Name of the task. If a task with the same name exists it will be replaced.
        interval:
            Interval in seconds between invocations.
        function:
            Callable to execute.
        """
        task = ScheduledTask(interval=interval, function=function, args=args, kwargs=kwargs)
        with self._lock:
            self._tasks[name] = task
        return task

    def remove_task(self, name: str) -> None:
        """Remove a task by name if it exists."""
        with self._lock:
            task = self._tasks.pop(name, None)
        if task:
            task.cancel()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            now = time.time()
            with self._lock:
                tasks_snapshot = dict(self._tasks)
            for name, task in tasks_snapshot.items():
                if task._cancelled:
                    continue
                if now >= task._next_run:
                    try:
                        task.function(*task.args, **task.kwargs)
                    except Exception as exc:
                        self.logger.exception(
                            "Error while executing scheduled task %s: %s", name, exc
                        )
                    task._next_run = now + task.interval
            time.sleep(self.tick)
