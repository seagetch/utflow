import inspect
import pickle

class Context(object):

    
    def __init__(self, **kwargs):

        for k, v in kwargs.items():
            self.__dict__[k] = v


    def __lshift__(self, obj):

        if isinstance(obj, dict):
            for k,v in obj.items():
                if k != "__parent__":
                    self.__dict__[str(k)] = v

        elif isinstance(obj, type(self)):
            for k,v in obj.__dict__.items():
                if k != "__parent__":
                    self.__dict__[str(k)] = v

        else:
            self._ = obj

        return self


    def __rshift__(self, obj):

        if callable(obj):
            params = inspect.signature(obj).parameters

            if "_" in self.__dict__:
                if isinstance(self._, list):
                    args = self._
                else:
                    args = [self._]
            else:
                args = []

            if len(args) > len(params):
                args = args[0:len(params)]

            kwargs = {}
            for i, (name, p) in enumerate(params.items()):
                if p.kind == inspect.Parameter.VAR_KEYWORD:
                    for k,v in self.__dict__.items():
                        kwargs[k] = v
                    break
                if i < len(args):
                    continue
                if name in self.__dict__:
                    kwargs[name] = self.__dict__[name]
                elif p.kind == inspect.Parameter.VAR_POSITIONAL:
                    continue
                elif p.default is inspect.Parameter.empty and i >= len(args):
                    raise Exception("parameter '%s' doesn't exist in %s"%(name, self))

            response = type(self)()
            if "__parent__" in self.__dict__:
                response.__reset__(self.__parent__)
            response << obj(*args, **kwargs)
            return response

        elif isinstance(obj, type(self)):
            obj << self
            return obj

        elif isinstance(obj, dict):
            for k,v in self.__dict__.items():
                obj[str(k)] = v
            return obj

        return None


    def __call__(self, **kwargs):
        
        self << kwargs
        return self


    def __getattr__(self, name):
        
        try:
            if "__parent__" in self.__dict__:
                return getattr(self.__parent__, name)
        except AttributeError:
            pass
        
        raise AttributeError(name)

        
    def __reset__(self, parent = None):
        
        if "__parent__" in self.__dict__:
            del(self.__parent__)
        if parent:
            self.__parent__ = parent
        return self


    def __transfer__(self):
        
        if "__parent__" in self.__dict__:
            for k, v in self.__dict__.items():
                if k != "__parent__":
                    self.__parent__.__dict__[k] = v
            self.__dict__.clear()


    def __dump__(self, f):
        
        parent = None
        
        if "__parent__" in self.__dict__:
            parent = self.__parent__
            self.__reset__()
        
        pickle.dump(self, f)
        
        self.__reset__(parent)