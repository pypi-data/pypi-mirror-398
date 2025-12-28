"""
**AveyTense Extensions**

@lifetime >= 0.3.26b3 \\
© 2024-Present Aveyzan // License: MIT \\
https://aveyzan.xyz/aveytense#aveytense.extensions

Similarly as `typing_extensions`, this module provides backports for Python types,
functions, classes and ABCs (especially generic).

About AVT types visit https://aveyzan.xyz/aveytense/glossary#avt_prefixed_types

This module occurred in many names:

- `aveytense.tcs` to 0.3.26rc2
- `aveytense.types_collection` during 0.3.26rc3 - 0.3.51
- `aveytense.types` during 0.3.52 - 0.3.56

Constants have been moved to separate submodule `aveytense.constants`.
"""

from __future__ import annotations

import collections.abc as _collections_abc
import collections as _collections
import hashlib as _hashlib
import sys as _sys
import typing as _typing

from ._collection._extensions import *
from ._collection._version import VERSION
from . import util as _util

NULL = type(None) # 0.3.26b3 (0.3.34 - type[None])
null = NULL # 0.3.41

_T = TypeVar("_T")

if False: # < 0.3.27rc1
    @deprecated("Deprecated since 0.3.27a3, use class 'aveytense.types_collection.ClassVar' instead.")
    def classvar(v: _T, /):
        """
        @lifetime >= 0.3.26b3 (experimental) \\
        @deprecated 0.3.27a3

        Transform variable in a class to a class variable.

        This will be valid only whether this function is \\
        invoked inside a class.
        Use it as:
        ```py \\
        class Example:
            test = classvar(96000) # has value 96000
        ```
        """
        class _t:
            _v: ClassVar[_T] = v
        return _t._v

    @deprecated("Deprecated since 0.3.26c3, use class 'aveytense.FinalVar' instead.")
    def finalvar(v: _T, /):
        """
        @lifetime >= 0.3.26b3 \\
        @deprecated 0.3.26c3 (use `aveytense.FinalVar` class-like instead)

        Use it as:
        ```py \\
        reassign_me = finalvar(96000) # has value 96000
        reassign_me += 3 # error
        ```
        """
        return _util.FinalVar(v)
    

# EnchantedBookQuantity = _lit[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36] ### >= 0.3.26b3; < 0.3.52

if False: # < 0.3.41
    
    
    FileMode = Literal[
        'r+', '+r', 'rt+', 'r+t', '+rt', 'tr+', 't+r', '+tr', 'w+', '+w', 'wt+', 'w+t', '+wt', 'tw+', 't+w', '+tw', 'a+', '+a', 'at+', 'a+t', '+at', 'ta+', 't+a', '+ta', 'x+', '+x', 'xt+',
        'x+t', '+xt', 'tx+', 't+x', '+tx', 'w', 'wt', 'tw', 'a', 'at', 'ta', 'x', 'xt', 'tx', 'r', 'rt', 'tr', 'U', 'rU', 'Ur', 'rtU', 'rUt', 'Urt', 'trU', 'tUr', 'Utr', 'rb+', 'r+b', '+rb',
        'br+', 'b+r', '+br', 'wb+', 'w+b', '+wb', 'bw+', 'b+w', '+bw', 'ab+', 'a+b', '+ab', 'ba+', 'b+a', '+ba', 'xb+', 'x+b', '+xb', 'bx+', 'b+x', '+bx', 'rb', 'br', 'rbU', 'rUb', 'Urb',
        'brU', 'bUr', 'Ubr', 'wb', 'bw', 'ab', 'ba', 'xb', 'bx'
    ] # 0.3.26b3
    FileOpener = AVT_Callable[[str, int], int] # 0.3.26b3
    TicTacToeBoard = AVT_List[AVT_List[str]] # 0.3.26b3

    AnySequenceForPick = Union[AVT_Sequence[_T], AVT_MutableSequence[_T], AVT_Uniqual[_T], AVT_MutableUniqual[_T]] # 0.3.26c3

    SequencePickType = Union[
        AVT_List[_T],
        AVT_Tuple[_T, ...],
        AVT_Set[_T],
        AVT_FrozenSet[_T],
        ListConvertible[_T]
    ] # 0.3.26c3

    SequencePickNGT = _uni[
        list,
        tuple,
        set,
        frozenset,
        Sequence,
        ListConvertible
    ] # 0.3.26c3

if False: # < 0.3.52
    
    VarLenHash = type(_hashlib.shake_256()) # it can appear as local hashlib._VarLenHash class in Python versions before 3.13 (0.3.41)
    "@lifetime >= 0.3.26rc3"

    BlakeHash = _hashlib.blake2b
    "@lifetime >= 0.3.26rc3"

    List = list # 0.3.26b3
    "@lifetime >= 0.3.26b3"

    if _sys.version_info >= (3, 9):
        Tuple = tuple # 0.3.26b3
        "@lifetime >= 0.3.26b3"
        
    else:
        Tuple = _typing.Tuple # 0.3.26b3
        "@lifetime >= 0.3.26b3"

    Deque = _collections.deque # 0.3.26b3
    "@lifetime >= 0.3.26b3"

    Dict = dict # 0.3.26b3
    "@lifetime >= 0.3.26b3"

    Bytes = bytes # 0.3.26b3
    "@lifetime >= 0.3.26b3"

    ByteArray = bytearray # 0.3.26b3
    "@lifetime >= 0.3.26b3"

    Filter = filter # 0.3.26b3
    "@lifetime >= 0.3.26b3"

    Type = type # 0.3.26b3
    "@lifetime >= 0.3.26b3"

    Zip = zip # 0.3.26b3
    "@lifetime >= 0.3.26b3"

    Slice = slice # 0.3.26c1
    "@lifetime >= 0.3.26rc1"

    Object = object
    "@lifetime >= 0.3.26rc3"

if False: # < 0.3.41 (if no removal version was provided, then all of these were removed in 0.3.41)
    
    class _FinalVar(NamedTuple, Generic[_T]):
        x: _T
    
    ModernReplace = _uni[list[_T], tuple[_T, ...], _T]
    # since 0.3.25, expected string; renamed from SupportsModernReplace (0.3.26b3)
    PickSequence = _uni[list[_T], tuple[_T, ...], set[_T], frozenset[_T], _collections.deque[_T], _collections_abc.Sequence[_T], _collections_abc.MutableSequence[_T]]
    # since 0.3.25, added support for Sequence and MutableSequence, renamed from SupportsPick (0.3.26b3)
    SanitizeMode = _lit[0, 1, 2, 3, 4, 5]
    # since 0.3.25, renamed from SupportsSanitizeMode (0.3.26b3)
    SupportsAbroadDivisor = _uni[int, float]
    # since 0.3.25; removed in 0.3.26b3, use FloatOrInteger instead
    ShuffleType = _uni[str, list[_T], _collections_abc.MutableSequence[_T]]
    # since 0.3.26rc1
    TypeOrFinalVarType = _uni[_T, _FinalVar[_T]]
    # since 0.3.26rc1
    
    __author__ = "Aveyzan <aveyzan@gmail.com>"
    "@lifetime >= 0.3.26rc3"
    __license__ = "MIT"
    "@lifetime >= 0.3.26rc3"
    __version__ = VERSION
    "@lifetime >= 0.3.26rc3"


if False: # < 0.3.46

    ProbabilityType = _uni[_T, list[_opt[_T]], tuple[_T, _opt[_T]], dict[_T, _opt[_T]], _collections.deque[_opt[_T]], set[_opt[_T]], frozenset[_opt[_T]]]
    # since 0.3.25, expected integer; renamed from SupportsProbabilityValuesAndFrequencies (0.3.26b3)
    

TenseVersionType = AVT_Tuple[_T, _T, _T]
# since 0.3.25, renamed from SupportsTenseVersion (0.3.26b3)

FloatOrInteger = Union[int, float] # since 0.3.25
_IntegerConvertible = Union[str, Buffer, IntegerConvertible, Indexable, Truncable] # since 0.3.26rc1
_FloatConvertible = Union[str, Buffer, FloatConvertible, Indexable] # since 0.3.26rc1
_ComplexConvertible = Union[complex, FloatConvertible, Indexable] # since 0.3.26rc1

if False: # < 0.3.48
    
    @deprecated("Deprecated since 0.3.41, will be removed on 0.3.48. Migrate to 'int' builtin instead")
    class Integer:
        """
        @lifetime >= 0.3.26b3
        
        Equivalent to `int`. Once instantiated, it returns \\
        integer of type `int`. (0.3.26c1)
        """
        def __new__(cls, x: _IntegerConvertible = ..., /):
            """
            @lifetime >= 0.3.26b3
            
            Equivalent to `int`. Once instantiated, it returns \\
            integer of type `int`. (0.3.26c1)
            """
            return int(x)
        
        def __instancecheck__(self, obj: object, /) -> TypeIs[int]:
            return isinstance(obj, int)

    @deprecated("Deprecated since 0.3.41, will be removed on 0.3.48. Migrate to 'float' builtin instead")
    class Float:
        """
        @lifetime >= 0.3.26b3
        
        Equivalent to `float`. Once instantiated, it returns \\
        number of type `float`. (0.3.26c1)
        """
        def __new__(cls, x: _FloatConvertible = ..., /):
            """
            @lifetime >= 0.3.26b3
            
            Equivalent to `float`. Once instantiated, it returns \\
            number of type `float`. (0.3.26c1)
            """
            return float(x)
        
        def __instancecheck__(self, obj: object, /) -> TypeIs[float]:
            return isinstance(obj, float)

    @deprecated("Deprecated since 0.3.41, will be removed on 0.3.48. Migrate to 'complex' builtin instead")
    class Complex:
        """
        @lifetime >= 0.3.26b3
        
        Equivalent to `complex`. Once instantiated, it returns \\
        number of type `complex`. (0.3.26c1)
        """
        def __new__(cls, r: _uni[ComplexConvertible, _ComplexConvertible] = ..., i: _ComplexConvertible = ..., /):
            """
            @lifetime >= 0.3.26b3
            
            Equivalent to `complex`. Once instantiated, it returns \\
            number of type `complex`. (0.3.26c1)
            """
            return complex(r, i)
        
        def __instancecheck__(self, obj: object, /) -> TypeIs[complex]:
            return isinstance(obj, complex)

    @deprecated("Deprecated since 0.3.41, will be removed on 0.3.48. Migrate to 'str' builtin instead")
    class String:
        """
        @lifetime >= 0.3.26b3
        
        Equivalent to `str`. Once instantiated, it returns \\
        string of type `str`. (0.3.26c1)
        """
        def __new__(cls, x: object = ..., /):
            """
            @lifetime >= 0.3.26b3
            
            Equivalent to `str`. Once instantiated, it returns \\
            string of type `str`. (0.3.26c1)
            """
            return str(x)
        
        def __instancecheck__(self, obj: object, /) -> TypeIs[str]:
            return isinstance(obj, str)

    @deprecated("Deprecated since 0.3.41, will be removed on 0.3.48. Migrate to 'bool' builtin instead")
    class Boolean:
        """
        @lifetime >= 0.3.26b3
        
        Equivalent to `bool`. Once instantiated, it returns \\
        boolean of type `bool`. (0.3.26c1)
        """
        def __new__(cls, x: object = ..., /):
            """
            @lifetime >= 0.3.26b3
            
            Equivalent to `bool`. Once instantiated, it returns \\
            boolean of type `bool`. (0.3.26c1)
            """
            return bool(x)
        
        def __instancecheck__(self, obj: object, /) -> TypeIs[bool]:
            return obj is True or obj is False

################ TypeScript References ################
# Remove these on 0.3.54.

if False: # < 0.3.54
    false = False
    "@lifetime >= 0.3.26rc3"
    true = True
    "@lifetime >= 0.3.26rc3"
    never = Never
    "@lifetime >= 0.3.26rc3"
    number = Union[int, float] # on JavaScript there is no 'complex' number type
    "@lifetime >= 0.3.26rc3"
    void = type(None)
    "@lifetime >= 0.3.26rc3"

__all__ = sorted([n for n in globals() if n[:1] != "_"])
"@lifetime >= 0.3.26rc1? Whole gamut of declarations written in `aveytense.extensions` module"

__all_deprecated__ = sorted([n for n in globals() if hasattr(globals()[n], "__deprecated__")])
"""
@lifetime >= 0.3.41

Returns all deprecated declarations within this module.
"""

__constants__ = [n for n in __all__ if n.isupper()]
"@lifetime >= 0.3.26rc3. All constants in `aveytense.extensions` module"

__non_constants__ = [n for n in __all__ if not n.isupper()]
"@lifetime >= 0.3.26rc3. All non-constants (functions, classes, type aliases) in `aveytense.extensions` module"

if False: # < 0.3.54
    __typing_util__ = sorted([
        # let me know if I missed some types from typing module!
        "Optional",
        "Union",
        "Callable",
        "Concatenate",
        "Pack" + " (alias to 'Concatenate')",
        "Annotated",
        "TypeAlias",
        "TypeAliasType",
        "TypeGuard",
        "TypeIs",
        "Unpack",
        "Any",
        "Final",
        "Literal",
        "LiteralString",
        "ClassVar",
        "Generic",
        "Protocol",
        "NoDefault",
        "NotRequired",
        "Required",
        "Self",
        "SpecVar (known as ParamSpec)",
        "SpecVarArgs" + " (known as ParamSpecArgs)",
        "SpecVarKwargs" + " (known as ParamSpecKwargs)",
        "NamedTuple",
        "NewType",
        "NoReturn",
        "ForwardRef",
    ])
    "@lifetime >= 0.3.26rc3. Utility types from `typing` module in `aveytense.types` module"

__abc__ = [n for n in __all__ if is_protocol(globals()[n]) or (isinstance(globals()[n], ABC) and n in _collections_abc.__dict__)]
"@lifetime >= 0.3.26rc3. ABCs (Abstract Base Classes) in `aveytense.extensions` module"

if __name__ == "__main__":
    error = RuntimeError("Import-only module")
    raise error
