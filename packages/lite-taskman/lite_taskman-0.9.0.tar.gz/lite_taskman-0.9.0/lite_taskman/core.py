# -*- coding: utf-8 -*-

from collections import namedtuple
from datetime import datetime
from time import time
import os
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from threading import get_ident
from traceback import extract_tb

def _log(s):
    print(f'[{str(datetime.now())[:-3]}] {s}') # in millisecond

def _default_cb(name: str, task_done: int, task_all: int, 
                batch_done: int, batch_all: int, elapsed_sec: float):
    """
    Default progress callback.
    
    :param name:        Name of the task that just finished.
    :param task_done:   Count of unique tasks completed so far.
    :param task_all:    Total count of tasks submitted to the pool (dynamic).
    :param batch_done:  Sum of 'batch_size' for all completed tasks.
    :param batch_all:   Sum of 'batch_size' for all submitted tasks (dynamic).
    :param elapsed_sec: Seconds passed since the start of the 'process()' call.
    """
    batch_info = '' if batch_all == task_all else f'batch progress {batch_done}/{batch_all}, '
    _log(f'  -- Task "{name}" progress {task_done}/{task_all}, {batch_info}elapsed {int(elapsed_sec * 1000)}ms')

Task = namedtuple('Task', ['fn', 'args', 'kwargs', 'name', 'batch_size', 'extra'])
Result = namedtuple('Result', ['name', 'result', 'extra', 'error', 'traceback'])

class TaskMan:
    """
    A lightweight thread pool manager supporting dynamic task addition and streaming results.
    """
    
    def __init__(self, max_workers=0, progress_cb=_default_cb):
        """
        Initialize the TaskManager.
        
        :param max_workers: Number of threads. Defaults to os.cpu_count().
        :param progress_cb: Callback function triggered on each task completion.
            Expected signature: (name: str, task_done: int, task_all: int, batch_done: int, batch_all: int, elapsed_sec: float) -> None
        """
        self.thread_id = get_ident()
        self.max_workers = max_workers if max_workers > 0 else os.cpu_count()
        self.process_cb = progress_cb
        self.pool = None
        self.tasks = []
        self.queue = {}


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


    def shutdown(self):
        """Clean up resources and shutdown the thread pool."""
        if self.pool: 
            self.pool.shutdown()
            self.pool = None
        self.queue.clear()
        self.tasks.clear()


    def add(self, fn, *args, _tm_name=None, _tm_batch_size=1, _tm_extra=None, **kwargs):
        """
        Add a task to the preparation list.
        
        :param fn: Target function to execute.
        :param args: Positional arguments for fn.
        :param _tm_name: Custom name for the task.
        :param _tm_batch_size: Value to increment the batch counter by.
        :param _tm_extra: Metadata associated with this task.
        :param kwargs: Keyword arguments for fn.
        """
        if not self.thread_id == get_ident(): # ensure add() not called in worker thread
            raise Exception('TaskMan.add() must be called in the same thread as __init__')
        name = _tm_name or fn.__name__
        self.tasks.append(Task(fn, args, kwargs, name, _tm_batch_size, _tm_extra))


    def process(self):
        """
        An incremental generator that submits tasks and yields results as they complete.
        Supports adding new tasks during iteration.
        
        :yield: Result(name, result, extra, error, traceback)
        """
        if not self.tasks and not self.queue: 
            return
        if not self.pool: # lazy init pool
            self.pool = ThreadPoolExecutor(max_workers=self.max_workers)
        
        tm = time()
        ta, ba, td, bd = 0, 0, 0, 0
        while self.queue or self.tasks:
            if self.tasks:
                ta += len(self.tasks)
                ba += sum(t.batch_size for t in self.tasks)
                self.queue.update({self.pool.submit(t.fn, *t.args, **t.kwargs): t for t in self.tasks})
                self.tasks.clear()
            if self.queue:
                done, _ = wait(self.queue, return_when=FIRST_COMPLETED)
                for f in done:
                    t = self.queue.pop(f) # delete from queue
                    td += 1
                    bd += t.batch_size
                    try:
                        yield Result(t.name, f.result(), t.extra, None, None)
                    except Exception as e:
                        yield Result(t.name, None, t.extra, e, extract_tb(e.__traceback__))
                    finally:
                        self.process_cb(t.name, td, ta, bd, ba, time() - tm)
    

    def exec(self):
        """
        All-in-one execution: Start -> Process all -> Shutdown (automatically).
        
        :return: A list of all Result objects.
        """
        with self:
            return list(self.process())

