from typing import Tuple, Dict, Any
from types import MethodType
import sys
from .core import functor, _Self


module = sys.modules[__name__]


ModuleType = type(module)


class FunctorModule(ModuleType):
    __slots__ = ("__call__", "_FunctorModule__module")
    __class__ = functor
    self = _Self()
    
    def __init__(self):
        super().__init__(module.__name__, module.__doc__)
        self.__call__ = MethodType(functor.__new__, functor)
        self.__module = module
    
    @property
    def __module__(self):
        return self.__module


new_module = FunctorModule()
sys.modules[__name__] = new_module


def __new__(cls, name: str, bases: Tuple[type, ...], namespace: Dict[str, Any], **kwargs: Any):
    if not bases or (len(bases) == 1 and bases[0] is object):
        return super().__new__(cls, name, bases, namespace, **kwargs)
    else:
        return type(name, tuple(base if not isinstance(base, cls) else functor for base in bases), namespace, **kwargs)


del FunctorModule.__init__
FunctorModule.__new__ = staticmethod(__new__)


del Tuple, Dict, Any, MethodType, sys, _Self, ModuleType, FunctorModule, __new__
new_module.__dict__.update(module.__dict__)
del new_module.new_module, new_module.module