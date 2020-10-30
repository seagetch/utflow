import contextlib

from .exceptions import Skip
from .task import Task

from logging import getLogger
logger = getLogger(__name__)


class TaskFlow:

    def __init__(self, *, start=None, end=None):
        self.start     = start
        self.end       = end
        self.started   = False
        self.ended     = False
        self.tasks     = 0
        self.context   = None
        self.last_task = None

        
    @contextlib.contextmanager
    def next(self, label = None, when = None):
        
        try:
            if label is None:
                label = self.tasks
                self.tasks += 1
            yield Task(self, label=label, when=when)
            
        except Skip as e:
            logger.debug(" %s"%str(e))
            pass
        
        
    def reset(self, start = None, end = None):
        
        self.start     = start
        self.end       = end
        self.started   = False
        self.ended     = False
        self.last_task = None