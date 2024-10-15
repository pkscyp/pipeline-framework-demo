
from typing import List


class BusinessFunctionRegistry:
    fn_names = []
    fn_methods={}
    @classmethod
    def register(cls, name:List[str]=None):
        def decorator(fn):
            if name:
                for nm in name:
                    cls.fn_names.append(nm.upper())
                    cls.fn_methods[nm.upper()] = fn
            else: 
                fnm = fn.__name__.upper()  
                cls.fn_names.append(fnm)
                cls.fn_methods[fnm] = fn
            print('registed ')
            return fn
        return decorator
    
    @classmethod    
    def get_method(cls, name:str):
        if name not in cls.fn_names:
            return None
        return cls.fn_methods[name]
    
