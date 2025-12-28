from typing import Union, Dict, Any, Iterable, Tuple, Hashable, KeysView, ValuesView, ItemsView, Iterator
from itertools import chain
from typing_extensions import Self


class ProxyGlobals(dict):
    @staticmethod
    def __new__(cls, globals: Union[Dict[Hashable, Any], Self], iterable: Iterable[Tuple[Hashable, Any]] = ()) -> Self:
        if isinstance(globals, ProxyGlobals):
            super(ProxyGlobals, globals).update(iterable)
            return globals
        instance = super().__new__(cls)
        try:
            other = globals
            globals = other.__globals__
            proxy = other.__proxy__
            super(ProxyGlobals, instance).update(chain(proxy.items(), iterable))
        except AttributeError:
            super(ProxyGlobals, instance).__init__(iterable)
        instance.__globals = globals
        return instance
    
    def __init__(self, *args, **kwargs):
        ...
    
    @property
    def __globals__(self) -> Dict[Hashable, Any]:
        return self.__globals
    
    @property
    def __proxy__(self):
        return super()
    
    def __getitem__(self, key: Hashable) -> Any:
        try:
            return self.__globals[key]
        except KeyError:
            return super().__getitem__(key)
    
    def __setitem__(self, key: Hashable, value):
        self.__globals[key] = value
    
    def __delitem__(self, key: Hashable):
        del self.__globals[key]
    
    def __len__(self) -> int:
        return len(self.__globals)
    
    def __contains__(self, key: Hashable) -> bool:
        return (key in self.__globals) or super().__contains__(key)

    def get(self, key: Hashable, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default
    
    def update(self, *args, **kwargs):
        self.__globals.update(*args, **kwargs)
    
    def copy(self) -> Self:
        instance = super().__new__(type(self))
        super(ProxyGlobals, instance).__init__(super().items())
        instance.__globals = self.__globals
        return instance
    
    def keys(self) -> KeysView[Hashable]:
        return self.__globals.keys()
    
    def values(self) -> ValuesView[Any]:
        return self.__globals.values()
    
    def items(self) -> ItemsView[Hashable, Any]:
        return self.__globals.items()
    
    def pop(self, key: Hashable, *args, **kwargs) -> Any:
        return self.__globals.pop(key, *args, **kwargs)
    
    def __iter__(self) -> Iterator[Hashable]:
        return iter(self.__globals)
    
    def __reversed__(self) -> Iterator[Hashable]:
        return reversed(self.__globals)
    
    def __eq__(self, value: object) -> bool:
        proxy, globals = _split_proxy_globals(value)
        result = self.__globals.__eq__(globals)
        if proxy is not None:
            result &= super().__eq__(dict(proxy.items()))
        return result
    
    def __or__(self, value: Dict[Hashable, Any]) -> Self:
        proxy, globals = _split_proxy_globals(value)
        globals = self.__globals.__or__(globals)
        if proxy is None:
            proxy = {}
        else:
            proxy = super().__or__(dict(proxy.items()))
        return self.__new__(type(self), globals, proxy.items())

    def __ror__(self, value: Dict[Hashable, Any]) -> Self:
        proxy, globals = _split_proxy_globals(value)
        globals = self.__globals.__ror__(globals)
        if proxy is None:
            proxy = {}
        else:
            proxy = super().__ror__(dict(proxy.items()))
        return self.__new__(type(self), globals, proxy.items())

    def __ior__(self, value: Dict[Hashable, Any]) -> Self:
        proxy, globals = _split_proxy_globals(value)
        self.__globals.__ior__(globals)
        if proxy is not None:
            super().__ior__(dict(proxy.items()))
        return self


def _split_proxy_globals(object: Dict[Hashable, Any]) -> Tuple[Any, Dict[Hashable, Any]]:
    try:
        proxy = object.__proxy__
        globals = object.__globals__
        return proxy, globals
    except AttributeError:
        return None, object