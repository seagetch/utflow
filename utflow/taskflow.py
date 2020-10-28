import contextlib
import os
import pickle
import uuid
from logging import getLogger

logger = getLogger(__name__)

TASKFLOW_DIR = os.environ.get("TASKFLOW_DIR") or os.path.join(os.getcwd(), ".utflow")

class TaskFlow:

    def __init__(self, *, start=None, end=None):
        self.start   = start
        self.end     = end
        self.started = False
        self.ended   = False
        self.tasks   = 0
        self.context = None
        self.last_task = None

        
    class Skip(Exception):
        
        def __init__(self, msg):
            super(Exception, self).__init__(msg)

            
    class Task:

        class Context(object):
            pass

        
        def __init__(self, flow, label, when=None):
            self.flow  = flow
            self.label = label
            self.when  = when

            
        def generate_filepath(self, label):
            return os.path.join(TASKFLOW_DIR, "state-%s.pickle"%label)

        
        def load_state(self):
            if self.flow.last_task is None:
                self.flow.context = type(self).Context()
            else:
                filepath = self.generate_filepath(self.flow.last_task)
                if os.path.exists(filepath):
                    logger.debug("Load state of previous task '%s'"%self.flow.last_task)
                    try:
                        with open(filepath, "rb") as f:
                            self.flow.context = pickle.load(f)
                    except EOFError:
                        pass


        def save_state(self):
            
            logger.debug("Dump state of task '%s'"%self.label)
            
            filepath = self.generate_filepath(self.label)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "wb") as f:
                pickle.dump(self.flow.context, f)

                
        def duplicate_state(self):
            
            logger.debug("Duplicate state of task '%s' as '%s'"%(self.flow.last_task, self.label))
            
            src_filepath  = self.generate_filepath(self.flow.last_task)
            dest_filepath = self.generate_filepath(self.label)
            os.symlink(src_filepath, dest_filepath)
            
            
        @contextlib.contextmanager
        def start(self):
            
            if not self.flow.ended and (not self.flow.start or self.flow.start == self.label):
                if not self.flow.started:
                    self.load_state()
                self.flow.started = True

            if self.flow.end and self.flow.end == self.label:
                self.flow.started = False
                self.flow.ended   = True
            
            if not self.flow.started or self.flow.ended:
                self.flow.last_task = self.label
                raise TaskFlow.Skip("Skipped task '%s'"%self.label)
                
            if not self.flow.context:
                self.flow.context = type(self).Context()
            
            if callable(self.when):
                result = self.when(self.flow.context)
                if not result:
                    self.duplicate_state()
                    self.flow.last_task = self.label
                    raise TaskFlow.Skip("Conditionally skipped task '%s'"%self.label)

            yield self.flow.context

            self.save_state()
            self.flow.last_task = self.label

    
    @contextlib.contextmanager
    def next(self, label = None, when = None):
        
        try:
            if label is None:
                label = self.tasks
                self.tasks += 1
            yield TaskFlow.Task(self, label=label, when=when)
            
        except TaskFlow.Skip as e:
            logger.debug(" %s"%str(e))
            pass
        
        
    def reset(self, start = None, end = None):
        
        self.start   = start
        self.end     = end
        self.started = False