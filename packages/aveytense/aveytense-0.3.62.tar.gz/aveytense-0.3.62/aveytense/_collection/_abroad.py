"""
@lifetime >= 0.3.29 \\
© 2024-Present Aveyzan // License: MIT

This internal module has been established to extend possibilities of `abroad()` \\
function and its variations, put many abroad types there.

Not in use in public scope.
"""

import copy as _copy
import sys as _sys

from . import _extensions
from .. import util as _util # no overlap

__name__ = "aveytense._inaccessible"

_T = _extensions.TypeVar("_T")
_V1 = _extensions.TypeVar("_V1")
_V2 = _extensions.TypeVar("_V2")
_M = _extensions.TypeVar("_M")

ReckonType = _extensions.Union[
    _extensions.IO[_extensions.Any],
    _extensions.AVT_Iterable[_T],
    _extensions.ReckonOperable,
    _extensions.Sizeable
]
"""
@lifetime >= 0.3.25

Package of types, which are considered countable and satisfy type requirement \\
for function `reckon()`. To 0.3.26b3 also known as `SupportsCountables`.
"""
ReckonNGT = _extensions.Union[
    _extensions.IO,
    _extensions.Iterable,
    _extensions.ReckonOperable,
    _extensions.Sizeable
] # since 0.3.25, renamed from SupportsCountablesLackOfGeneric (0.3.26b3)

AbroadValue1 = _extensions.Union[int, float, complex, ReckonType[_T]] # >= 0.3.25 // renamed from SupportsAbroadValue1 (0.3.26b3)
AbroadValue2 = _extensions.Union[int, float, bool, ReckonType[_T]] # >= 0.3.25 // renamed from SupportsAbroadValue2 (0.3.26b3)
AbroadModifier = _extensions.Optional[AbroadValue1[_T]] # >= 0.3.25 // renamed from SupportsAbroadModifier (0.3.26b3)

# >= 0.3.25, lose of dict and defaultdict support, added frozenset, renamed from SupportsAbroadPackValues (0.3.26b3)
# 0.3.53: 'enumerate' is not subscriptable before Py3.9
AbroadPackType = _extensions.Union[_extensions.AVT_List[_T], _extensions.AVT_Tuple[_T, ...], _extensions.AVT_Deque[_T], _extensions.AVT_Set[_T], _extensions.AVT_Enumerate[_T], _extensions.AVT_FrozenSet[_T]]
AbroadVividType = _extensions.Union[ # >= 0.3.25 // renamed from SupportsAbroadVividValues (0.3.26)
    _extensions.AVT_Tuple[AbroadValue1[_V1]],
    _extensions.AVT_Tuple[AbroadValue1[_V1], AbroadValue2[_V2]],
    _extensions.AVT_Tuple[AbroadValue1[_V1], AbroadValue2[_V2], AbroadModifier[_M]]
]
AbroadMultiInitializer = _extensions.AVT_List[_extensions.AVT_List[_T]] # >= 0.3.25
AbroadConvectType = AbroadValue1[_T] # >= 0.3.25 // renamed from SupportsAbroadConvectValues (0.3.26b3)
AbroadLiveType = AbroadConvectType[_T] # >= 0.3.25 // renamed from SupportsAbroadLiveValues (0.3.26b3)

class _AbroadUnknownInitializer(_extensions.Generic[_T]):
    """@lifetime >= 0.3.29"""
    
    def __init__(self, seq: _extensions.AVT_Iterable[_T], v1: int, v2: int, m: int, /):
        
        import inspect
        
        if not isinstance(seq, _extensions.Iterable) or (type(v1), type(v2), type(m)) != (int, int, int):
            error = TypeError()
            raise error
        
        for e in seq:
            if not isinstance(e, int):
                error = TypeError()
                raise error
        
        _tmp = inspect.currentframe().f_back.f_lineno
        self.__frame = _tmp if type(_tmp) is int else -1
        self.__l = list(seq)
        self.__p = (v1, v2, m)
        
    def __iter__(self):
        
        return iter(self.__l)
    
    def __reversed__(self):
        """@lifetime >= 0.3.32"""
        
        return reversed(self.__l)
    
    def __str__(self):
        
        if len(self.__l) == 0:
            return "abroad( <empty> )"
        
        else:
            
            if self.__p == (0, 0, 0):
                return "abroad( <mixed> )"
            
            return "abroad({})".format(", ".join([str(e) for e in self.__p]))
            
    def __repr__(self):
        
        return "<<'{}.{}' object :: {}> defined in line {}>".format(__name__, type(self).__name__, self.__str__(), self.__frame)
    
    def __pos__(self):
        """
        @lifetime >= 0.3.28
        
        Returns sequence as a list. `+` can be claimed as "allow to change any items, this sequence can be updated"
        """
        return self.__l
    
    def __neg__(self):
        """
        @lifetime >= 0.3.28
        
        Returns sequence as a tuple. `-` can be claimed as "do not change any items, this sequence cannot be updated"
        """
        return tuple(self.__l)
    
    def __invert__(self):
        """
        @lifetime >= 0.3.28
        
        Returns sequence as a set. `~` can be claimed as "allow to change any items, this sequence can be updated, BUT items must be unique"
        """
        return set(self.__l)
    
    def __getitem__(self, key: int):
        """
        @lifetime >= 0.3.29. `self[key]`
        """
        try:
            return self.__l[key]
        
        except IndexError:
            error = IndexError("sequence out of range")
            raise error
        
    def __contains__(self, item: _T):
        """
        @lifetime >= 0.3.32. `item in self`
        """
        return item in self.__l
    
    def __add__(self, other: _extensions.Union[_extensions.AVT_Iterable[_T], _extensions.Self]):
        """
        @lifetime >= 0.3.32. `self + other`
        """
        if not isinstance(other, (_extensions.Iterable, type(self))):
            error = TypeError("expected an iterable or abroad() function result as a right operand")
            raise error
        
        # 1st statement: obvious certificate that this class has the __iter__
        # method, so it satisfies requirement for list constructor
        if (isinstance(other, type(self)) and len(list(other)) == 0) or (isinstance(other, _extensions.Iterable) and len(other) == 0):
            return self
        
        # this notation seems ugly since there is double invocation, but
        # necessary in case of inheritance, so code will type hint subclasses
        # objects as returned results. this notation is also here due to
        # refraining from using base class as a role of constructor - type
        # hinted will be object of base class, what might not be a good idea
        return type(self)(self.__l + [e for e in other], 0, 0, 0) 
    
    def __radd__(self, other: _extensions.Union[_extensions.AVT_Iterable[_T], _extensions.Self]):
        """
        @lifetime >= 0.3.32. `other + self`
        """
        if not isinstance(other, (_extensions.Iterable, type(self))):
            error = TypeError("expected an iterable or abroad() function result as a left operand")
            raise error
        
        if (isinstance(other, type(self)) and len(list(other)) == 0) or (isinstance(other, _extensions.Iterable) and len(other) == 0):
            return self
        
        return type(self)([e for e in other] + self.__l, 0, 0, 0)
    
    def __mul__(self, other: int):
        """
        @lifetime >= 0.3.32. `self * other`
        """
        if not isinstance(other, int) or (isinstance(other, int) and other < 1):
            error = TypeError("expected a non-negative integer as a right operand")
            raise error
        
        return type(self)(self.__l * other, self.__p[0], self.__p[1], self.__p[2])
    
    def __rmul__(self, other: int):
        """
        @lifetime >= 0.3.32. `other * self`
        """
        return self.__mul__(other)
    
    def __copy__(self):
        """
        @lifetime >= 0.3.34
        
        Returns shallow copy
        """
        return _copy.copy(self)
    
    def __deepcopy__(self):
        """
        @lifetime >= 0.3.34
        
        Returns deep copy
        """
        return _copy.deepcopy(self)
       
    @_util.finalproperty
    def params(self):
        """
        @lifetime >= 0.3.29
        
        Returns parameters as integers
        """
        return self.__p
    
class AbroadInitializer(_AbroadUnknownInitializer[int]): ... # >= 0.3.28

if __name__ == "__main__":
    error = RuntimeError("Import-only module")
    raise error