import inspect

class Context(object):
    
    
    def __lshift__(self, obj):
        
        if isinstance(obj, dict):
            for k,v in obj.items():
                self.__dict__[str(k)] = v
        
        elif isinstance(obj, type(self)):
            for k,v in obj.__dict__.items():
                self.__dict__[str(k)] = v
        
        else:
            self._ = obj
        
        return self
    
    
    def __rshift__(self, obj):
        
        if callable(obj):
            params = inspect.signature(obj).parameters
            args = self._ if "_" in self.__dict__ and isinstance(self._, list) else []
            kwargs = {}
            for i, (name, p) in enumerate(params.items()):
                if name in self.__dict__:
                    kwargs[name] = self.__dict__[name]
                elif p.default is inspect.Parameter.empty and i >= len(args):
                    raise Exception("parameter '%s' doesn't exist in %s"%(name, self))
            response = type(self)()
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
