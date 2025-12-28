from typing import overload, Any, Union
from types import FunctionType, MethodType
from functools import partial
import inspect
from typing_extensions import Self
from .utils.proxy import ProxyGlobals


class _Self:
    def __get__(self, *_):
        frame = inspect.currentframe().f_back
        while frame:
            value = frame.f_globals.get(_Self)
            if value is not None:
                return value
            frame = frame.f_back
        raise RuntimeError("'functor.self' can only be accessed inside a 'functor' decorated function without 'bound'")


class functor:
    """
    This :class:`functor` acts as a decorator or a constructor for an instance of :class:`FunctionType`
    or :class:`functor` that contains :attr:`__code__` in principle. An object that implements :attr:`__call__`
    may not be simply used. Please decorate :attr:`__call__` when defining the class of that object. This means
    when using other decorators, this :class:`functor` may be firstly used since it returns a function that
    contains :attr:`__code__`.
    
    Args:
        function (Union[FunctionType, functor]): the function that will become a :class:`functor` object, which
            should contains :attr:`__code__`
        bound (bool): whether to bind the first argument of the function to the current :class:`functor` instance.
            Default: False
    
    Returns:
        output (functor): the :class:`functor` object from the given :attr:`function`
    
    Examples:
        >>> @functor
        ... def my_function():
        ...     return functor.self
        >>> 
        >>> my_function()
        <function my_function at 0x10e5de5f0>
    """
    
    __slots__ = ("__call__", "__repr__")
    self: Self = _Self()
    
    @overload
    @staticmethod
    def __new__(cls, function: Union[FunctionType, Self], *, bound: bool = False) -> Self:
        ...
    
    @staticmethod
    def __new__(cls, function: Union[FunctionType, Self, None] = None, *, bound: bool = False) -> Self:
        if function is None:
            return partial(cls.__as_functor__, bound=bound) # decorator with arguments
        else:
            return cls.__as_functor__(function, bound=bound)
    
    @classmethod
    def __as_functor__(cls, function: Union[FunctionType, Self], *, bound: bool = False) -> Self:
        if type(function) is cls:
            return function
        else:
            instance = super().__new__(cls)
            
            if bound:
                instance.__call__ = MethodType(function, instance)
                instance.__repr__ = lambda: repr(function)
                return instance
            else:
                method_self = None
                if isinstance(function, cls):
                    function = function.__call__
                    if isinstance(function, MethodType):
                        method_self = function.__self__
                        function = function.__func__
                
                function_globals = function.__globals__
                if _Self in function_globals:
                    return function
                
                try:
                    code = function.__code__
                except AttributeError:
                    raise ValueError("'function' should contain '__code__' when 'bound' is False")
                new_globals = ProxyGlobals(function_globals, [(_Self, instance)])
                new_function = FunctionType(
                    code,
                    new_globals,
                    function.__name__,
                    function.__defaults__,
                    function.__closure__
                )
                new_function.__kwdefaults__ = function.__kwdefaults__
                new_function.__qualname__ = function.__qualname__
                new_function.__module__ = function.__module__
                new_function.__doc__ = function.__doc__
                
                if method_self is not None:
                    new_function = MethodType(new_function, method_self)
                
                instance.__call__ = new_function
                instance.__repr__ = lambda: repr(instance.__call__)
                return instance
    
    def __get__(self, instance, _) -> MethodType:
        if instance is None:
            return self
        return MethodType(self, instance)
    
    def __getattr__(self, name: str) -> Any:
        return getattr(self.__call__, name)
    
    @property
    def __func__(self) -> FunctionType:
        return self.__call__