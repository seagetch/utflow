import contextlib

from .exceptions import Skip
from .task import Task, ProcessLocalTask

from logging import getLogger
logger = getLogger(__name__)


class TaskFlow:

    def __init__(self, *, start=None, end=None, context=None):

        self.start     = start
        self.end       = end
        self.started   = False
        self.ended     = False
        self.tasks     = 0
        self.context   = None
        self.last_task = None
        
        self.session_context = context

        
    def _task(self, label = None, *, when = None, task_class = Task):
        if label is None:
            label = self.tasks
            self.tasks += 1
        yield task_class(self, label=label, when=when)


    @contextlib.contextmanager
    def init(self):
        try:
            for context in self._task(label=None, task_class=ProcessLocalTask):
                yield context
        except Skip as e:
            logger.debug(" %s"%str(e))

        
    @contextlib.contextmanager
    def next(self, label = None, *, when = None):
        try:
            for context in self._task(label=label, when=when):
                yield context
        except Skip as e:
            logger.debug(" %s"%str(e))

        
    def _start(self, label = None, *, when = None, task_class = Task):
        def decorator(func):
            assert(callable(func))
            if label:
                local_label = label
            else:
                local_label = func.__name__
            task = task_class(self, label=local_label, when=when)
            try:
                with task.start() as _:
                    return func(_)
            except Skip as e:
                logger.debug(" %s"%str(e))

        return decorator
    

    def start_next(self, label = None, *, when = None):
        return self._start(label=label, when=when)
    

    def start_init(self):
        return self._start(label=None, when=None, task_class=ProcessLocalTask)


    def reset(self, start = None, end = None):

        self.start     = start
        self.end       = end
        self.started   = False
        self.ended     = False
        self.tasks     = 0
        self.context   = None
        self.last_task = None
