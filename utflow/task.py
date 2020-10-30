import os
import contextlib
import pickle
import uuid

from .context import Context
from .exceptions import Skip


TASKFLOW_DIR = os.environ.get("TASKFLOW_DIR") or os.path.join(os.getcwd(), ".utflow")


from logging import getLogger
logger = getLogger(__name__)


class Task:
    
    
    def __init__(self, flow, label, when=None):
        
        self.flow  = flow
        self.label = label
        self.when  = when

        
    def generate_filepath(self, label):
        
        return os.path.join(TASKFLOW_DIR, "state-%s.pickle"%label)

    
    def load_state(self):
        
        if self.flow.last_task is None:
            self.flow.context = Context()
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
        if os.path.exists(dest_filepath):
            os.remove(dest_filepath)
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
            raise Skip("Skipped task '%s'"%self.label)
            
        if not self.flow.context:
            self.flow.context = Context()
        
        if callable(self.when):
            result = self.when(self.flow.context)
            if not result:
                self.duplicate_state()
                self.flow.last_task = self.label
                raise Skip("Conditionally skipped task '%s'"%self.label)

        yield self.flow.context

        self.save_state()
        self.flow.last_task = self.label
