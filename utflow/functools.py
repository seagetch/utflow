import inspect

class LazyBoundFunction(object):
    def __init__(self, func, *args, **kwargs):
        if not callable(func):
            raise Exception("func must be callable.")
        params = inspect.signature(func).parameters
        self.func   = func
        self.args   = list(args)
        self.params = list(params.keys())
        var_keyword = [p for name, p in params.items() if p.kind == inspect.Parameter.VAR_KEYWORD]
        self.has_var_keyword = len(var_keyword) > 0
        
        if not self.has_var_keyword:
            self.kwargs = {}
            for k,v in kwargs.items():
                if k in self.params:
                    self.kwargs[k] = v
                    
        else:
            self.kwargs = kwargs
        
    def __call__(self, *args, **kwargs):
        call_args = list(args) + self.args
        call_kwargs = self.kwargs
        
        arg_names   = self.params[0:len(call_args)]
        kwarg_names = self.params[len(call_args):]
        
        if not self.has_var_keyword:
            for k,v in kwargs.items():
                if k in arg_names:
                    call_args[arg_names.index(k)] = v
                elif k in kwarg_names:
                    call_kwargs[k] = v
        else:
            for k,v in kwargs.items():
                if k in arg_names:
                    call_args[arg_names.index(k)] = v
                else:
                    call_kwargs[k] = v
        return self.func(*call_args, **call_kwargs)
    
    def __name__(self):
        return self.func.__name__

def partial_lazy(func, *args, **kwargs):
    return LazyBoundFunction(func, *args, **kwargs)