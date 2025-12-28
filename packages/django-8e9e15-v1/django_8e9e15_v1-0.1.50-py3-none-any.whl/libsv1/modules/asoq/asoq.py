import atexit
import multiprocessing
import importlib
import os
import logging
from multiprocessing.managers import BaseManager
from typing import Callable, Optional, Any

logger = logging.getLogger(__name__)
_manager: Optional[BaseManager] = None
_shared_queue: Optional[multiprocessing.Queue] = None
_asoq_instance: Optional['InMemoryAsoq'] = None
_worker_process: Optional[multiprocessing.Process] = None

class TaskProxy:
    def __init__(self, func: Callable):
        self.func = func
        self.task_name = f"{func.__module__}.{func.__name__}"
        self.__name__ = func.__name__
        self.__module__ = func.__module__

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def delay(self, **kwargs: Any) -> None:
        queue = get_asoq_queue()
        logger.debug("Task '%s' enqueued from PID %d.", self.task_name, os.getpid())
        queue.put((self.task_name, kwargs))


class InMemoryAsoq:
    def __init__(self, queue: multiprocessing.Queue):
        self._queue = queue

    def run_worker(self):
        logger.info("Worker process started with PID: %d", os.getpid())
        while True:
            task_name = None
            try:
                task_name, kwargs = self._queue.get()
                if task_name == "__STOP__":
                    break
                module_path, func_name = task_name.rsplit('.', 1)
                module = importlib.import_module(module_path)
                task_func = getattr(module, func_name)
                task_func(**kwargs)
            except Exception:
                logger.exception(
                    "An error occurred in the worker process while processing task '%s'.",
                    task_name or "unknown"
                )

def get_asoq_queue() -> multiprocessing.Queue:
    global _asoq_instance, _manager, _shared_queue
    if _asoq_instance is None:
        _manager = multiprocessing.Manager()
        _shared_queue = _manager.Queue()
        _asoq_instance = InMemoryAsoq(queue=_shared_queue)
    return _shared_queue


def task() -> Callable[[Callable], TaskProxy]:
    def decorator(func: Callable) -> TaskProxy:
        return TaskProxy(func)
    return decorator


def _run_worker_process(queue: multiprocessing.Queue):
    worker_asoq = InMemoryAsoq(queue=queue)
    worker_asoq.run_worker()


def start_worker():
    global _worker_process
    if _worker_process is not None and _worker_process.is_alive():
        return

    queue_for_worker = get_asoq_queue()
    _worker_process = multiprocessing.Process(target=_run_worker_process, args=(queue_for_worker,))
    _worker_process.start()
    atexit.register(_cleanup_worker)


def _cleanup_worker():
    if _worker_process and _worker_process.is_alive():
        logger.info("Terminating Asoq worker process...")
        try:
            get_asoq_queue().put(("__STOP__", {}))
            _worker_process.join(timeout=2)
        finally:
            if _worker_process.is_alive():
                _worker_process.terminate()
                _worker_process.join(timeout=1)

logger.addHandler(logging.NullHandler())