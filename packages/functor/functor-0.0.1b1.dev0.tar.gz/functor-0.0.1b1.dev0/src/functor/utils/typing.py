from typing_extensions import *
from typing import *
from ..core import functor


class FunctorType: ...
FunctorType = TypeVar('FunctorType', bound=functor)
del functor