"""
@lifetime >= 0.3.26rc3 \\
© 2024-Present Aveyzan // License: MIT

Core of `aveytense.extensions`; import this module instead
"""

# Table of supported Python versions by 'typing_extensions' (starting with Python 3.6, stats for 'typing_extensions' 4.15.0):
#
# | PY   | FIRST   | LAST
# | ---- | ------- | -------
# | 3.6  | 3.6.2   | 4.1.1 (< 4.2.0)
# | 3.7  | 3.7.4   | 4.7.1 (< 4.8.0)
# | 3.8  | 3.7.4.2 | 4.13.2 (< 4.14.0)
# | 3.9  | 3.7.4.2 | -
# | 3.10 | 3.10.0  | -
# | 3.11 | 4.5.0   | -
# | 3.12 | 4.7.0   | -
# | 3.13 | 4.12.0  | -
# | 3.14 | 4.14.0  | -

# LAST MICRO RELEASES FOR PYTHON 3.6 - 3.12 (* indicates predicted)
#
# | PY   | BUGFIX  | SECURITY |
# | ---- | ------- | -------- |
# | 3.6  | 3.6.8   | 3.6.15   |
# | 3.7  | 3.7.8   | 3.7.17   |
# | 3.8  | 3.8.10  | 3.8.20   |
# | 3.9  | 3.9.13  | 3.9.23   |
# | 3.10 | 3.10.11 | 3.10.18* |
# | 3.11 | 3.11.9  | 3.11.13* |
# | 3.12 | 3.12.10 | 3.12.11* |

from __future__ import annotations
from ._exceptions import _ErrorHandler as _E

### IMPORTS FOR PY3.6+ ###

from abc import (
    # 0.3.44
    ABC as ABC, 
    ABCMeta as ABCMeta,
    abstractmethod as abstractmethod
)
from array import (
    # 0.3.37
    array as array, 
    ArrayType as ArrayType
)
from ast import (
    # 0.3.44
    Expression as Expression, 
    Module as Module,
    Interactive as Interactive,
    # 0.3.54
    AST as AST
)
from collections import (
    # 0.3.37
    ChainMap as ChainMap, 
    Counter as Counter,
    defaultdict as defaultdict,
    deque as deque,
    OrderedDict as OrderedDict,
    # 0.3.44
    UserDict as UserDict,
    UserList as UserList,
    namedtuple as namedtuple,
    UserString as UserString
)
from collections.abc import (
    # < 0.3.50
    AsyncGenerator as AsyncGenerator,
    AsyncIterable as AsyncIterable,
    AsyncIterator as AsyncIterator,
    Awaitable as Awaitable,
    Callable as Callable,
    Collection as Collection,
    Container as Container,
    Coroutine as Coroutine,
    Generator as Generator,
    Hashable as Hashable,
    ItemsView as ItemsView,
    Iterable as Iterable,
    Iterator as Iterator,
    KeysView as KeysView,
    Mapping as Mapping,
    MappingView as MappingView,
    MutableMapping as MutableMapping,
    MutableSequence as MutableSequence,
    MutableSet as MutableUniqual,
    Reversible as Reversible,
    Sequence as Sequence,
    Set as Uniqual, # Naming to this to prevent ambiguity with typing.Set alias
    Sized as Sized,
    ValuesView as ValuesView
)
from contextlib import (
    # 0.3.53
    AbstractAsyncContextManager as AsyncContextManager, # typo found in 0.3.55a2
    AbstractContextManager as ContextManager,
)
from dataclasses import dataclass as dataclass # 0.3.37
from decimal import Decimal # 0.3.60
from enum import EnumMeta as EnumMeta # 0.3.26rc1
from functools import (
    # 0.3.26
    partial as partial,
    # 0.3.37
    cached_property as cachedproperty, 
    partialmethod as partialmethod,
    singledispatchmethod as singledispatchmethod,
    lru_cache as lru_cache,
    singledispatch as singledispatch,
    # 0.3.54
    lru_cache as lruCache,
    singledispatch as singleDispatch
)
from importlib import (
    # 0.3.44
    import_module as import_module,
    # 0.3.54
    import_module as importModule
)
from inspect import (
    # 0.3.26rc3
    ArgInfo as ArgInfo, 
    Arguments as Arguments,
    Attribute as Attribute,
    BlockFinder as BlockFinder,
    BoundArguments as BoundArguments,
    ClosureVars as ClosureVars,
    FrameInfo as FrameInfo,
    FullArgSpec as FullArgSpec,
    Parameter as Parameter,
    Signature as Signature,
    Traceback as Traceback,
)
from numbers import Rational as _Rational # 0.3.60
from os import PathLike as PathLike # 0.3.52
from re import (
    # 0.3.26
    Match as Match, 
    Pattern as Pattern,
    # 0.3.60
    RegexFlag as RegexFlag # only used for 'FlagsType'
)
from types import ( # Imports from 0.3.51 are used for builtin function inspection via ~.util.ParamVar.
    # 0.3.26rc1/0.3.34?
    coroutine as coroutine,
    new_class as new_class,
    # 0.3.26rc3
    new_class as newClass,
    ModuleType as ModuleType,
    TracebackType as TracebackType,
    CodeType as CodeType,
    # 0.3.37
    FunctionType as FunctionType,
    FrameType as FrameType,
    MethodType as MethodType,
    # 0.3.42
    MappingProxyType as MappingProxyType,
    # 0.3.43
    DynamicClassAttribute as DynamicClassAttribute,
    # 0.3.44
    AsyncGeneratorType as AsyncGeneratorType, # >=Py3.6
    CoroutineType as CoroutineType, # >=Py3.5
    # 0.3.51
    BuiltinFunctionType as BuiltinFunctionType,
    # 0.3.53
    SimpleNamespace as SimpleNamespace, 
    # 0.3.54
    prepare_class as prepare_class,
    prepare_class as prepareClass,
)
from typing import (
    # 0.3.26rc1
    no_type_check as noTypeCheck,
    # 0.3.37
    get_type_hints as get_type_hints, 
    no_type_check as no_type_check,
    # 0.3.44
    cast as cast,
    # 0.3.54
    get_type_hints as getTypeHints
)
from uuid import UUID as UUID # 0.3.26rc3
import sys as _sys

__name__ = "aveytense.extensions"

# In this part of the code, we are retrieving currently used version of 'typing_extensions', and formalize the version
# like sys.version_info:
class TypingExtensionsVersionInfo:
    """
    @lifetime >= 0.3.54
    
    Version info for `typing_extensions`
    """
    
    def __init__(self):
        
        if _sys.version_info >= (3, 8):
            from importlib.metadata import version 
        else: # Py<3.8 will require pypi module importlib_metadata
            from importlib_metadata import version
        
        _typing_ext_string_ver_ = version("typing_extensions")
        
        # There I am believing devs won't use the epoch version component.
        # Every version since version 4.0.0 have 3 components, unlike before 4.0.0
        # some can have 4 (last being submicro)
        _split_components_ = _typing_ext_string_ver_.split(".")
        
        self.major = int(_split_components_[0])
        self.minor = int(_split_components_[1])
        
        _search_ = ("a", "b", "rc")
        _submicro_ = len(_split_components_) == 4
        
        if not _submicro_:
            self.submicro = 0
        else:
            self.micro = int(_split_components_[2])
            
        _search_found_ = False
        
        for search in _search_:
                
            if search in _split_components_[-1]:
                
                _search_found_ = True
                _split_id_ = _split_components_[-1].split(search)
                
                if not _submicro_:
                    self.micro = int(_split_id_[0])
                else:
                    self.submicro = int(_submicro_[0])
                
                if search == "a":
                    self.releaselevel = ("alpha", 1)
                    
                elif search == "b":
                    self.releaselevel = ("beta", 2)
                    
                else:
                    self.releaselevel = ("candidate", 3)
                    
                self.serial = int(_split_id_[1])
                
                break
                
        if not _search_found_:
            
            if not _submicro_:
                self.micro = int(_split_components_[-1])
            else:
                self.submicro = int(_split_components_[-1])
                
            self.releaselevel = ("final", 4)
            self.serial = 0

    def __gt__(self, other: tuple):
        
        if not isinstance(other, tuple):
            return False
        
        if len(other) == 1:
            return other < (self.major,)
        
        elif len(other) == 2:
            return other < (self.major, self.minor)
        
        elif len(other) == 3:
            return other < (self.major, self.minor, self.micro)
        
        elif len(other) == 4:
            
            if self.submicro == 0:
                return other < (self.major, self.minor, self.micro, self.releaselevel[1])
            else:
                return other < (self.major, self.minor, self.micro, self.submicro)
            
        return False
    
    def __lt__(self, other: tuple):
        
        if not isinstance(other, tuple):
            return False
        
        return not self.__gt__(other) and other != (self.major, self.minor, self.micro, self.releaselevel[1] if self.submicro == 0 else self.submicro)[:len(other)]
    
    def __ge__(self, other: tuple):
        
        if not isinstance(other, tuple):
            return False
        
        return not self.__lt__(other)
    
    def __le__(self, other: tuple):
        
        if not isinstance(other, tuple):
            return False
        
        return not self.__gt__(other)
    
    def __eq__(self, other: tuple):
        
        if not isinstance(other, tuple):
            return False
        
        return not self.__gt__(other) and not self.__lt__(other)
    
    def __ne__(self, other: tuple):
        
        if not isinstance(other, tuple):
            return False
        
        return not self.__eq__(other)
    
    def __str__(self):
        
        if self.releaselevel[1] == 1:
            _level_ = "a"
        elif self.releaselevel[1] == 2:
            _level_ = "b"
        elif self.releaselevel[1] == 3:
            _level_ = "rc"
        else:
            _level_ = None
        
        return "typing_extensions {}".format(".".join((
            str(self.major),
            str(self.minor),
            str(self.micro),
        )) + (
            "" if self.submicro == 0 else "." + str(self.submicro)
        ) + (
            _level_ + str(self.serial) if _level_ is not None else ""
        ))

TypingExtensionsVersionInfo = TypingExtensionsVersionInfo()

### Private functions and not for export ###

def _prevent_unused_imports(*_): pass # nothing, only prevent unused imports. implemented 0.3.55a2

### Enums and Flags ###
# 0.3.44: Additional checking to ensure these enumerator and flag classes exist already.

import enum as _enum

class Enum(_enum.Enum):
    """
    @lifetime >= 0.3.26rc1 [`enum.Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)
    """
    
    if False: # attempt 0.3.56
        
        def _add_alias_(self, name: str):
            self.__class__._add_member_(name, self)

        def _add_value_alias_(self, value: Any):
            cls = self.__class__
            try:
                if value in cls._value2member_map_:
                    if cls._value2member_map_[value] is not self:
                        raise ValueError('%r is already bound: %r' % (value, cls._value2member_map_[value]))
                    return
            except TypeError:
                # unhashable value, do long search
                for m in cls._member_map_.values():
                    if m._value_ == value:
                        if m is not self:
                            raise ValueError('%r is already bound: %r' % (value, cls._value2member_map_[value]))
                        return
            try:
                # This may fail if value is not hashable. We can't add the value
                # to the map, and by-value lookups for this value will be
                # linear.
                cls._value2member_map_.setdefault(value, self)
                cls._hashable_values_.append(value)
            except TypeError:
                # keep track of the value in a list so containment checks are quick
                cls._unhashable_values_.append(value)
                cls._unhashable_values_map_.setdefault(self.name, []).append(value)

# 0.3.56: define __len__, __iter__, __ror__, __rand__ and __rxor__ before Python 3.11
class Flag(_enum.Flag):
    """
    @lifetime >= 0.3.26rc1 [`enum.Flag`](https://docs.python.org/3/library/enum.html#enum.Flag)
    """
    
    if _sys.version_info < (3, 11):
        
        def __len__(self):
            return self._value_.bit_count()
        
        def __iter__(self):
            """
            Returns flags in definition order.
            """
            yield from self._iter_member_(self._value_) # collections.abc.Iterator[Self]
            
        def __ror__(self, other: Self):
            return super().__or__(other)
        
        def __rand__(self, other: Self):
            return super().__and__(other)
        
        def __rxor__(self, other: Self):
            return super().__xor__(other)
    
class ReprEnum(Enum): # >=Py3.11; practically subclass of enum.Enum and nothing in the body. Try to define for least than Py3.11
    """
    @lifetime >= 0.3.26rc1 [`enum.ReprEnum`](https://docs.python.org/3/library/enum.html#enum.ReprEnum)
    """

if _sys.version_info >= (3, 11):
    
    from enum import verify as verify, EnumCheck as EnumCheck, EnumType as EnumType
    
    # If not the same (as before 3.13 it can occur), we need to ensure they are the same by using type assignment
    if ReprEnum != _enum.ReprEnum:
        ReprEnum = _enum.ReprEnum
        
class EnumDict(Enum): # base class ignored after assignment below
    """
    @lifetime >= 0.3.26rc1 [`enum.EnumDict`](https://docs.python.org/3/library/enum.html#enum.EnumDict)
    
    Undocumented internal class `enum._EnumDict` before Python 3.13
    """
    
if _sys.version_info >= (3, 13):
    EnumDict = _enum.EnumDict
    
else:
    # questionable: since when enum._EnumDict was in enum.py file?
    EnumDict = _enum._EnumDict
    
class FlagBoundary(Enum): # >=Py3.11. Define for least than Py3.11
    """
    @lifetime >= 0.3.26rc1 [`enum.FlagBoundary`](https://docs.python.org/3/library/enum.html#enum.FlagBoundary)
    
    Control how out of range values are handled.
    
    - `STRICT` -> error is raised             (default for `Flag`)
    - `CONFORM` -> extra bits are discarded
    - `EJECT` -> lose flag status
    - `KEEP` -> keep flag status and all bits (default for `IntFlag`)
    """
    STRICT = _enum.auto() # 1; enum.auto accessible for >=Py3.8
    CONFORM = _enum.auto() # 2
    EJECT = _enum.auto() # 3
    KEEP = _enum.auto() # 4

class IntegerFlag(_enum.IntFlag): # accessible for >=Py3.6 (can be recreated via bases: >= Py3.11 (int, ReprEnum, Flag, boundary=FlagBoundary.KEEP), < Py3.11 (int, Flag))
    """
    @lifetime >= 0.3.26rc1. [`enum.IntFlag`](https://docs.python.org/3/library/enum.html#enum.IntFlag)
    """

if _sys.version_info >= (3, 11):
    
    class IntegerEnum(_enum.IntEnum):
        """
        @lifetime >= 0.3.26rc1. [`enum.IntEnum`](https://docs.python.org/3/library/enum.html#enum.IntEnum)
        """
        
    class StringEnum(_enum.StrEnum):
        """
        @lifetime >= 0.3.26rc1. [`enum.StrEnum`](https://docs.python.org/3/library/enum.html#enum.StrEnum)
        """
        
else:
    
    class IntegerEnum(int, ReprEnum):
        """
        @lifetime >= 0.3.26rc1. [`enum.IntEnum`](https://docs.python.org/3/library/enum.html#enum.IntEnum)
        """
        
    class StringEnum(str, ReprEnum):
        """
        @lifetime >= 0.3.26rc1. [`enum.StrEnum`](https://docs.python.org/3/library/enum.html#enum.StrEnum)
        """
        
        def __new__(cls, *values):
            "values must already be of type `str`"
            if len(values) > 3:
                raise TypeError('too many arguments for str(): %r' % (values, ))
            if len(values) == 1:
                # it must be a string
                if not isinstance(values[0], str):
                    raise TypeError('%r is not a string' % (values[0], ))
            if len(values) >= 2:
                # check that encoding argument is a string
                if not isinstance(values[1], str):
                    raise TypeError('encoding must be a string, not %r' % (values[1], ))
            if len(values) == 3:
                # check that errors argument is a string
                if not isinstance(values[2], str):
                    raise TypeError('errors must be a string, not %r' % (values[2]))
            value = str(*values)
            member = str.__new__(cls, value)
            member._value_ = value
            return member

        @staticmethod
        def _generate_next_value_(name, start, count, last_values):
            """
            Return the lower-cased version of the member name.
            """
            return name.lower()
        
### UTILITY TYPES ###

# It is not worth to use solutions from 'typing_extensions' because these were provided later, and won't be supported in Python 3.6.
# In the following imports this includes 'Optional', 'Union', 'IO', 'BinaryIO', 'TextIO' and 'Generic', which were provided in 4.7.0.
from typing import (
    # ?
    IO as IO,
    # 0.3.26b3
    Generic as Generic, # >=Py3.5
    ClassVar as ClassVar, # >=Py3.5.3
    # 0.3.26rc1
    Optional as Optional, # >=Py3.5
    Union as Union, # >=Py3.5
    # 0.3.26rc3
    BinaryIO as BinaryIO, 
    TextIO as TextIO,
    # 0.3.37
    TYPE_CHECKING as TYPE_CHECKING # >=Py3.5.2
)

# ****************** Py3.6: 10/2017 ************************
# NOTE: LAST BUGFIX: 3.6.8 / SECURITY: 3.6.15
if _sys.version_info >= (3, 6, 2):
    from typing import NoReturn as NoReturn # 0.3.26b3
else:
    from typing_extensions import NoReturn as NoReturn # 0.3.26b3

# ****************** Py3.7: 10/2018 ************************
# NOTE: LAST BUGFIX: 3.7.8 / SECURITY: 3.7.17
if _sys.version_info >= (3, 7):
    
    from types import (
        # 0.3.51
        ClassMethodDescriptorType as ClassMethodDescriptorType,
        MethodDescriptorType as MethodDescriptorType,
        MethodWrapperType as MethodWrapperType,
        WrapperDescriptorType as WrapperDescriptorType,
        # 0.3.54
        resolve_bases as resolve_bases,
        # 0.3.56
        resolve_bases as resolveBases
    )
    from uuid import SafeUUID as SafeUUID
    
else:
    class SafeUUID(Enum):
        safe = 0
        unsafe = -1
        unknown = None

if _sys.version_info >= (3, 7, 4):
    # Py3.14+ = 'annotationlib.ForwardRef'
    from typing import ForwardRef as ForwardRef # 0.3.26rc3
else:
    from typing_extensions import ForwardRef as ForwardRef # 0.3.26rc3

# ****************** Py3.8: 10/2019 ************************
# NOTE: LAST BUGFIX: 3.8.10 / SECURITY: 3.8.20
if _sys.version_info >= (3, 8):
    
    from types import CellType as CellType # 0.3.54
    from typing import (
        # 0.3.26rc1
        Final as Final,
        Protocol as Protocol
    )
    
else:
    
    from typing_extensions import (
        # 0.3.26rc1
        Final as Final,
        Protocol as Protocol
    )
    
if TypingExtensionsVersionInfo >= (4, 8): # Py3.8+
    from typing_extensions import Doc as Doc
    
# ****************** Py3.9: 10/2020 ************************
# NOTE: LAST BUGFIX: 3.9.13 / SECURITY: 3.9.23
#
# / 0.3.42 /: Inspect type subscription with abstract base
# classes from 'collections.abc'
# / 0.3.46 /: Inspect type substription with inbuilt classes
# from 'builtins' in submodule '~._subscript_builtins'
# / 0.3.52 /: Migrate inbuilt classes there; types with AVT
# prefix only have purpose for typing, more specifically,
# subscripting. These change when going since or below Python 3.9.
# Some generic classes can throw errors when inspecting
# them in isinstance() or issubclass(), hence ordinarily classes
# without AVT prefix are exported.
if _sys.version_info >= (3, 9):
    
    from builtins import (
        # 0.3.52
        dict as AVT_Dict,
        frozenset as AVT_FrozenSet,
        list as AVT_List,
        set as AVT_Set,
        tuple as AVT_Tuple,
        type as AVT_Type
    )
    from collections import (
        # 0.3.52
        ChainMap as AVT_ChainMap,
        Counter as AVT_Counter,
        OrderedDict as AVT_OrderedDict,
        defaultdict as AVT_DefaultDict,
        deque as AVT_Deque
    )
    from collections.abc import (
        # 0.3.52
        AsyncGenerator as AVT_AsyncGenerator,
        AsyncIterable as AVT_AsyncIterable,
        AsyncIterator as AVT_AsyncIterator,
        Awaitable as AVT_Awaitable,
        Callable as AVT_Callable,
        Collection as AVT_Collection,
        Container as AVT_Container,
        Coroutine as AVT_Coroutine,
        Generator as AVT_Generator,
        ItemsView as AVT_ItemsView,
        Iterable as AVT_Iterable,
        Iterator as AVT_Iterator,
        KeysView as AVT_KeysView,
        Mapping as AVT_Mapping,
        MappingView as AVT_MappingView,
        MutableMapping as AVT_MutableMapping,
        MutableSequence as AVT_MutableSequence,
        MutableSet as AVT_MutableUniqual,
        Reversible as AVT_Reversible,
        Sequence as AVT_Sequence,
        Set as AVT_Uniqual,
        ValuesView as AVT_ValuesView
    )
    from contextlib import (
        # 0.3.53
        AbstractAsyncContextManager as AVT_AsyncContextManager,
        AbstractContextManager as AVT_ContextManager
    )
    from os import PathLike as AVT_PathLike # 0.3.54
    from re import (
        # 0.3.52
        Match as AVT_Match,
        Pattern as AVT_Pattern
    )
    from types import GenericAlias as GenericAlias # 0.3.37
    from typing import Annotated as Annotated # 0.3.26rc1
    
    ByteString = Union[bytes, bytearray, memoryview] # 0.3.37
    
else:
    
    from typing import (
        # 0.3.37
        ByteString as ByteString,
        # builtins, 0.3.52
        Dict as AVT_Dict,
        FrozenSet as AVT_FrozenSet,
        List as AVT_List,
        Set as AVT_Set,
        Tuple as AVT_Tuple,
        Type as AVT_Type, # >=Py3.5.2
        # collections, 0.3.52
        DefaultDict as AVT_DefaultDict, # >=Py3.5.2
        # collections.abc, 0.3.52
        AsyncIterable as AVT_AsyncIterable, # >=Py3.5.2
        AsyncIterator as AVT_AsyncIterator, # >=Py3.5.2
        Awaitable as AVT_Awaitable, # >=Py3.5.2
        Callable as AVT_Callable,
        Collection as AVT_Collection,
        Container as AVT_Container,
        Coroutine as AVT_Coroutine,
        Generator as AVT_Generator,
        ItemsView as AVT_ItemsView,
        Iterable as AVT_Iterable,
        Iterator as AVT_Iterator,
        KeysView as AVT_KeysView,
        Mapping as AVT_Mapping,
        MappingView as AVT_MappingView,
        MutableMapping as AVT_MutableMapping,
        MutableSequence as AVT_MutableSequence,
        MutableSet as AVT_MutableUniqual,
        Reversible as AVT_Reversible,
        Sequence as AVT_Sequence,
        Set as AVT_Uniqual,
        ValuesView as AVT_ValuesView,
        # contextlib, 0.3.53
        ContextManager as AVT_ContextManager, # >=Py3.5.4
        # re, 0.3.52
        Match as AVT_Match, # typing_extensions >= 4.7.0
        Pattern as AVT_Pattern, # typing_extensions >= 4.7.0
        # temporary internal imports for 'AVT_PathLike'
        TypeVar as _TypeVar,
        runtime_checkable as _runtime
    )
    from typing_extensions import Annotated as Annotated # 0.3.26rc1
    
    if _sys.version_info >= (3, 6, 1):
        
        from typing import (
            # collections, 0.3.52
            ChainMap as AVT_ChainMap,
            Counter as AVT_Counter,
            Deque as AVT_Deque,
            # collections.abc, 0.3.52
            AsyncGenerator as AVT_AsyncGenerator
        )
        
    else:
        
        from typing_extensions import (
            # collections, 0.3.52
            ChainMap as AVT_ChainMap,
            Counter as AVT_Counter,
            Deque as AVT_Deque,
            # collections.abc, 0.3.52
            AsyncGenerator as AVT_AsyncGenerator
        )
        
    if _sys.version_info >= (3, 6, 2):
        from typing import AsyncContextManager as AVT_AsyncContextManager # contextlib, 0.3.53
    else:
        from typing_extensions import AsyncContextManager as AVT_AsyncContextManager # contextlib, 0.3.53
        
    if _sys.version_info >= (3, 7, 2):
        from typing import OrderedDict as AVT_OrderedDict # collections, 0.3.52
    else:
        from typing_extensions import OrderedDict as AVT_OrderedDict # collections, 0.3.52
    
    _AnyStr_cov_pathLikeExclusive = _TypeVar("_AnyStr_cov_pathLikeExclusive", str, bytes, covariant = True)
    
    # 'os.PatLike' exists since Python 3.6, but wasn't generic until 3.9.
    @_runtime
    class AVT_PathLike(Protocol[_AnyStr_cov_pathLikeExclusive]):
        """@lifetime >= 0.3.54"""
        
        def __fspath__(self) -> _AnyStr_cov_pathLikeExclusive: ...
        
    del _TypeVar, _runtime

# ****************** Py3.10: 10/2021 ************************
if _sys.version_info >= (3, 10):
    
    # Py3.14+ = 'annotationlib.get_annotations'
    from inspect import (
        # 0.3.37
        get_annotations as get_annotations,
        # 0.3.57
        get_annotations as getAnnotations
    ) 
    from types import (
        # ?
        EllipsisType as EllipsisType,
        # 0.3.26
        NoneType as NoneType,
        # 0.3.37
        UnionType as UnionType, 
        NotImplementedType as NotImplementedType
    )
    from typing import (
        # 0.3.26rc1
        ParamSpec as ParamSpec, 
        ParamSpecArgs as ParamSpecArgs,
        ParamSpecKwargs as ParamSpecKwargs,
        TypeGuard as TypeGuard,
        TypeAlias as TypeAlias,
        Concatenate as Concatenate,
        get_args as get_args, # >= 0.3.34
        # 0.3.37
        get_origin as get_origin,
        # 0.3.54
        get_args as getArgs, # < 0.3.34
        get_origin as getOrigin
    )
    
else:
    
    from typing_extensions import (
        # 0.3.26rc1
        ParamSpec as ParamSpec, 
        ParamSpecArgs as ParamSpecArgs, 
        ParamSpecKwargs as ParamSpecKwargs,
        TypeGuard as TypeGuard, 
        TypeAlias as TypeAlias,
        Concatenate as Concatenate,
        final as _final,
        get_args as get_args, # >= 0.3.34
        # 0.3.37
        get_origin as get_origin,
        # 0.3.54
        get_origin as getOrigin,
        get_args as getArgs # < 0.3.34
    )
    
    NotImplementedType = type(NotImplemented) # >= 0.3.52
    
    @_final
    class NoneType:
        "@lifetime >= 0.3.26"
        def __bool__(self) -> Literal[False]: ...
        
    @_final
    class EllipsisType: ...
    
    del _final
        
    NoneType = cast(NoneType, type(None))
    EllipsisType = cast(EllipsisType, type(Ellipsis))
    
    # backport 0.3.56, Py3.8+
    if TypingExtensionsVersionInfo >= (4, 13):
        from typing_extensions import (
            get_annotations as get_annotations,
            # 0.3.57
            get_annotations as getAnnotations
        )

if _sys.version_info >= (3, 10, 1):
    from typing import Literal as Literal # 0.3.26rc1
else:
    from typing_extensions import Literal as Literal # 0.3.26rc1

# ****************** Py3.11: 10/2022 ************************
# NewType (3.5.2+): the error message for subclassing instances
# of NewType was improved on 3.11
if _sys.version_info >= (3, 11):
    
    from typing import (
        # 0.3.26rc1
        Any as Any,
        LiteralString as LiteralString, 
        Never as Never,
        NewType as NewType,
        NotRequired as NotRequired,
        Required as Required,
        Self as Self,
        overload as overload,
        # 0.3.37
        assert_never as assert_never, 
        assert_type as assert_type,
        clear_overloads as clear_overloads,
        final as final,
        get_overloads as get_overloads,
        reveal_type as reveal_type,
        # 0.3.54
        assert_never as assertNever,
        assert_type as assertType,
        clear_overloads as clearOverloads,
        get_overloads as getOverloads,
        reveal_type as revealType,
    )
    
else:
    
    from typing_extensions import (
        # 0.3.26rc1
        Any as Any,
        LiteralString as LiteralString, 
        Never as Never,
        NewType as NewType,
        NotRequired as NotRequired,
        Required as Required,
        Self as Self,
        overload as overload,
        # 0.3.37
        assert_never as assert_never, 
        reveal_type as reveal_type,
        final as final,
        # 0.3.54
        assert_never as assertNever,
        reveal_type as revealType
    )
        
    if TypingExtensionsVersionInfo >= (4, 2):
        
        from typing_extensions import (
            # 0.3.37
            assert_type as assert_type, 
            clear_overloads as clear_overloads,
            get_overloads as get_overloads,
            # 0.3.54
            assert_type as assertType,
            clear_overloads as clearOverloads,
            get_overloads as getOverloads
        )

# ****************** Py3.12: 10/2023 ************************
# Unpack (3.11+): see PEP 692 (changed the repr of Unpack[])
# dataclass_transform (3.11+) was lacking frozen_default parameter
if _sys.version_info >= (3, 12):
    
    from collections.abc import Buffer as _Buffer # 0.3.37
    from inspect import BufferFlags as BufferFlags # 0.3.26rc2
    from types import (
        # 0.3.40
        get_original_bases as get_original_bases,
        # 0.3.54
        get_original_bases as getOriginalBases
    )
    from typing import (
        # 0.3.26rc1
        Unpack as Unpack,
        # 0.3.37
        dataclass_transform as dataclass_transform, 
        override as override,
        # 0.3.54
        dataclass_transform as dataclassTransform
    )
    
else:
    
    if TypingExtensionsVersionInfo >= (4, 1): # Py3.6+
        from typing_extensions import (
            
            # 0.3.26rc1
            Unpack as Unpack,
            
            # 0.3.37
            dataclass_transform as dataclass_transform,
            
            # 0.3.54
            dataclass_transform as dataclassTransform
        )
    
    
    if TypingExtensionsVersionInfo >= (4, 4): # Py3.7+
        from typing_extensions import override as override # 0.3.37
    
    if TypingExtensionsVersionInfo >= (4, 6): # Py3.7+
        from typing_extensions import (
            # 0.3.37
            Buffer as _Buffer,
            # 0.3.55a2
            get_original_bases as get_original_bases,
            get_original_bases as getOriginalBases
        )
        
    else:
        
        class Buffer(metaclass=ABCMeta):

            __slots__ = ()

            @abstractmethod
            def __buffer__(self, flags: int) -> memoryview:
                raise NotImplementedError

            @classmethod
            def __subclasshook__(cls, C: type):
                
                def _check_methods(C: type, *methods: str):
                    mro = C.__mro__
                    for method in methods:
                        for B in mro:
                            if method in B.__dict__:
                                if B.__dict__[method] is None:
                                    return NotImplemented
                                break
                        else:
                            return NotImplemented
                    return True
                
                if cls is Buffer:
                    return _check_methods(C, "__buffer__")
                return NotImplemented
    
    class BufferFlags(IntegerFlag): # 0.3.26rc2
        SIMPLE = 0x0
        WRITABLE = 0x1
        FORMAT = 0x4
        ND = 0x8
        STRIDES = 0x10 | ND
        C_CONTIGUOUS = 0x20 | STRIDES
        F_CONTIGUOUS = 0x40 | STRIDES
        ANY_CONTIGUOUS = 0x80 | STRIDES
        INDIRECT = 0x100 | STRIDES
        CONTIG = ND | WRITABLE
        CONTIG_RO = ND
        STRIDED = STRIDES | WRITABLE
        STRIDED_RO = STRIDES
        RECORDS = STRIDES | WRITABLE | FORMAT
        RECORDS_RO = STRIDES | FORMAT
        FULL = INDIRECT | WRITABLE | FORMAT
        FULL_RO = INDIRECT | FORMAT
        READ = 0x100
        WRITE = 0x200

# ****************** Py3.13: 10/2024 ************************
# About TypeVar & TypeVarTuple see PEP 696 about 'default'
# parameter. NamedTuple is for backporting updates since its
# existence (3.5.2)

if _sys.version_info >= (3, 13):
    
    from types import CapsuleType as CapsuleType # 0.3.54
    from typing import (
        # 0.3.26b3
        TypeVar as TypeVar,
        # 0.3.26rc1
        NamedTuple as NamedTuple, 
        Protocol as Protocol,
        TypeIs as TypeIs,
        NoDefault as NoDefault,
        ReadOnly as ReadOnly,
        runtime_checkable as runtime,
        runtime_checkable as runtime_checkable,
        # 0.3.26rc3
        TypeVarTuple as TypeVarTuple,
        # 0.3.37
        get_protocol_members as get_protocol_members,
        is_protocol as is_protocol,
        # 0.3.54
        get_protocol_members as getProtocolMembers,
        is_protocol as isProtocol,
    )
    
    AnyStr = TypeVar("AnyStr", bytes, str)
    
else:
    
    from typing import AnyStr as AnyStr
    from typing_extensions import (
        # 0.3.26b3
        TypeVar as TypeVar,
        # 0.3.26rc1
        NamedTuple as NamedTuple, 
        Protocol as Protocol,
        runtime_checkable as runtime,
        runtime_checkable as runtime_checkable,
        # 0.3.26rc3
        TypeVarTuple as TypeVarTuple,
        # 0.3.37
        is_protocol as is_protocol,
        # 0.3.54
        is_protocol as isProtocol # pyright: ignore[reportUnusedImport]
    )
        
    if TypingExtensionsVersionInfo >= (4, 7): # Py3.7+
        
        from typing_extensions import (
            # 0.3.37
            get_protocol_members as get_protocol_members,
            # 0.3.54
            get_protocol_members as getProtocolMembers # pyright: ignore[reportUnusedImport]
        )
        
    if TypingExtensionsVersionInfo >= (4, 9): # Py3.8+
        from typing_extensions import ReadOnly as ReadOnly # 0.3.26rc1
    
    if TypingExtensionsVersionInfo >= (4, 10): # Py3.8+
        from typing_extensions import TypeIs as TypeIs # 0.3.26rc1
    
    if TypingExtensionsVersionInfo >= (4, 12): # Py3.8+
        from typing_extensions import (
            # 0.3.26rc1
            NoDefault as NoDefault,
            # 0.3.54
            CapsuleType as CapsuleType
        )                              
    
if _sys.version_info >= (3, 13, 3):
    from warnings import deprecated as deprecated # 0.3.37
else:
    
    if TypingExtensionsVersionInfo >= (4, 5): # Py3.7+
        from typing_extensions import deprecated as deprecated # 0.3.37

# ****************** Py3.14: 07.10.2025 ************************
# Removal of 'collections.abc.ByteString', but we will still
# re-declare it. Update: removal was postponed to 3.17, but
# we will still re-declare it. 'typing.TypeAliasType': star
# unpacking (3.14)
if _sys.version_info >= (3, 14):
    
    from annotationlib import Format as Format # 0.3.54
    from io import (
        Reader as Reader,
        Writer as Writer
    )
    from typing import (
        # 0.3.26rc1
        TypeAliasType as TypeAliasType,
        # 0.3.56
        evaluate_forward_ref as evaluate_forward_ref,
        # 0.3.57
        evaluate_forward_ref as evaluateForwardRef
    )
    
else:
    
    if TypingExtensionsVersionInfo >= (4, 6): # Py3.7+
        from typing_extensions import TypeAliasType as TypeAliasType # 0.3.26rc1
        
    elif _sys.version_info >= (3, 12):
        from typing import TypeAliasType as TypeAliasType # 0.3.26rc1
    
    if TypingExtensionsVersionInfo >= (4, 13): # Py3.8+
        from typing_extensions import (
            Format as Format,
            # 0.3.57
            evaluate_forward_ref as evaluate_forward_ref,
            evaluate_forward_ref as evaluateForwardRef
        )
        
    else:
        class Format(IntegerEnum):
            VALUE = 1
            VALUE_WITH_FAKE_GLOBALS = 2
            FORWARDREF = 3
            STRING = 4
            
    if TypingExtensionsVersionInfo >= (4, 14): # Py3.9+
        from typing_extensions import (
            Reader as Reader,
            Writer as Writer
        )

### ****************** Py3.15: 10/2026 ************************
# If you are unfamiliar of PEP 728 about extra items in
# 'typing.TypedDict', PEP 728 was accepted and is planned for
# Python 3.15. 'typing_extensions' forgot one detail: set their
# internal value for PEP 728 check to 'False'. I will redo this
# statement in latest version, if anything changes with this PEP.
if _sys.version_info >= (3, 15):
    
    from typing import (
        # 0.3.37
        TypedDict as TypedDict,
        is_typeddict as is_typeddict,
        # 0.3.54
        is_typeddict as isTypedDict,
        NoExtraItems as NoExtraItems
    ) 
    
else:
    
    from typing import (
        # ?
        no_type_check_decorator as no_type_check_decorator,
        # 0.3.26rc1
        no_type_check_decorator as noTypeCheckDecorator
    )
    from typing_extensions import (
        # 0.3.37
        TypedDict as TypedDict,
        is_typeddict as is_typeddict, # TE>=4.1
        # 0.3.54
        is_typeddict as isTypedDict
    )
    
    if TypingExtensionsVersionInfo >= (4, 13): # Py3.8+
        from typing_extensions import NoExtraItems as NoExtraItems
    
    _prevent_unused_imports(noTypeCheckDecorator)

if _sys.version_info >= (3, 7):
    
    _prevent_unused_imports(resolveBases)
    
    if TypingExtensionsVersionInfo >= (4, 2): # Py3.7+
        _prevent_unused_imports(assertType, clearOverloads, getOverloads)
    
    if TypingExtensionsVersionInfo >= (4, 6): # Py3.7+
        _prevent_unused_imports(getOriginalBases)

    if TypingExtensionsVersionInfo >= (4, 7): # Py3.7+
        _prevent_unused_imports(getProtocolMembers, isProtocol)
        
    if TypingExtensionsVersionInfo >= (4, 13): # Py3.8+
        _prevent_unused_imports(evaluateForwardRef, getAnnotations)

_prevent_unused_imports(AsyncContextManager, ContextManager, MutableUniqual, Uniqual)
_prevent_unused_imports(assertNever, dataclassTransform, getArgs, getOrigin, getTypeHints, importModule, isTypedDict, lruCache, noTypeCheck, revealType, singleDispatch, newClass, prepareClass)

import _collections_abc, _hashlib, hashlib, hmac as _hmac, typing as _typing, typing_extensions as _typing_ext # not for export

_T = TypeVar("_T")
_P = ParamSpec("_P")
_A = TypeVar("_A", int, float, str) # array.array
_I = TypeVar("_I", default = int) # memoryview
_N = TypeVar("_N", int, float, _typing_ext.SupportsFloat, _typing_ext.SupportsInt, _typing_ext.SupportsIndex, _typing_ext.SupportsComplex) # itertools.count
_T1 = TypeVar("_T1")
_T2 = TypeVar("_T2")
_T3 = TypeVar("_T3")
_T_con = TypeVar("_T_con", contravariant = True)
_T_cov = TypeVar("_T_cov", covariant = True)
_T1_cov = TypeVar("_T1_cov", covariant = True) # itertools.groupby
_T2_cov = TypeVar("_T2_cov", covariant = True) # itertools.groupby
_KT_con = TypeVar("_KT_con", contravariant = True)
_KT_cov = TypeVar("_KT_cov", covariant = True)
_VT_cov = TypeVar("_VT_cov", covariant = True)
_T_yield_cov = TypeVar("_T_yield_cov", covariant = True) # Generator, Coroutine
_T_send_con = TypeVar("_T_send_cov", contravariant = True, default = None) # Generator -> CoroutineWrapperType
_T_return_cov = TypeVar("_T_return_cov", covariant = True, default = None) # Generator -> CoroutineWrapperType
_T_send_noDefault_con = TypeVar("_T_send_noDefault_con", contravariant = True) # Coroutine
_T_return_noDefault_cov = TypeVar("_T_return_noDefault_cov", covariant = True) # Coroutine
_T_start_cov = TypeVar("_T_start_cov", covariant = True, default = Any) # slice
_T_stop_cov = TypeVar("_T_stop_cov", covariant = True, default = _T_start_cov) # slice
_T_step_cov = TypeVar("_T_step_cov", covariant = True, default = Union[_T_start_cov, _T_stop_cov]) # slice
_T_awaitable = TypeVar("_T_awaitable", bound = AVT_Awaitable[Any]) # builtins.anext
_T_awaitable_cov = TypeVar("_T_awaitable_cov", covariant = True, bound = AVT_Awaitable[Any]) # builtins._SupportsSynchronousAnext
    
class _AsyncNextOperable(Protocol[_T_cov]): # >= 0.3.60 // _typeshed.SupportsAnext
    def __anext__(self) -> Awaitable[_T_cov]: ...
    
class _AsyncIterOperable(Protocol[_T_cov]): # >= 0.3.60 // _typeshed.SupportsAiter
    def __aiter__(self) -> _T_cov: ...
    
class _SynchronousAsyncNextOperable(Protocol[_T_awaitable_cov]): # >= 0.3.60 // builtins._SupportsSynchronousAnext
    def __anext__(self) -> _T_awaitable_cov: ...

_T_anext_cov = TypeVar("_T_anext_cov", covariant = True, bound = _AsyncNextOperable[Any])

if hasattr(_typing_ext, "disjoint_base"): # typing Py3.15+
    from typing_extensions import disjoint_base as disjoint_base

else:
    def disjoint_base(cls: AVT_Type[_T]):
        """
        @lifetime >= 0.3.56
        
        This decorator marks a class as a disjoint base.

        Child classes of a disjoint base cannot inherit from other disjoint bases that are
        not parent classes of the disjoint base.

        For example:

            @disjoint_base
            class Disjoint1: pass

            @disjoint_base
            class Disjoint2: pass

            class Disjoint3(Disjoint1, Disjoint2): pass  # Type checker error

        Type checkers can use knowledge of disjoint bases to detect unreachable code
        and determine when two types can overlap.

        See PEP 800."""
        cls.__disjoint_base__ = True
        return cls

# 0.3.52
# These both local variables below hold special names that Python uses in lambda and generator expressions.
# We use this way to ensure the change with this attribute's value will happen simultaneously with this project.
_LambdaName = (lambda: None).__name__ # "<lambda>"
_GenExprName = (i for i in (1,)).__qualname__ # "<genexpr>"

class _GenExprTypeMeta(type):
    """@lifetime >= 0.3.52"""
    def __instancecheck__(self, obj: object):
        return isinstance(obj, Generator) and obj.__qualname__.endswith(_GenExprName)

class _LambdaTypeMeta(type):
    """@lifetime >= 0.3.52"""
    def __instancecheck__(self, obj: object):
        return isinstance(obj, FunctionType) and obj.__name__.endswith(_LambdaName)

class GenExprType(metaclass = _GenExprTypeMeta):
    """
    @lifetime >= 0.3.52
    
    Use this class to find, if a generator object is actually created from generator expression, with `isinstance()`.
    """
    __init__ = None
    
class LambdaType(metaclass = _LambdaTypeMeta):
    """
    @lifetime >= 0.3.44 \\
    @modified 0.3.52
    
    Use this class to find, if a callable is actually a lambda expression, with `isinstance()`.
    
    NOTE: this class isn't the same as Python's `types.LambdaType`, and it is reserved for `isinstance()` only
    """
    if False: # projected
        def __new__(
            cls,
            code: CodeType,
            globals: AVT_Dict[str, Any],
            argdefs: Optional[AVT_Tuple[object, ...]] = None,
            closure: Optional[AVT_Tuple[CellType, ...]] = None,
            kwdefaults: Optional[AVT_Dict[str, object]] = None
        ):
            # using assumption 'types.LambdaType' is type alias to 'types.FunctionType',
            # return 'types.FunctionType', just without the 'name' parameter required
            return FunctionType(code, globals, _LambdaName, argdefs, closure, kwdefaults)
    else:
        __init__ = None
    
class _SpecialFormMeta(type):
    """@lifetime >= 0.3.52"""
    def __instancecheck__(self, obj: object): # 0.3.53: enhance type checking
        
        from typing import _SpecialForm
        from typing_extensions import _SpecialForm as _ExtSpecialForm
        
        # since 3.13 'typing.Annotated' is instance of 'typing._SpecialForm'
        if _sys.version_info >= (3, 13):
            return isinstance(obj, (_SpecialForm, _ExtSpecialForm))
        else:
            return isinstance(obj, (_SpecialForm, _ExtSpecialForm)) or obj is Annotated
            
class AnnotationForm:
    """
    @lifetime >= 0.3.48
    
    Refer to `_typeshed.AnnotationForm`
    """
    
class CoroutineWrapperType(AVT_Generator[_T_yield_cov, _T_send_con, _T_return_cov]):
    """
    @lifetime >= 0.3.53
    
    A wrapper object implementing `__await__` for coroutines
    """
    
class MaybeNone:
    """
    @lifetime >= 0.3.57
    
    Refer to `_typeshed.MaybeNone`
    """
    
class Incomplete:
    """
    @lifetime >= 0.3.60
    
    Refer to `_typeshed.Incomplete`
    """
    
# Let's be honest, I was having trouble re-creating these classes with type annotations.
# In reality none of these are protocols, because these get appropriate values assigned later,
# these definitions are only for correct type hinting
class AnyMeta(Protocol):
    """
    @lifetime >= 0.3.52
    
    Metaclass of `typing.Any`.
    
    Should be only used as `type(obj) is AnyMeta`
    """
    def __instancecheck__(self, obj: object) -> bool: ...
    def __repr__(self) -> str: ...
    
@final
class DictKeys(AVT_KeysView[_KT_cov], Generic[_KT_cov, _VT_cov]):
    """
    @lifetime >= 0.3.53
    
    Generic version of class `_collections_abc.dict_keys` (generic only in stub files)
    """
    def __eq__(self, value: object, /) -> bool: ...
    def __reversed__(self) -> AVT_Iterator[_KT_cov]: ...
    __hash__: ClassVar[None]  # type: ignore[assignment]
    if _sys.version_info >= (3, 13):
        def isdisjoint(self, other: AVT_Iterable[_KT_cov], /) -> bool: ...
    if _sys.version_info >= (3, 10):
        @property
        def mapping(self) -> MappingProxyType[_KT_cov, _VT_cov]: ...

@final
class DictValues(AVT_ValuesView[_VT_cov], Generic[_KT_cov, _VT_cov]):
    """
    @lifetime >= 0.3.53
    
    Generic version of class `_collections_abc.dict_values` (generic only in stub files)
    """
    def __reversed__(self) -> AVT_Iterator[_VT_cov]: ...
    if _sys.version_info >= (3, 10):
        @property
        def mapping(self) -> MappingProxyType[_KT_cov, _VT_cov]: ...

@final
class DictItems(AVT_ItemsView[_KT_cov, _VT_cov]):
    """
    @lifetime >= 0.3.53
    
    Generic version of class `_collections_abc.dict_items` (generic only in stub files)
    """
    def __eq__(self, value: object, /) -> bool: ...
    def __reversed__(self) -> AVT_Iterator[AVT_Tuple[_KT_cov, _VT_cov]]: ...
    __hash__: ClassVar[None]  # type: ignore[assignment]
    if _sys.version_info >= (3, 13):
        def isdisjoint(self, other: AVT_Iterable[AVT_Tuple[_KT_cov, _VT_cov]], /) -> bool: ...
    if _sys.version_info >= (3, 10):
        @property
        def mapping(self) -> MappingProxyType[_KT_cov, _VT_cov]: ...

if False: # < 0.3.57
    class ProtocolMeta(Protocol):
        """@lifetime >= 0.3.52"""
        __protocol_attrs__: ClassVar[AVT_Set[str]]
        def __init__(cls, *args: Any, **kwargs: Any) -> None: ...
        def __new__(
            mcls: AVT_Type[Self],
            name: str,
            bases: AVT_Tuple[type, ...],
            namespace: AVT_Dict[str, Any],
            /,
            **kwargs: Any
        ) -> Self: ...
        def __subclasscheck__(self, cls: type) -> bool: ...
        def __instancecheck__(self, obj: object) -> bool: ...
    
class SpecialForm(metaclass = _SpecialFormMeta):
    """
    @lifetime >= 0.3.52
    
    Use this class to find, if a type is actually a special form from `typing`
    """

if False: # < 0.3.57
    class TypedDictMeta(Protocol):
        """@lifetime >= 0.3.52"""
        def __new__(cls, typename: str, fields: AVT_Dict[str, Any] = {}, /, *, total: bool = True) -> Self: ...

class TypingNoDefaultType:
    """@lifetime >= 0.3.53"""
    
class TypingTupleType(tuple):
    """
    @lifetime >= 0.3.53
    
    Internal class for deprecated type alias `typing.Tuple`
    """

class TypingGenericType(Protocol):
    """
    @lifetime >= 0.3.52
    
    Internal class for generic aliases before `types.GenericAlias` (>=Py3.9)
    """
    _name: Optional[str] # ?
    _inst: bool # ?
    @property
    def __origin__(self) -> Union[type, TypeAliasType]: ...
    @property
    def __args__(self) -> AVT_Tuple[Any, ...]: ...
    @property
    def __parameters__(self) -> AVT_Tuple[Any, ...]: ...
    if _sys.version_info >= (3, 9):
        __slots__: None
        def __init__(self, origin: type, args: AVT_Tuple[Any, ...], *, inst: bool = True, name: Optional[str] = None) -> None: ...
    else:
        _special: bool # ?
        def __init__(self, origin: type, args: Any, *, inst: bool = True, special: bool = False, name: Optional[str] = None) -> None: ...
    def __eq__(self, other: Self) -> bool: ...
    def __hash__(self) -> int: ...
    if _sys.version_info >= (3, 10):
        def __or__(self, other: type) -> UnionType: ...
        def __ror__(self, other: type) -> UnionType: ...
    else:
        def __or__(self, other: type) -> TypingUnionType: ...
        def __ror__(self, other: type) -> TypingUnionType: ...
    def __getitem__(self, args: Any) -> Self: ...
    def __repr__(self) -> str: ...
    def __iter__(self) -> AVT_Generator[Any, Any, None]: ...
    def __reduce__(self) -> AVT_Tuple[Any, ...]: ...
    def copy_with(self, args: Any) -> Self: ...
    def _determine_new_args(self, args: Any) -> AVT_Tuple[Any, ...]: ...
    def _make_substitution(self, args: AVT_Iterable[type], new_arg_by_param: Any) -> AVT_List[Any]: ...
    ### inherited from typing._BaseGenericAlias ###
    def __dir__(self) -> AVT_List[str]: ...
    def __instancecheck__(self, obj: object) -> bool: ...
    def __subclasscheck__(self, cls: type) -> NoReturn: ...
    def __setattr__(self, attr: str, val: Any) -> None: ...
    def __getattr__(self, attr: str) -> Any: ...
    def __mro_entries__(self, bases: AVT_Iterable[object]) -> AVT_Tuple[type, ...]: ...
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ... 

class TypingAnnotatedType(TypingGenericType, Protocol):
    """
    @lifetime >= 0.3.52
    
    Internal class for `typing.Annotated` class
    """
    __iter__: None
    @property
    def __origin__(self) -> Union[type, TypeAliasType]: ...
    @property
    def __metadata__(self) -> Any: ...
    def __init__(self, origin: type, metadata: Any) -> None: ...
    def __repr__(self) -> str: ...
    def __reduce__(self) -> AVT_Tuple[Any, ...]: ...
    def __eq__(self, other: Self) -> bool: ...
    def __hash__(self) -> int: ...
    def __getattr__(self, attr: str) -> Any: ...
    def __mro_entries__(self, bases: AVT_Iterable[object]) -> AVT_Tuple[type, ...]: ...
    def copy_with(self, args: Any) -> Self: ...
    
class TypingCallableType(TypingGenericType, Protocol):
    """
    @lifetime >= 0.3.52
    
    Internal class for `collections.abc.Callable` class
    """
    __iter__: None
    def __repr__(self) -> str: ...
    def __reduce__(self) -> AVT_Tuple[Any, ...]: ...
    
class TypingConcatenateType(TypingGenericType, Protocol):
    """
    @lifetime >= 0.3.52
    
    Internal class for `typing.Concatenate` class
    """
    def copy_with(self, args: Any) -> Self: ...
    
class TypingLiteralType(TypingGenericType, Protocol):
    """
    @lifetime >= 0.3.52
    
    Internal class for `typing.Literal` class
    """
    def __eq__(self, other: Self) -> bool: ...
    def __hash__(self) -> int: ...

if _sys.version_info >= (3, 9):
    
    class TypingSpecialGenericType(Protocol):
        """
        @lifetime >= 0.3.59
        
        Internal special generic alias type, especially for deprecated aliases of `collections.abc` in `typing`
        """
        __iter__: None
        __slots__: None # undocumented
        @property
        def __origin__(self) -> Union[type, TypeAliasType]: ...
        def __init__(self, origin: type, nparams: int, *, inst: bool = True, name: Optional[str] = None, defaults: AVT_Tuple[type, ...] = ()) -> None: ...
        def __getitem__(self, params: Any) -> TypingGenericType: ...
        def copy_with(self, params: Any) -> TypingGenericType: ...
        def __repr__(self) -> str: ...
        def __subclasscheck__(self, cls: type) -> bool: ...
        def __reduce__(self) -> Optional[str]: ...
        # Parameter names in __or__ and __ror__ are consistent in the code these methods are in 'typing._SpecialGenericAlias'.
        def __or__(self, right: type) -> TypingUnionType: ...
        def __ror__(self, left: type) -> TypingUnionType: ...
        def __call__(self, *args: Any, **kwds: Any) -> Any: ...
        def __mro_entries__(self, bases: AVT_Iterable[object]) -> AVT_Tuple[type, ...]: ...
        def __dir__(self) -> AVT_List[str]: ...
        def __instancecheck__(self, obj: object) -> bool: ...
        def __subclasscheck__(self, cls: type) -> NoReturn: ...
        def __setattr__(self, attr: str, val: Any) -> None: ...
        def __getattr__(self, attr: str) -> Any: ...
        
        
    if _sys.version_info < (3, 13, 0, "beta"):
        
        class TypingExtensionsSpecialGenericType(TypingSpecialGenericType):
            """@lifetime >= 0.3.59"""
        
else:
    class TypingSpecialGenericType(TypingGenericType, Protocol):
        """
        @lifetime >= 0.3.59
        
        Internal special generic alias type, especially for aliases of `collections.abc` in `typing`
        """
        ...
    
class TypingUnionType(TypingGenericType, Protocol):
    """
    @lifetime >= 0.3.52
    
    Internal class for `typing.Union` class.
    
    Since Python 3.14 this type alias equals `typing.Union`
    """
    __iter__: None
    def __eq__(self, other: Self) -> bool: ...
    def __hash__(self) -> int: ...
    def __repr__(self) -> str: ...
    def __reduce__(self) -> AVT_Tuple[Any, ...]: ...
    def __instancecheck__(self, obj: object) -> bool: ...
    def __subclasscheck__(self, cls: type) -> bool: ...
    def copy_with(self, args: Any) -> Self: ...
    
class TypingUnpackType(TypingGenericType, Protocol):
    """
    @lifetime >= 0.3.52
    
    Retrieves internal class for `typing.Unpack` class
    """
    def __repr__(self) -> str: ...
    def __getitem__(self, args: Any) -> Self: ...
    @property
    def __typing_unpacked_tuple_args__(self) -> Optional[AVT_Tuple[Any, ...]]: ...
    @property
    def __typing_is_unpacked_typevartuple__(self) -> bool: ...

### Itertools ###
# 0.3.55a2+

from itertools import (
    # 0.3.55a2
    accumulate as accumulate, 
    chain as chain,
    combinations as combinations,
    combinations_with_replacement as combinations_with_replacement,
    compress as compress,
    count as count,
    cycle as cycle,
    dropwhile as dropwhile,
    filterfalse as filterfalse,
    groupby as groupby,
    islice as islice,
    permutations as permutations,
    product as product,
    repeat as repeat,
    starmap as starmap,
    takewhile as takewhile,
    tee as tee,
    zip_longest as zip_longest
)

if _sys.version_info >= (3, 10):
    from itertools import pairwise as pairwise # 0.3.55a2
    
else:
    
    class pairwise: # 0.3.55a2
        """
        Return an iterator of overlapping pairs taken from the input iterator.

        s -> (s0, s1), (s1, s2), (s2, s3), ...
        """
        
        def __new__(cls, iterable: AVT_Iterable[_T]):
            
            if not isinstance(iterable, Iterable):
                error = TypeError("expected an iterable object")
                raise error
            
            _iterator = iter(iterable)
            a = next(_iterator, None)

            for b in _iterator:
                yield a, b
                a = b

# 'itertools.batched' is defined since Python 3.12, but we add the 'strict' parameter before 3.13
if _sys.version_info >= (3, 13):
    from itertools import batched as batched # 0.3.55a2

else:
    class batched: # 0.3.55a2
        """
        Batch data into tuples of length n. The last batch may be shorter than n.

        Loops over the input iterable and accumulates data into tuples up to size n. The input is consumed lazily,
        just enough to fill a batch. The result is yielded as soon as a batch is full or when the input iterable is
        exhausted.
        ```
        >>> for batch in batched('ABCDEFG', 3):
        ...     print(batch)
        ...
        ('A', 'B', 'C')
        ('D', 'E', 'F')
        ('G',)
        ```
        If "strict" is True, raises a ValueError if the final batch is shorter than n.
        """
        
        def __new__(cls, iterable: AVT_Iterable[_T], n: int, *, strict: bool = False):
            
            if not isinstance(iterable, Iterable):
                error = TypeError("expected an iterable object")
                raise error
            
            if not isinstance(n, int) or (isinstance(n, int) and n < 1):
                error = ValueError("expected 1 or above in parameter 'n'")
                raise error
            
            i = 0
            _list = []
            _extract_from = tuple(iterable)
            
            if strict and len(_extract_from) % n != 0:
                error = ValueError("on strict mode, length of the iterable object must be divisible by 'n'")
                raise error
            
            while i < len(_extract_from):
                _list.append(_extract_from[i : i + n])
                i += n
                
            for e in _list:
                yield e
                
### Private AVT Types ###

@runtime
class _AVT_Slice(Protocol[_T_start_cov, _T_stop_cov, _T_step_cov]):
    """
    @lifetime >= 0.3.55
    
    An internal protocol class holding body-less `slice` members. Equivalent to ordinary `slice` at runtime.
    """
    
    @property
    def start(self) -> _T_start_cov: ...
    @property
    def step(self) -> _T_step_cov: ...
    @property
    def stop(self) -> _T_stop_cov: ...
    
    @overload
    def __new__(cls, start: None, stop: None = None, step: None = None, /) -> _AVT_Slice[Any, Any, Any]: ...
    @overload
    def __new__(cls, stop: _T2, /) -> _AVT_Slice[Any, _T2, Any]: ...
    @overload
    def __new__(cls, start: _T1, stop: None, step: None = None, /) -> _AVT_Slice[_T1, Any, Any]: ...
    @overload
    def __new__(cls, start: None, stop: _T2, step: None = None, /) -> _AVT_Slice[Any, _T2, Any]: ...
    @overload
    def __new__(cls, start: _T1, stop: _T2, step: None = None, /) -> _AVT_Slice[_T1, _T2, Any]: ...
    @overload
    def __new__(cls, start: None, stop: None, step: _T3, /) -> _AVT_Slice[Any, Any, _T3]: ...
    @overload
    def __new__(cls, start: _T1, stop: None, step: _T3, /) -> _AVT_Slice[_T1, Any, _T3]: ...
    @overload
    def __new__(cls, start: None, stop: _T2, step: _T3, /) -> _AVT_Slice[Any, _T2, _T3]: ...
    @overload
    def __new__(cls, start: _T1, stop: _T2, step: _T3, /) -> _AVT_Slice[_T1, _T2, _T3]: ...
    
    def __eq__(self, value: object, /) -> bool: ...
    
    if _sys.version_info >= (3, 12):
        def __hash__(self) -> int: ...
    else:
        __hash__: ClassVar[None]  # type: ignore[assignment]

    def indices(self, len: Indexable, /) -> AVT_Tuple[int, int, int]: ...

### AVT Types ###

# 'array', 'builtins', 'types', 0.3.54+
if _sys.version_info >= (3, 12):
    from array import array as AVT_Array
    
else:
    class AVT_Array(array, Generic[_A]):
        """@lifetime >= 0.3.54 // Generic version of `array.array`"""
            

if _sys.version_info >= (3, 9):
    from builtins import enumerate as AVT_Enumerate # >= 0.3.55a2
    from types import GenericAlias as AVT_GenericAlias # >= 0.3.55a1
else:
    
    class AVT_Enumerate(enumerate, Generic[_T]):
        """@lifetime >= 0.3.55a2 // Generic version of `enumerate`"""
    
    AVT_GenericAlias = TypingGenericType # >= 0.3.55a1


class AVT_Filter(filter, Generic[_T]):
    """@lifetime >= 0.3.55b1 // Generic version of `filter`"""
    
class AVT_Map(map, Generic[_T]):
    """@lifetime >= 0.3.55b1 // Generic version of `map`"""

if _sys.version_info >= (3, 14):
    from builtins import memoryview as AVT_MemoryView
    
else:
    
    class AVT_MemoryView(Generic[_I]):
        """@lifetime >= 0.3.54 // Generic version of `memoryview`"""
        
        def __new__(cls, obj: ReadableBuffer):
            return memoryview(obj)
        @property
        def format(self) -> str: ...
        @property
        def itemsize(self) -> int: ...
        @property
        def shape(self) -> Optional[AVT_Tuple[int, ...]]: ...
        @property
        def strides(self) -> Optional[AVT_Tuple[int, ...]]: ...
        @property
        def suboffsets(self) -> Optional[AVT_Tuple[int, ...]]: ...
        @property
        def readonly(self) -> bool: ...
        @property
        def ndim(self) -> int: ...
        @property
        def obj(self) -> ReadableBuffer: ...
        @property
        def c_contiguous(self) -> bool: ...
        @property
        def f_contiguous(self) -> bool: ...
        @property
        def contiguous(self) -> bool: ...
        @property
        def nbytes(self) -> int: ...
        def __enter__(self) -> Self: ...
        def __exit__(
            self,
            exc_type: Optional[AVT_Type[BaseException]],  # noqa: PYI036 # This is the module declaring BaseException
            exc_val: Optional[BaseException],
            exc_tb: Optional[TracebackType],
            /,
        ) -> None: ...
        @overload
        def cast(self, format: Literal["c", "@c"], shape: Union[AVT_List[int], AVT_Tuple[int, ...]] = ...) -> AVT_MemoryView[bytes]: ...
        @overload
        def cast(self, format: Literal["f", "@f", "d", "@d"], shape: Union[AVT_List[int], AVT_Tuple[int, ...]] = ...) -> AVT_MemoryView[float]: ...
        @overload
        def cast(self, format: Literal["?"], shape: Union[AVT_List[int], AVT_Tuple[int, ...]] = ...) -> AVT_MemoryView[bool]: ...
        @overload
        def cast(self, format: Literal['b', 'B', '@b', '@B', 'h', 'H', '@h', '@H', 'i', 'I', '@i', '@I', 'l', 'L', '@l', '@L', 'q', 'Q', '@q', '@Q', 'P', '@P'], shape: Union[AVT_List[int], AVT_Tuple[int, ...]] = ...) -> AVT_MemoryView: ...
        @overload
        def __getitem__(self, key: Union[Indexable, AVT_Tuple[Indexable, ...]], /) -> _I: ...
        @overload
        def __getitem__(self, key: slice, /) -> AVT_MemoryView[_I]: ...
        def __contains__(self, x: object, /) -> bool: ...
        def __iter__(self) -> Iterator[_I]: ...
        def __len__(self) -> int: ...
        def __eq__(self, value: object, /) -> bool: ...
        def __hash__(self) -> int: ...
        @overload
        def __setitem__(self, key: slice, value: ReadableBuffer, /) -> None: ...
        @overload
        def __setitem__(self, key: Union[Indexable, AVT_Tuple[Indexable, ...]], value: _I, /) -> None: ...
        if _sys.version_info >= (3, 10):
            def tobytes(self, order: Optional[Literal["C", "F", "A"]] = "C") -> bytes: ...
        else:
            def tobytes(self, order: Optional[Literal["C", "F", "A"]] = None) -> bytes: ...

        def tolist(self) -> AVT_List[int]: ...
        if _sys.version_info >= (3, 8):
            def toreadonly(self) -> AVT_MemoryView: ...
        def release(self) -> None: ...
        def hex(self, sep: Union[str, bytes] = ..., bytes_per_sep: Indexable = ...) -> str: ...
        def __buffer__(self, flags: int, /) -> AVT_MemoryView: ...
        def __release_buffer__(self, buffer: AVT_MemoryView, /) -> None: ...

        # These are inherited from the Sequence ABC, but don't actually exist on memoryview.
        # See https://github.com/python/cpython/issues/125420
        
        # I will be following this restriction, however, I advise you to use the tolist() method first,
        # then use either of these methods below for older versions of Python, like view.tolist().count(int.from_bytes(b"a", "little"))
        # (assuming we have 'view' with value memoryview(b"abcd"), then 1 would be returned in this case).
        # view.index() and view.count(), despite these are formally defined on Python 3.14, may be buggy,
        # so using tolist() before these methods is strongly encouraged.
        index: ClassVar[None]  # type: ignore[assignment]
        count: ClassVar[None]  # type: ignore[assignment]

if _sys.version_info >= (3, 10): 
    from types import UnionType as AVT_UnionType # >= 0.3.55a1
else:
    AVT_UnionType = TypingUnionType # >= 0.3.55a1
    
class AVT_Reversed(reversed, Generic[_T]):
    """@lifetime >= 0.3.55b1 // Generic version of `reversed`"""

class AVT_Slice(Generic[_T_start_cov, _T_stop_cov, _T_step_cov]):
    """
    @lifetime >= 0.3.55b1 // Generic version of `slice`
    
    `slice` is a non-subscriptable final class. In this case this class only defines `__new__` method, which returns `slice` object.
    This object cannot be, however, *subscripted*.
    
    Instead consider using `AVT_Slice[Start?, Stop?, Step?]`
    """
    
    # Any instead of None is misleading, all I do here is keeping it in sync with 'slice' built-in
    @overload
    def __new__(cls, start: None, stop: None = None, step: None = None, /) -> _AVT_Slice[Any, Any, Any]: ...
    @overload
    def __new__(cls, stop: _T2, /) -> _AVT_Slice[Any, _T2, Any]: ...
    @overload
    def __new__(cls, start: _T1, stop: None, step: None = None, /) -> _AVT_Slice[_T1, Any, Any]: ...
    @overload
    def __new__(cls, start: None, stop: _T2, step: None = None, /) -> _AVT_Slice[Any, _T2, Any]: ...
    @overload
    def __new__(cls, start: _T1, stop: _T2, step: None = None, /) -> _AVT_Slice[_T1, _T2, Any]: ...
    @overload
    def __new__(cls, start: None, stop: None, step: _T3, /) -> _AVT_Slice[Any, Any, _T3]: ...
    @overload
    def __new__(cls, start: _T1, stop: None, step: _T3, /) -> _AVT_Slice[_T1, Any, _T3]: ...
    @overload
    def __new__(cls, start: None, stop: _T2, step: _T3, /) -> _AVT_Slice[Any, _T2, _T3]: ...
    @overload
    def __new__(cls, start: _T1, stop: _T2, step: _T3, /) -> _AVT_Slice[_T1, _T2, _T3]: ...
    
    def __new__(cls, *args):
        
        if len(args) not in (1, 2, 3):
            error = TypeError("expected 1-3 arguments, got {}".format(len(args)))
            raise error
        
        if len(args) == 1:
            return slice(args[0])
        
        else:
            return slice(args[0], args[1], args[2])
        
if _sys.version_info >= (3, 8): # TE>=4.10, Py3.8+
    AVT_TypeIs = TypeIs # 0.3.56
else:
    AVT_TypeIs = TypeGuard # 0.3.56
    
class AVT_Zip(zip, Generic[_T_cov]):
    """@lifetime >= 0.3.55a2 // Generic version of `zip`"""

# 'itertools', 0.3.55a2+
class AVT_Accumulate(accumulate, Generic[_T]):
    """@lifetime >= 0.3.55a2 // Generic version of `itertools.accumulate`"""
    
class AVT_Batched(batched, Generic[_T_cov]):
    """
    @lifetime >= 0.3.55a2 // Generic version of `itertools.batched`
    
    `batched` exists since 3.12, and it is backported in-code, to include `strict` \\
    keyword parameter that was added in 3.13. Use `aveytense.types.batched` \\
    import to use in versions 3.8 - 3.12!
    """
    
class AVT_Chain(chain, Generic[_T]):
    """@lifetime >= 0.3.55a2 // Generic version of `itertools.chain`"""
    
class AVT_Combinations(combinations, Generic[_T_cov]):
    """@lifetime >= 0.3.55a2 // Generic version of `itertools.combinations`"""
    
class AVT_CombinationsReplacement(combinations_with_replacement, Generic[_T_cov]):
    """@lifetime >= 0.3.55a2 // Generic version of `itertools.combinations_with_replacement`"""
    
class AVT_Compress(compress, Generic[_T]):
    """@lifetime >= 0.3.55a2 // Generic version of `itertools.compress`"""
    
class AVT_Count(count, Generic[_N]):
    """@lifetime >= 0.3.55a2 // Generic version of `itertools.count`"""
    
class AVT_Cycle(cycle, Generic[_T]):
    """@lifetime >= 0.3.55a2 // Generic version of `itertools.cycle`"""
    
class AVT_DropWhile(dropwhile, Generic[_T]):
    """@lifetime >= 0.3.55a2 // Generic version of `itertools.dropwhile`"""
    
class AVT_FilterFalse(filterfalse, Generic[_T]):
    """@lifetime >= 0.3.55a2 // Generic version of `itertools.filterfalse`"""
    
class AVT_GroupBy(groupby, Generic[_T1_cov, _T2_cov]):
    """@lifetime >= 0.3.55a2 // Generic version of `itertools.groupby`"""
    
class AVT_Islice(islice, Generic[_T]):
    """@lifetime >= 0.3.55a2 // Generic version of `itertools.islice`"""
    
class AVT_Pairwise(pairwise, Generic[_T_cov]):
    """
    @lifetime >= 0.3.55a2 // Generic version of `itertools.pairwise`
    
    `pairwise` exists since 3.10, and it is backported
    """
    
class AVT_Permutations(permutations, Generic[_T_cov]):
    """@lifetime >= 0.3.55a2 // Generic version of `itertools.permutations`"""
    
class AVT_Product(product, Generic[_T_cov]):
    """@lifetime >= 0.3.55a2 // Generic version of `itertools.product`"""
    
class AVT_Repeat(repeat, Generic[_T]):
    """@lifetime >= 0.3.55a2 // Generic version of `itertools.repeat`"""
    
class AVT_StarMap(starmap, Generic[_T_cov]):
    """@lifetime >= 0.3.55a2 // Generic version of `itertools.starmap`"""
    
class AVT_TakeWhile(takewhile, Generic[_T]):
    """@lifetime >= 0.3.55a2 // Generic version of `itertools.takewhile`"""
    
class AVT_ZipLongest(zip_longest, Generic[_T_cov]):
    """@lifetime >= 0.3.55a2 // Generic version of `itertools.zip_longest`"""
    
_prevent_unused_imports(
    AVT_Accumulate,
    AVT_Array,
    AVT_AsyncContextManager,
    AVT_AsyncGenerator,
    AVT_AsyncIterable,
    AVT_AsyncIterator,
    AVT_Awaitable,
    AVT_Batched,
    AVT_Callable,
    AVT_Chain,
    AVT_ChainMap,
    AVT_Collection,
    AVT_Combinations,
    AVT_CombinationsReplacement,
    AVT_Compress,
    AVT_Container,
    AVT_ContextManager,
    AVT_Coroutine,
    AVT_Count,
    AVT_Counter,
    AVT_Cycle,
    AVT_DefaultDict,
    AVT_Deque,
    AVT_Dict,
    AVT_DropWhile,
    AVT_Enumerate,
    AVT_Filter,
    AVT_FilterFalse,
    AVT_FrozenSet,
    AVT_Generator,
    AVT_GenericAlias,
    AVT_GroupBy,
    AVT_Islice,
    AVT_ItemsView,
    AVT_Iterable,
    AVT_Iterator,
    AVT_KeysView,
    AVT_List,
    AVT_Map,
    AVT_Mapping,
    AVT_MappingView,
    AVT_Match,
    AVT_MemoryView,
    AVT_MutableMapping,
    AVT_MutableSequence,
    AVT_MutableUniqual,
    AVT_OrderedDict,
    AVT_Pairwise,
    AVT_PathLike,
    AVT_Pattern,
    AVT_Permutations,
    AVT_Product,
    AVT_Repeat,
    AVT_Reversed,
    AVT_Reversible,
    AVT_Sequence,
    AVT_Set,
    AVT_StarMap,
    AVT_TakeWhile,
    AVT_Tuple,
    AVT_Type,
    AVT_UnionType,
    AVT_Uniqual,
    AVT_ValuesView,
    AVT_Zip,
    AVT_ZipLongest
)

### Protocol Classes ###

@runtime
class NextOperable(Protocol[_T_cov]):
    """
    @lifetime >= 0.3.26b3 // `_typeshed.SupportsNext`

    A protocol class with magic method `__next__` that equals `next(self)`. \\
    Returned type is addicted to covariant type parameter.
    """
    def __next__(self) -> _T_cov: ...

@runtime
class AsyncNextOperable(Protocol[_T_cov]):
    """
    @lifetime >= 0.3.26b3 // `_typeshed.SupportsAnext`

    A protocol class with magic method `__anext__`. Returned type must be an awaitable \\
    of type represented by covariant type parameter.
    """
    def __anext__(self) -> Awaitable[_T_cov]: ... # 0.3.60: remove 'async' keyword
    
@runtime
class ExitOperable(Protocol):
    """
    @lifetime >= 0.3.26b3

    A protocol class with magic method `__exit__`. Returned type is addicted to covariant type parameter.
    """
    def __exit__(
        self,
        exc_type: Optional[AVT_Type[Exception]] = None,
        exc_value: Optional[Exception] = None,
        traceback: Optional[TracebackType] = None
    ) -> bool: ...

@runtime
class AsyncExitOperable(Protocol[_T_cov]):
    """
    @lifetime >= 0.3.26b3

    A protocol class with magic method `__aexit__`. Returned type must be an awaitable \\
    of type represented by covariant type parameter.
    """
    async def __aexit__(
        self,
        exc_type: Optional[AVT_Type[Exception]] = None,
        exc_value: Optional[Exception] = None,
        traceback: Optional[TracebackType] = None
    ) -> Awaitable[_T_cov]: ...

@runtime
class EnterOperable(Protocol[_T_cov]):
    """
    @lifetime >= 0.3.26b3

    A protocol class with magic method `__enter__`. Returned type is addicted to covariant type parameter.
    """
    def __enter__(self) -> _T_cov: ...

@runtime
class AsyncEnterOperable(Protocol[_T_cov]):
    """
    @lifetime >= 0.3.26b3

    A protocol class with magic method `__aenter__`. Returned type must be an awaitable \\
    of type represented by covariant type parameter.
    """
    async def __aenter__(self) -> Awaitable[_T_cov]: ...
    
@runtime
class ItemGetter(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc3 // `_typeshed.SupportsGetItem`

    A protocol class with one method `__getitem__`. Type parameters:
    - first equals type for `key`
    - second equals returned type

    This method is invoked whether we want to get value \\
    via index notation `self[key]`, as instance of the class.
    """
    def __getitem__(self, key: _T_con, /) -> _T_cov: ...

if _sys.version_info >= (3, 9):
    
    @runtime
    class ClassItemGetter(Protocol):
        """
        @lifetime >= 0.3.26rc3

        A protocol class with one method `__class_getitem__`. No type parameters.

        This method is invoked whether we want to get value \\
        via index notation `self[key]`, as reference to the class.
        """
        def __class_getitem__(cls, args: Any, /) -> GenericAlias: ...

class SizeableItemGetter(Sized, ItemGetter[int, _T_cov]):
    """
    @lifetime >= 0.3.27a3 // `_typeshed.SupportsLenAndGetItem`

    A protocol class with methods `__len__` and `__getitem__`. Type parameters:
    - first equals returned type for `__getitem__`
    """

@runtime
class ItemSetter(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc3

    A protocol class with one method `__setitem__`. Type parameters:
    - first equals type for `key`
    - second equals type for `value`

    This method is invoked whether we want to set a new value for \\
    specific item accessed by `key`, as `self[key] = value`.
    """
    def __setitem__(self, key: _T_con, value: _T_cov, /) -> None: ...

@runtime
class ItemDeleter(Protocol[_T_con]):
    """
    @lifetime >= 0.3.26rc3

    A protocol class with one method `__delitem__`. Type parameters:
    - first equals type for `key`

    This method is invoked whether we want to delete specific item \\
    using `del` keyword as `del self[key]`.
    """
    def __delitem__(self, key: _T_con, /) -> None: ...
    
class ItemManager(
    ItemGetter[_T_con, _T_cov],
    ItemSetter[_T_con, _T_cov],
    ItemDeleter[_T_con]
):
    """
    @lifetime >= 0.3.26rc3

    A protocol class with following methods:
    - `__getitem__` - two type parameters (key type, return type)
    - `__setitem__` - two type parameters (key type, return type)
    - `__delitem__` - one type parameter (key type)
    """
    ...

@runtime
class Getter(Protocol[_T_cov]):
    """
    @lifetime >= 0.3.26

    A protocol class with one method `__get__`. Type parameters:
    - first equals returned type
    """
    def __get__(self, instance: object, owner: Optional[type] = None, /) -> _T_cov: ...

@runtime
class Setter(Protocol[_T_con]):
    """
    @lifetime >= 0.3.27a3

    A protocol class with one method `__set__`. Type parameters:
    - first equals type for `value`
    """
    def __set__(self, instance: object, value: _T_con, /) -> None: ...
    
@runtime
class Deleter(Protocol):
    """
    @lifetime >= 0.3.44
    
    A protocol class with one method `__delete__`. No type parameters.
    """
    def __delete__(self, instance: object, /) -> None: ...
    
class Descriptor(
    Setter[_T_con],
    Getter[_T_cov],
    Deleter
):
    """
    @lifetime >= 0.3.44
    
    A protocol class with descriptor methods: `__get__`, `__set__` and `__delete__`
    """
    ...

@runtime
class FinalDescriptor(Protocol[_T_cov]):
    """
    @lifetime >= 0.3.44
    
    A protocol class providing descriptor methods, just `__set__` and `__delete__` throw an error. \\
    The same as `~.util.finalproperty` works.
    """
    def __get__(self, instance: Optional[object], owner: Optional[type] = None, /) -> _T_cov: ...
    def __set__(self, instance: Optional[object], value: Any, /) -> NoReturn: ...
    def __delete__(self, instance: Optional[object], /) -> NoReturn: ...

class KeysProvider(ItemGetter[_KT_con, Any]):
    """
    @lifetime >= 0.3.26

    A protocol class with method `keys()`. Type parameters:
    - first equals key
    - second equals value
    """
    def keys(self) -> AVT_Iterable[_KT_con]: ...

@runtime
class ItemsProvider(Protocol[_KT_cov, _VT_cov]):
    """
    @lifetime >= 0.3.26

    A protocol class with method `items()`. Type parameters:
    - first equals key
    - second equals value
    """
    def items(self) -> AVT_Uniqual[AVT_Tuple[_KT_cov, _VT_cov]]: ...
    
@runtime
class Buffer(Protocol):
    """
    @lifetime >= 0.3.44
    
    A protocol class with one method `__buffer__`.
    """
    def __buffer__(self, flags: int, /) -> memoryview: ...
    
Buffer = _Buffer

@runtime
class BufferReleaser(Protocol):
    """
    @lifetime >= 0.3.26

    A protocol class with one method `__release_buffer__`.
    """
    def __release_buffer__(self, buffer: memoryview, /) -> None: ...
    
# >= 0.3.44; < 0.3.54 as 'BufferManager'
@runtime
class BufferProtocol(Protocol):
    """
    @lifetime >= 0.3.54
    
    This protocol class allows to implement buffer protocol to specific class
    """
    def __buffer__(self, flags: int, /) -> memoryview: ...
    def __release_buffer__(self, buffer: memoryview, /) -> None: ...

@runtime
class NewArgumentsGetter(Protocol[_T_cov]):
    """
    @lifetime >= 0.3.26

    A protocol class with one method `__getnewargs__`. Type parameters:
    - first equals type for returned tuple
    """
    def __getnewargs__(self) -> AVT_Tuple[_T_cov]: ...

@runtime
class SubclassHooker(Protocol):
    """
    @lifetime >= 0.3.26

    A protocol class with one method `__subclasshook__`. No type parameters.

    Description: \\
    "Abstract classes can override this to customize `issubclass()`. \\
    This is invoked early on by `abc.ABCMeta.__subclasscheck__()`. \\
    It should return True, False or NotImplemented. If it returns \\
    NotImplemented, the normal algorithm is used. Otherwise, it \\
    overrides the normal algorithm (and the outcome is cached)."
    """
    def __subclasshook__(cls, subclass: type, /) -> bool: ...

@runtime
class LengthHintProvider(Protocol):
    """
    @lifetime >= 0.3.26rc3

    A protocol class with one method `__length_hint__`. No type parameters.

    This method is invoked like in case of `list` built-in, just on behalf of specific class. \\
    It should equal invoking `len(self)`, as seen for `list`: "Private method returning \\
    an estimate of `len(list(it))`".
    """
    def __length_hint__(self) -> int: ...

FSPathProvider = AVT_PathLike
"""@lifetime >= 0.3.27a3"""

@runtime
class BytearrayConvertible(Protocol):
    """
    @lifetime >= 0.3.26rc3

    An unofficial ABC with one method `__bytearray__`, which *has* to equal invoking `bytearray(self)`.
    """
    def __bytearray__(self) -> bytearray: ...

@runtime
class ListConvertible(Protocol[_T_cov]):
    """
    @lifetime >= 0.3.26rc3

    An unofficial ABC with one method `__tlist__` (before 0.3.27a3 - `__list__`), which *has* to equal invoking `list(self)`. \\
    Returned list type is addicted to covariant type parameter.
    """
    
    def __tlist__(self) -> AVT_List[_T_cov]:
        "@lifetime >= 0.3.26rc3. Return `list(self)`"
        ...

@runtime
class TupleConvertible(Protocol[_T_cov]):
    """
    @lifetime >= 0.3.26rc3

    An unofficial ABC with one method `__ttuple__` (before 0.3.27a3 - `__tuple__`), which *has* to equal invoking `tuple(self)`. \\
    Returned tuple type is addicted to covariant type parameter.
    """
    
    def __ttuple__(self) -> AVT_Tuple[_T_cov, ...]:
        "@lifetime >= 0.3.26rc3. Return `tuple(self)`"
        ...

@runtime
class SetConvertible(Protocol[_T_cov]):
    """
    @lifetime >= 0.3.26rc3

    An unofficial ABC with one method `__tset__` (before 0.3.27a3 - `__set_init__`), which *has* to equal invoking `set(self)`. \\
    Returned set type is addicted to covariant type parameter.
    """
    
    def __tset__(self) -> AVT_Set[_T_cov]:
        "@lifetime >= 0.3.26rc3. Return `set(self)`"
        ...

@runtime
class ReckonOperable(Protocol):
    """
    @lifetime >= 0.3.26rc1

    An unofficial ABC with one method `__reckon__` that equals `aveytense.reckon(self)`. \\
    Returned type is always an integer.
    """
    def __reckon__(self) -> int:
        """
        @lifetime >= 0.3.26rc1

        Return `reckon(self)`.
        """
        ...

@runtime
class Absolute(Protocol[_T_cov]):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__abs__` that equals invoking `abs(self)`. \\
    Returned type is addicted to covariant type parameter.
    """
    def __abs__(self) -> _T_cov: ...

@runtime
class Truncable(Protocol[_T_cov]):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__trunc__` that equals invoking `math.trunc(self)`. \\
    Returned type is addicted to covariant type parameter.
    """
    def __trunc__(self) -> _T_cov: ...

@runtime
class BooleanConvertible(Protocol):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__bool__` that equals invoking `bool(self)`.
    """
    # >= ^; < 0.3.44; where ^ is version of this class definition, had additional method __nonzero__ (removed since it is for Python 2)
    def __bool__(self) -> bool: ...

@runtime
class IntegerConvertible(Protocol):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__int__` that equals invoking `int(self)`
    """
    def __int__(self) -> int: ...

@runtime
class FloatConvertible(Protocol):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__float__` that equals invoking `float(self)`
    """
    def __float__(self) -> float: ...

@runtime
class ComplexConvertible(Protocol):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__complex__` that equals invoking `complex(self)`
    """
    def __complex__(self) -> complex: ...

@runtime
class BytesConvertible(Protocol):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__bytes__` that equals invoking `bytes(self)`
    """
    def __bytes__(self) -> bytes: ...

@runtime
class BinaryRepresentable(Protocol):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one unofficial method `__bin__` that has to equal invoking `bin(self)`
    """
    def __bin__(self) -> str: ...

@runtime
class OctalRepresentable(Protocol):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__oct__` that equals invoking `oct(self)`
    """
    def __oct__(self) -> str: ...

@runtime
class HexadecimalRepresentable(Protocol):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__hex__` that equals invoking `hex(self)`
    """
    def __hex__(self) -> str: ...

@runtime
class StringConvertible(Protocol):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__str__` that equals invoking `str(self)`
    """
    def __str__(self) -> str: ...

@runtime
class Representable(Protocol):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__repr__` that equals invoking `repr(self)`
    """
    def __repr__(self) -> str: ...

@runtime
class Indexable(Protocol):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__index__`. This allows to use self inside slice expressions, \\
    those are: `slice(self, ..., ...)` and `iterable[self: ... : ...]` (`self` can be \\
    placed anywhere)
    """
    def __index__(self) -> int: ...

@runtime
class Positive(Protocol[_T_cov]):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__pos__` that equals `+self`. \\
    Returned type is addicted to covariant type parameter.
    """
    def __pos__(self) -> _T_cov: ...

@runtime
class Negative(Protocol[_T_cov]):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__neg__` that equals `-self`. \\
    Returned type is addicted to covariant type parameter.
    """
    def __neg__(self) -> _T_cov: ...

@runtime
class Invertible(Protocol[_T_cov]):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__invert__` that equals `~self`. \\
    Returned type is addicted to covariant type parameter.
    """
    def __invert__(self) -> _T_cov: ...

BufferOperable = Buffer
"@lifetime >= 0.3.26rc1. *aveytense.extensions.Buffer*"

@runtime
class LeastComparable(Protocol[_T_con]):
    """
    @lifetime >= 0.3.26b3

    Can be compared with `<`
    """
    def __lt__(self, other: _T_con) -> bool: ...

@runtime
class GreaterComparable(Protocol[_T_con]):
    """
    @lifetime >= 0.3.26b3

    Can be compared with `>`
    """
    def __gt__(self, other: _T_con) -> bool: ...

@runtime
class LeastEqualComparable(Protocol[_T_con]):
    """
    @lifetime >= 0.3.26b3

    Can be compared with `<=`
    """
    def __le__(self, other: _T_con) -> bool: ...

@runtime
class GreaterEqualComparable(Protocol[_T_con]):
    """
    @lifetime >= 0.3.26b3

    Can be compared with `>=`
    """
    def __ge__(self, other: _T_con) -> bool: ...

@runtime
class EqualComparable(Protocol[_T_con]):
    """
    @lifetime >= 0.3.26rc1

    Can be compared with `==`
    """
    def __eq__(self, other: _T_con) -> bool: ...

@runtime
class InequalComparable(Protocol[_T_con]):
    """
    @lifetime >= 0.3.26rc1

    Can be compared with `!=`
    """
    def __ne__(self, other: _T_con) -> bool: ...


class Comparable(
    LeastComparable[Any],
    GreaterComparable[Any],
    LeastEqualComparable[Any],
    GreaterEqualComparable[Any],
    EqualComparable[Any],
    InequalComparable[Any],
    AVT_Container[Any]
):
    """
    @lifetime >= 0.3.26b3

    An ABC supporting any form of comparison with operators \\
    `>`, `<`, `>=`, `<=`, `==`, `!=`, `in` (last 3 missing before 0.3.26rc1)
    """
    ...

class ComparableWithoutIn(
    LeastComparable[Any],
    GreaterComparable[Any],
    LeastEqualComparable[Any],
    GreaterEqualComparable[Any],
    EqualComparable[Any]
):
    """
    @lifetime >= 0.3.27a2

    An ABC same as `Comparable`, but without the `in` keyword support
    """
    ...

@runtime
class BitwiseAndOperable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__and__` that equals `self & other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __and__(self, other: _T_con) -> _T_cov: ...

@runtime
class BitwiseOrOperable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__or__` that equals `self | other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __or__(self, other: _T_con) -> _T_cov: ...

@runtime
class BitwiseXorOperable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__xor__` that equals `self ^ other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __xor__(self, other: _T_con) -> _T_cov: ...

@runtime
class BitwiseLeftOperable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__lshift__` that equals `self << other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __lshift__(self, other: _T_con) -> _T_cov: ...

@runtime
class BitwiseRightOperable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__rshift__` that equals `self >> other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __rshift__(self, other: _T_con) -> _T_cov: ...

class BitwiseOperable(
    BitwiseAndOperable[Any, Any],
    BitwiseOrOperable[Any, Any],
    BitwiseXorOperable[Any, Any],
    BitwiseLeftOperable[Any, Any],
    BitwiseRightOperable[Any, Any]
):
    """
    @lifetime >= 0.3.26rc1

    Can be used with `&`, `|`, `^`, `<<` and `>>` operators
    """
    ...

@runtime
class BitwiseAndReassignable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__iand__` that equals `self &= other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __iand__(self, other: _T_con) -> _T_cov: ...

@runtime
class BitwiseOrReassignable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__ior__` that equals `self |= other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __ior__(self, other: _T_con) -> _T_cov: ...

@runtime
class BitwiseXorReassignable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__ixor__` that equals `self ^= other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __ixor__(self, other: _T_con) -> _T_cov: ...

@runtime
class BitwiseLeftReassignable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__ilshift__` that equals `self <<= other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __ilshift__(self, other: _T_con) -> _T_cov: ...

@runtime
class BitwiseRightReassignable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__irshift__` that equals `self >>= other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __irshift__(self, other: _T_con) -> _T_cov: ...

class BitwiseReassignable(
    BitwiseAndOperable[Any, Any],
    BitwiseOrOperable[Any, Any],
    BitwiseXorOperable[Any, Any],
    BitwiseLeftReassignable[Any, Any],
    BitwiseRightReassignable[Any, Any]):
    """
    @lifetime >= 0.3.26rc1

    Can be used with `&=`, `|=`, `^=`, `<<=` and `>>=` operators
    """
    ...

class BitwiseCollection(
    BitwiseReassignable,
    BitwiseOperable
):
    """
    @lifetime >= 0.3.26rc1

    Can be used with `&`, `|` and `^` operators, including their \\
    augmented forms: `&=`, `|=` and `^=`, with `~` use following::

        class Example(BitwiseCollection, Invertible[_T]): ...
    """
    ...

class UnaryOperable(Positive[Any], Negative[Any], Invertible[Any]):
    """
    @lifetime >= 0.3.26rc1

    Can be used with `+`, `-` and `~` operators preceding the type
    """
    ...

class Indexed(ItemGetter[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc2
    
    A protocol class with one method `__getitem__` that equals `self[key]`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `key` parameter.
    """
    ...

@runtime
class Ceilable(Protocol[_T_cov]):
    """
    @lifetime >= 0.3.26b3

    A protocol class with magic method `__ceil__` that equals `ceil(self)`. \\
    Returned type is addicted to covariant type parameter.
    """
    def __ceil__(self) -> _T_cov: ...

@runtime
class Floorable(Protocol[_T_cov]):
    """
    @lifetime >= 0.3.26b3

    A protocol class with magic method `__floor__` that equals `floor(self)`. \\
    Returned type is addicted to covariant type parameter.
    """
    def __floor__(self) -> _T_cov: ...

@runtime
class Roundable(Protocol[_T_cov]):
    """
    @lifetime >= 0.3.26b3

    A protocol class with magic method `__round__` that equals `round(self)`. \\
    Returned type is addicted to covariant type parameter.
    """
    def __round__(self, ndigits: Optional[int] = None) -> _T_cov: ...

CeilOperable = Ceilable
FloorOperable = Floorable
RoundOperable = Roundable

@runtime
class AdditionOperable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__add__` that equals `self + other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __add__(self, other: _T_con) -> _T_cov: ...

@runtime
class SubtractionOperable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__sub__` that equals `self - other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __sub__(self, other: _T_con) -> _T_cov: ...

@runtime
class MultiplicationOperable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__mul__` that equals `self * other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __mul__(self, other: _T_con) -> _T_cov: ...

@runtime
class MatrixMultiplicationOperable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__matmul__` that equals `self @ other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __matmul__(self, other: _T_con) -> _T_cov: ...

@runtime
class TrueDivisionOperable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__truediv__` that equals `self / other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __truediv__(self, other: _T_con) -> _T_cov: ...

@runtime
class FloorDivisionOperable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__floordiv__` that equals `self // other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __floordiv__(self, other: _T_con) -> _T_cov: ...

@runtime
class DivmodOperable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__divmod__` that equals `divmod(self, other)`. \\
    Returned type is addicted to covariant type parameter as the second type parameter \\
    first is type for `other` parameter.
    """
    def __divmod__(self, other: _T_con) -> _T_cov: ...

@runtime
class ModuloOperable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__mod__` that equals `self % other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __mod__(self, other: _T_con) -> _T_cov: ...

@runtime
class ExponentiationOperable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__pow__` that equals `self ** other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __pow__(self, other: _T_con) -> _T_cov: ...

@runtime
class ReflectedAdditionOperable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__radd__` that equals `other + self`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __radd__(self, other: _T_con) -> _T_cov: ...

@runtime
class ReflectedSubtractionOperable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__rsub__` that equals `other - self`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __rsub__(self, other: _T_con) -> _T_cov: ...

@runtime
class ReflectedMultiplicationOperable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__rmul__` that equals `other * self`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __rmul__(self, other: _T_con) -> _T_cov: ...

@runtime
class ReflectedMatrixMultiplicationOperable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__rmatmul__` that equals `other @ self`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __rmatmul__(self, other: _T_con) -> _T_cov: ...

@runtime
class ReflectedTrueDivisionOperable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__rtruediv__` that equals `other / self`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __rtruediv__(self, other: _T_con) -> _T_cov: ...

@runtime
class ReflectedFloorDivisionOperable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__rfloordiv__` that equals `other // self`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __rfloordiv__(self, other: _T_con) -> _T_cov: ...

@runtime
class ReflectedDivmodOperable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__rdivmod__` that equals `divmod(other, self)`. \\
    Returned type is addicted to covariant type parameter as the second type parameter; \\
    first is type for `other` parameter.
    """
    def __rdivmod__(self, other: _T_con) -> _T_cov: ...

@runtime
class ReflectedModuloOperable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__rmod__` that equals `other % self`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __rmod__(self, other: _T_con) -> _T_cov: ...

@runtime
class ReflectedExponentiationOperable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__rpow__` that equals `other ** self`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __rpow__(self, other: _T_con) -> _T_cov: ...

@runtime
class AdditionReassignable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__iadd__` that equals `self += other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __iadd__(self, other: _T_con) -> _T_cov: ...

@runtime
class SubtractionReassignable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__isub__` that equals `self -= other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __isub__(self, other: _T_con) -> _T_cov: ...

@runtime
class MultiplicationReassignable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__imul__` that equals `self *= other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __imul__(self, other: _T_con) -> _T_cov: ...

@runtime
class MatrixMultiplicationReassignable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__imatmul__` that equals `self @= other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __imatmul__(self, other: _T_con) -> _T_cov: ...

@runtime
class TrueDivisionReassingable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__itruediv__` that equals `self /= other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __itruediv__(self, other: _T_con) -> _T_cov: ...

@runtime
class FloorDivisionReassignable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__ifloordiv__` that equals `self //= other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __ifloordiv__(self, other: _T_con) -> _T_cov: ...

@runtime
class ModuloReassignable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__imod__` that equals `self %= other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __imod__(self, other: _T_con) -> _T_cov: ...

@runtime
class ExponentiationReassignable(Protocol[_T_con, _T_cov]):
    """
    @lifetime >= 0.3.26rc1
    
    A protocol class with magic method `__ipow__` that equals `self **= other`. \\
    Returned type is addicted to covariant type parameter as the second \\
    type parameter; first is type for `other` parameter.
    """
    def __ipow__(self, other: _T_con) -> _T_cov: ...

class ReflectedArithmeticOperable(
    ReflectedAdditionOperable[Any, Any],
    ReflectedSubtractionOperable[Any, Any],
    ReflectedMultiplicationOperable[Any, Any],
    ReflectedMatrixMultiplicationOperable[Any, Any],
    ReflectedTrueDivisionOperable[Any, Any],
    ReflectedFloorDivisionOperable[Any, Any],
    ReflectedDivmodOperable[Any, Any],
    ReflectedModuloOperable[Any, Any]
):
    """
    @lifetime >= 0.3.26rc1

    An ABC supporting every kind (except bitwise) of reflected arithmetic operations with following operators:
    ```
        + - * @ / // % ** divmod
    ```
    where left operand is `other` and right is `self`
    """
    ...

class ArithmeticOperable(
    AdditionOperable[Any, Any],
    SubtractionOperable[Any, Any],
    MultiplicationOperable[Any, Any],
    MatrixMultiplicationOperable[Any, Any],
    TrueDivisionOperable[Any, Any],
    FloorDivisionOperable[Any, Any],
    DivmodOperable[Any, Any],
    ModuloOperable[Any, Any],
    ExponentiationOperable[Any, Any],
    ReflectedArithmeticOperable
):
    """
    @lifetime >= 0.3.26rc1

    An ABC supporting every kind (except bitwise) of arithmetic operations, including their \\
    reflected equivalents, with following operators:
    ```
        + - * @ / // % ** divmod
    ```
    Both `self` and `other` can be either left or right operands.
    """
    ...

class ArithmeticReassignable(
    AdditionReassignable[Any, Any],
    SubtractionReassignable[Any, Any],
    MultiplicationReassignable[Any, Any],
    MatrixMultiplicationReassignable[Any, Any],
    TrueDivisionReassingable[Any, Any],
    FloorDivisionReassignable[Any, Any],
    ModuloReassignable[Any, Any],
    ExponentiationReassignable[Any, Any]
):
    """
    @lifetime >= 0.3.26rc1

    An ABC supporting every kind (except bitwise) of augmented/re-assigned arithmetic operations \\
    with following operators:
    ```
        += -= *= @= /= //= %= **=
    ```
    """
    ...

class ArithmeticCollection(
    ArithmeticOperable,
    ArithmeticReassignable
):
    """
    @lifetime >= 0.3.26rc1

    An ABC supporting every kind (except bitwise) of augmented/re-assigned and normal arithmetic operations \\
    with following operators:
    ```
        + - * @ / // % ** divmod += -= *= @= /= //= %= **=
    ```
    """
    ...

class OperatorCollection(
    ArithmeticCollection,
    BitwiseCollection,
    UnaryOperable,
    Comparable
):
    """
    @lifetime >= 0.3.26rc1

    An ABC supporting every kind of augmented/re-assigned, reflected and normal arithmetic operations \\
    with following operators:
    ```
        + - * @ / // % ** divmod & | ^ += -= *= @= /= //= %= **= &= |= ^=
    ```
    unary assignment with `+`, `-` and `~`, and comparison with following operators:
    ```
        > < >= <= == != in
    ```
    """
    ...

class LenGetItemOperable(Sized, ItemGetter[int, _T_cov]): # _typeshed.SupportsLenAndGetItem
    """
    @lifetime >= 0.3.26rc2
    
    A protocol class with `__getitem__` and `__len__` methods. Those are typical in sequences.
    """
    ...

@runtime
class Formattable(Protocol):
    """
    @lifetime >= 0.3.26rc1

    A protocol class with one method `__format__` that equals invoking `format(self)`.
    """
    def __format__(self, format_spec: str = "") -> str: ...

@runtime
class Flushable(Protocol): # _typeshed.SupportsFlush
    """
    @lifetime >= 0.3.27b1

    A protocol class with one method `flush()`.
    """
    def flush(self) -> object: ...

@runtime
class Writable(Protocol[_T_con]): # _typeshed.SupportsWrite
    """
    @lifetime >= 0.3.27b1

    A protocol class with one method `write()`.
    """
    def write(self, data: _T_con, /) -> int: ...
    
@runtime
class Readable(Protocol[_T_cov]):
    """
    @lifetime >= 0.3.55b2
    
    A protocol class with one method `read()`
    """
    def read(self, size: int = ..., /) -> _T_cov: ...
    
@runtime
class FilenoProvider(Protocol):
    """
    @lifetime >= 0.3.60
    
    A protocol class with method `fileno()`
    """
    def fileno(self) -> int: ...
    
@runtime
class Copyable(Protocol):
    """
    @lifetime >= 0.3.34
    
    A protocol class with method `copy()`.
    """
    # >= 0.3.43; < 0.3.60 it was __copy__ instead; for __copy__ use Copyable2
    def copy(self) -> Self: ... 
    
@runtime
class Copyable2(Protocol):
    """
    @lifetime >= 0.3.60
    
    A protocol class with method `__copy__()`
    """
    def __copy__(self) -> Self: ...

@runtime
class DeepCopyable(Protocol):
    """
    @lifetime >= 0.3.43
    
    A protocol class with method `__deepcopy__()`.
    """
    def __deepcopy__(self, memo: Optional[AVT_Dict[int, Any]] = None) -> Self: ...
    
### NEGATIONS ###
    
@runtime
class NotIterable(Protocol):
    """
    @lifetime >= 0.3.26b3

    A protocol class disallowing iteration with `for` loop
    """
    __iter__ = None

@runtime
class NotCallable(Protocol[_T_cov]):
    """
    @lifetime >= 0.3.45

    A protocol class disallowing invoking its subclasses (`__call__()` throws an error)
    """
    __call__ = None
            
# NotInvocable = NotCallable # >= 0.3.26rc1; < 0.3.54

@runtime
class NotUnaryOperable(Protocol):
    """
    @lifetime >= 0.3.26rc1

    A protocol class indicating that its subclasses' objects cannot use unary operators `+`, `-` and `~`
    """
    def __pos__(self):
        _E(108, "")
        
    def __neg__(self):
        _E(108, "")
        
    def __invert__(self):
        _E(108, "")

@runtime
class NotReassignable(Protocol[_T_con]):
    """
    @lifetime >= 0.3.26b3

    A protocol class that doesn't support any form of re-assignment, those are augmented assignment
    operators: `+=`, `-=`, `*=`, `**=`, `/=`, `//=`, `%=`, `>>=`, `<<=`, `&=`, `|=`, `^=`. Setting new
    value also is prohibited.
    """
    __slots__ = ("__weakref__",)
    __op = (
        "; used operator '+='", # 0
        "; used operator '-='", # 1
        "; used operator '*='", # 2
        "; used operator '/='", # 3
        "; used operator '//='", # 4
        "; used operator '**='", # 5
        "; used operator '<<='", # 6
        "; used operator '>>='", # 7
        "; used operator '%='", # 8
        "; used operator '&='", # 9
        "; used operator '|='", # 10
        "; used operator '^='", # 11
    )
    
    def __set__(self, i: Self, v: _T_con):
        
        s = " variable that isn't assignable and re-assignable"
        _E(102, s)
            
    def __iadd__(self, o: _T_con):
        i = 0
        _E(102, self.__op[i])
        
    def __isub__(self, o: _T_con):
        i = 1
        _E(102, self.__op[i])
        
    def __imul__(self, o: _T_con):
        i = 2
        _E(102, self.__op[i])
        
    def __ifloordiv__(self, o: _T_con):
        i = 4
        _E(102, self.__op[i])
        
    def __idiv__(self, o: _T_con):
        i = 3
        _E(102, self.__op[i])
        
    def __itruediv__(self, o: _T_con):
        i = 3
        _E(102, self.__op[i])
        
    def __imod__(self, o: _T_con):
        i = 8
        _E(102, self.__op[i])
        
    def __ipow__(self, o: _T_con):
        i = 5
        _E(102, self.__op[i])
        
    def __ilshift__(self, o: _T_con):
        i = 6
        _E(102, self.__op[i])
        
    def __irshift__(self, o: _T_con):
        i = 7
        _E(102, self.__op[i])
        
    def __iand__(self, o: _T_con):
        i = 9
        _E(102, self.__op[i])
        
    def __ior__(self, o: _T_con):
        i = 10
        _E(102, self.__op[i])
        
    def __ixor__(self, o: _T_con):
        i = 11
        _E(102, self.__op[i])

@runtime
class NotComparable(Protocol[_T_con]):
    """
    @lifetime >= 0.3.26b3

    A protocol class for subclasses disallowing using comparison operators `==`, `!=`, `>`, `<`, `>=`, `<=`, `in`
    """
    __slots__ = ()
    __op = (
        "; used operator '<'", # 0
        "; used operator '>'", # 1
        "; used operator '<='", # 2
        "; used operator '>='", # 3
        "; used operator '=='", # 4
        "; used operator '!='", # 5
        "; used operator 'in'", # 6
    )
    def __lt__(self, other: _T_con):
        i = 0
        _E(102, self.__op[i])
        
    def __gt__(self, other: _T_con):
        i = 1
        _E(102, self.__op[i])
        
    def __le__(self, other: _T_con):
        i = 2
        _E(102, self.__op[i])
        
    def __ge__(self, other: _T_con):
        i = 3
        _E(102, self.__op[i])
        
    def __eq__(self, other: _T_con):
        i = 4
        _E(102, self.__op[i])
        
    def __ne__(self, other: _T_con):
        i = 5
        _E(102, self.__op[i])
        
    def __contains__(self, other: _T_con):
        i = 6
        _E(102, self.__op[i])
    
class Allocator:
    """
    @lifetime >= 0.3.27b3

    An allocator class. Classes extending this class have access to `__alloc__` magic method, \\
    but it is advisable to use it wisely.
    """
    __a = bytearray()

    def __init__(self, b: Union[bytearray, BytearrayConvertible], /):
        
        if isinstance(b, BytearrayConvertible):
            self.__a = b.__bytearray__()
            
        elif isinstance(b, bytearray):
            self.__a = b
            
        else:
            error = TypeError("Expected a bytearray object or object of class extending 'BytearrayConvertible' class")
            raise error
    
    def __alloc__(self):
        return self.__a.__alloc__()
    
class AwaitableGenerator(
    AVT_Awaitable[_T_return_noDefault_cov],
    AVT_Generator[_T_yield_cov, _T_send_noDefault_con, _T_return_noDefault_cov],
    Generic[_T_yield_cov, _T_send_noDefault_con, _T_return_noDefault_cov, _T],
    metaclass = ABCMeta
):
    """
    @lifetime >= 0.3.58 // `_typeshed._type_checker.AwaitableGenerator`
    """
    ...

### Array Typecode & Memoryview Format Types ###

ArrayIntegerTypecodes: TypeAlias = Literal["b", "B", "h", "H", "i", "I", "l", "L", "q", "Q"] # >= 0.3.60
ArrayFloatTypecodes: TypeAlias = Literal["f", "d"] # >= 0.3.60
if _sys.version_info >= (3, 16): # >= 0.3.60 (all versions)
    ArrayUnicodeTypecodes: TypeAlias = Literal["w"]
elif _sys.version_info >= (3, 13):
    ArrayUnicodeTypecodes: TypeAlias = Literal["u", "w"]
else:
    ArrayUnicodeTypecodes: TypeAlias = Literal["u"]
ArrayTypecodes: TypeAlias = Union[ArrayIntegerTypecodes, ArrayFloatTypecodes, ArrayUnicodeTypecodes] # >= 0.3.60

MemoryViewIntegerFormats: TypeAlias = Literal["b", "B", "@b", "@B", "h", "H", "@h", "@H", "i", "I", "@i", "@I", "l", "L", "@l", "@L", "q", "Q", "@q", "@Q", "P", "@P"] # >= 0.3.60
MemoryViewFloatFormats: TypeAlias = Literal["f", "@f", "d", "@d"] # >= 0.3.60
MemoryViewBytesFormats: TypeAlias = Literal["c", "@c"] # >= 0.3.60
MemoryViewBooleanFormats: TypeAlias = Literal["?"] # >= 0.3.60

### File Types ###

FileBinaryModeUpdating: TypeAlias = Literal[ # >= 0.3.59 // _typeshed.OpenBinaryModeUpdating
    "rb+", "r+b", "+rb", "br+", "b+r", "+br",
    "wb+", "w+b", "+wb", "bw+", "b+w", "+bw",
    "ab+", "a+b", "+ab", "ba+", "b+a", "+ba",
    "xb+", "x+b", "+xb", "bx+", "b+x", "+bx"
]
FileBinaryModeReading: TypeAlias = Literal["rb", "br", "rbU", "rUb", "Urb", "brU", "bUr", "Ubr"] # >= 0.3.59 // _typeshed.OpenBinaryModeReading
FileBinaryModeWriting: TypeAlias = Literal["wb", "bw", "ab", "ba", "xb", "bx"] # >= 0.3.59 // _typeshed.OpenBinaryModeWriting
FileBinaryMode: TypeAlias = Union[FileBinaryModeUpdating, FileBinaryModeReading, FileBinaryModeWriting] # >= 0.3.59 // _typeshed.OpenBinaryMode
FileGenericPath: TypeAlias = Union[AnyStr, AVT_PathLike[AnyStr]] # >= 0.3.59 // _typeshed.GenericPath
FilePath: TypeAlias = Union[FileGenericPath[str], FileGenericPath[bytes]] # >= 0.3.59 // _typeshed.StrOrBytesPath
FileTextModeUpdating: TypeAlias = Literal[ # >= 0.3.59 // _typeshed.OpenTextModeUpdating
    "r+", "+r", "rt+", "r+t", "+rt", "tr+", "t+r", "+tr",
    "w+", "+w", "wt+", "w+t", "+wt", "tw+", "t+w", "+tw",
    "a+", "+a", "at+", "a+t", "+at", "ta+", "t+a", "+ta",
    "x+", "+x", "xt+", "x+t", "+xt", "tx+", "t+x", "+tx"
] 
FileTextModeReading: TypeAlias = Literal["w", "wt", "tw", "a", "at", "ta", "x", "xt", "tx"] # >= 0.3.59 // _typeshed.OpenTextModeReading
FileTextModeWriting: TypeAlias = Literal["r", "rt", "tr", "U", "rU", "Ur", "rtU", "rUt", "Urt", "trU", "tUr", "Utr"] # >= 0.3.59 // _typeshed.OpenTextModeWriting
FileTextMode: TypeAlias = Union[FileTextModeUpdating, FileTextModeReading, FileTextModeWriting] # >= 0.3.59 // _typeshed.OpenTextMode
FileType: TypeAlias = Union[int, FilePath] # >= 0.3.26b3 // _typeshed.StrOrBytesPath


### Private classes from typing.py ###
# Use these with isinstance() to determine if these are desired special forms.

TypingAnnotatedType = type(Annotated[int, "$"]) # >= 0.3.52
TypingCallableType = type(AVT_Callable[..., Any]) # >= 0.3.52 // 'typing._GenericAlias': < Py3.9
TypingConcatenateType = type(Concatenate[int, _P]) # >= 0.3.52 // TypeError occurred until 0.3.53 ('typing.ParamSpec' missing before Py3.11, ellipsis was used instead)
TypingGenericType = type(TypeGuard[int]) # >= 0.3.52
TypingLiteralType = type(Literal[0]) # >= 0.3.52
TypingNoDefaultType = type(NoDefault) # >= 0.3.53
TypingUnionType = type(Union[int, str]) # >= 0.3.52 // 'typing._GenericAlias': < Py3.9 / 'types.UnionType': >= Py3.14
TypingUnpackType = type(Unpack[AVT_Tuple[int, str]]) # >= 0.3.52

# >> TypingSpecialGenericType: >= 0.3.59
# >> TypingExtensionsSpecialGenericType: >= 0.3.59
# NOTE: 'typing.Generator' (with other three) re-implemented in 'typing_extensions' exists for Python versions preceding 3.13 beta, defined as an instance of
# 'typing_extensions._SpecialGenericAlias'. 'typing_extensions' will import 'collections.abc.Generator' with 3 other abstract base classes when 3.13 beta or
# higher is used, meaning aforementioned internal class '_SpecialGenericAlias' won't be defined in 'typing_extensions' (excluding 'typing' that has this class
# since 3.9). 
if _sys.version_info >= (3, 9):
    TypingSpecialGenericType = type(_typing.Generator)
    if _sys.version_info < (3, 13, 0, "beta"):
        TypingExtensionsSpecialGenericType = type(_typing_ext.Generator)
else:
    TypingSpecialGenericType = type(_typing_ext.Generator)

# >> TypingTupleType: >= 0.3.53
# NOTE: Even if 'typing.Tuple' is deprecated since 3.9, it actually has an internal class that implements it. So I decided for version 0.3.54 to copy and paste
# its source code below (different for Py3.8 and Py3.9+ so both versions are included) in case Python removes the 'typing.Tuple' type alias.
if hasattr(_typing, "Tuple"):
    TypingTupleType = type(_typing.Tuple)
    
# (0.3.54)
elif _sys.version_info >= (3, 9):
    
    class TypingTupleType(TypingSpecialGenericType, _root=True):
        """
        @lifetime >= 0.3.53
        
        Internal class for tuple type alias `typing.Tuple`
        """
        
        @_typing._tp_cache
        def __getitem__(self, params):
            
            import typing
            
            if not isinstance(params, tuple):
                params = (params,)
            if len(params) >= 2 and params[-1] is ...:
                msg = "Tuple[t, ...]: t must be a type."
                params = tuple(typing._type_check(p, msg) for p in params[:-1])
                return self.copy_with((*params, typing._TypingEllipsis))
            msg = "Tuple[t0, t1, ...]: each t must be a type."
            params = tuple(typing._type_check(p, msg) for p in params)
            return self.copy_with(params)
else:
    class TypingTupleType(TypingGenericType, _root=True):
        """
        @lifetime >= 0.3.53
        
        Internal class for tuple type alias `typing.Tuple`
        """
        def __getitem__(self, params):
            if self._name != 'Callable' or not self._special:
                return self.__getitem_inner__(params)
            if not isinstance(params, tuple) or len(params) != 2:
                raise TypeError("Callable must be used as "
                                "Callable[[arg, ...], result].")
            args, result = params
            if args is Ellipsis:
                params = (Ellipsis, result)
            else:
                if not isinstance(args, list):
                    raise TypeError(f"Callable[args, result]: args must be a list."
                                    f" Got {args}")
                params = (tuple(args), result)
            return self.__getitem_inner__(params)

        @_typing._tp_cache
        def __getitem_inner__(self, params):
            
            import typing
            
            if self.__origin__ is tuple and self._special:
                if params == ():
                    return self.copy_with((typing._TypingEmpty,))
                if not isinstance(params, tuple):
                    params = (params,)
                if len(params) == 2 and params[1] is ...:
                    msg = "Tuple[t, ...]: t must be a type."
                    p = typing._type_check(params[0], msg)
                    return self.copy_with((p, typing._TypingEllipsis))
                msg = "Tuple[t0, t1, ...]: each t must be a type."
                params = tuple(typing._type_check(p, msg) for p in params)
                return self.copy_with(params)
            if self.__origin__ is Callable and self._special:
                args, result = params
                msg = "Callable[args, result]: result must be a type."
                result = typing._type_check(result, msg)
                if args is Ellipsis:
                    return self.copy_with((typing._TypingEllipsis, result))
                msg = "Callable[[arg, ...], result]: each arg must be a type."
                args = tuple(typing._type_check(arg, msg) for arg in args)
                params = args + (result,)
                return self.copy_with(params)
            return super().__getitem__(params)
        
### Unions ###
# Not warranted to stay.

StringUnion: TypeAlias = Union[_T, str]
"@lifetime >= 0.3.26rc3"
IntegerUnion: TypeAlias = Union[_T, int]
"@lifetime >= 0.3.26rc3"
FloatUnion: TypeAlias = Union[_T, float]
"@lifetime >= 0.3.26rc3"
ComplexUnion: TypeAlias = Union[_T, complex]
"@lifetime >= 0.3.26rc3"
IntegerFloatUnion: TypeAlias = Union[_T, int, float]
"@lifetime >= 0.3.26rc3"
IntegerStringUnion: TypeAlias = Union[_T, int, str]
"@lifetime >= 0.3.26rc3"
BooleanUnion: TypeAlias = Union[_T, bool]
"@lifetime >= 0.3.26rc3"
TrueUnion: TypeAlias = Union[_T, Literal[True]]
"@lifetime >= 0.3.26rc3"
FalseUnion: TypeAlias = Union[_T, Literal[False]]
"@lifetime >= 0.3.26rc3"

### Uncategorized ###

# *** uppercased
AnnotationForm = Any # >= 0.3.48 // _typeshed.AnnotationForm (backport before 3.14)
AnnotateFunc: TypeAlias = AVT_Callable[[Format], AVT_Dict[str, AnnotationForm]] # >= 0.3.57 // _typeshed.AnnotateFunc (backport before 3.14)
AnyCallable: TypeAlias = AVT_Callable[..., Any] # >= 0.3.26rc3
if _sys.version_info >= (3, 10): # >= 0.3.60 // builtins._ClassInfo
    ClassInfoType: TypeAlias = Union[type, UnionType, AVT_Tuple[Union[type, UnionType], ...]]
else:
    ClassInfoType: TypeAlias = Union[type, AVT_Tuple[type, ...]]
ColorType: TypeAlias = Union[int, str, None] # >= 0.3.25 // renamed from SupportsColor (0.3.26b3)
ColourType: TypeAlias = ColorType # >= 0.3.26b3
# CoroutineWrapperType
async def _f(): pass
_coroutine = _f()
# this class as '_collections_abc.coroutine_wrapper' doesn't exist, neither does it exist in 'types'
CoroutineWrapperType = type(_coroutine.__await__()) # >= 0.3.53
_coroutine.close()
del _coroutine
# END CoroutineWrapperType
DecimalComparableType: TypeAlias = Union[Decimal, float, _Rational] # >= 0.3.60
DecimalNewType: TypeAlias = Union[Decimal, float, str, AVT_Tuple[int, AVT_Sequence[int], int]] # >= 0.3.60
DecimalType: TypeAlias = Union[int, Decimal] # >= 0.3.60
EvaluateFunc: TypeAlias = AVT_Callable[[Format], AnnotationForm] # >= 0.3.59 // _typeshed.EvaluateFunc (backport before 3.14)
FlagsType: TypeAlias = Union[int, RegexFlag] # >= 0.3.60
Hash: TypeAlias = _hashlib.HASH # >= 0.3.44
if _sys.version_info >= (3, 9): # >= 0.3.44 // 0.3.53: '_hashlib.HASHXOF' undefined before Python 3.9 (patched error)
    Hashxof: TypeAlias = _hashlib.HASHXOF
else:
    Hashxof = type(hashlib.shake_128())
HaveCodeType: TypeAlias = Union[MethodType, FunctionType, CodeType, type, AVT_Callable[..., Any]] # >= 0.3.60 // type from dis.dis()
Hmac: TypeAlias = _hmac.HMAC # >= 0.3.44
InComparable: TypeAlias = AVT_Container # >= 0.3.26rc1
Incomplete = Any # >= 0.3.60 // _typeshed.Incomplete
Interface = Protocol # >= 0.3.44
LenOperable: TypeAlias = Sized # >= 0.3.26rc1
MaybeNone = Any # >= 0.3.57 // _typeshed.MaybeNone
OptionalCallable: TypeAlias = Optional[AVT_Callable[_P, _T]] # >= 0.3.26rc3
Pack = Concatenate
PatternType: TypeAlias = Union[AnyStr, AVT_Pattern[AnyStr]] # >= 0.3.60 // type from re.match()
ReadableBuffer: TypeAlias = _Buffer # >= 0.3.44 // _typeshed.ReadableBuffer
ReadOnlyBuffer: TypeAlias = _Buffer # >= 0.3.44 // _typeshed.ReadOnlyBuffer
RichComparable: TypeAlias = Union[LeastComparable[Any], GreaterComparable[Any]] # >= ?
Sizeable: TypeAlias = Sized # >= 0.3.26rc3
Text: TypeAlias = str # >= 0.3.58
TrueSequence: TypeAlias = Union[AVT_Sequence[_T], AVT_Uniqual[_T]] # >= 0.3.54
Unused: TypeAlias = object # >= 0.3.44 // _typeshed.Unused
Uuid: TypeAlias = UUID # >= 0.3.54
WriteableBuffer: TypeAlias = _Buffer # >= 0.3.44 // _typeshed.WriteableBuffer

# *** lowercased
cached_property = cachedproperty

del _collections_abc, _enum, _hashlib, hashlib, _hmac, _typing, _typing_ext # not for export!

### Functions/methods ###

def int_bit_count(i: int, /): # -> int
    """
    @lifetime >= 0.3.60
    
    `int.bit_count()` (>=3.10) since Python 3.8
    """
    
    if not isinstance(i, int):
        error = TypeError("expected an integer")
        raise error
    
    # code highlighted in python documentation
    return bin(i).count("1")

def int_to_bytes(
    i: int,
    /,
    length: Indexable = 1,
    byteorder: Literal["little", "big"] = "big",
    *,
    signed: bool = False
): # -> bytes
    """
    @lifetime >= 0.3.60
    
    `int.to_bytes()` (backporting update for default value of the first 2 parameters from Python 3.11)
    """
    
    if not isinstance(i, int):
        error = TypeError("expected an integer")
        raise error
    
    return i.to_bytes(length, byteorder, signed = signed)

def int_from_bytes(
    i: int,
    /,
    bytes: Union[AVT_Iterable[Indexable], BytesConvertible, ReadableBuffer],
    byteorder: Literal["little", "big"] = "big",
    *,
    signed: bool = False
): # -> int
    """
    @lifetime >= 0.3.60
    
    `int.from_bytes()` (backporting update for default value of `byteorder` parameter before Python 3.11)
    """
    
    if not isinstance(i, int):
        error = TypeError("expected an integer")
        raise error
    
    return i.from_bytes(bytes, byteorder, signed = signed)

# NOTE: for int.is_integer() (>= 3.12) use isinstance(o, int) instead.

def str_replace(
    s: str,
    old: str,
    new: str,
    /,
    count: Indexable = -1
): # -> str
    """
    @lifetime >= 0.3.60
    
    `str.replace()` (backporting update for `count` parameter from Python 3.13 - from positional-only to universal parameter)
    """
    
    if not isinstance(s, str):
        error = TypeError("expected a string")
        raise error
    
    return s.replace(old, new, count)

def str_removeprefix(
    s: str,
    prefix: str,
    /
): # -> str
    """
    @lifetime >= 0.3.60
    
    `str.removeprefix()` (backporting the method before Python 3.9; see PEP 616)
    """
    
    if not isinstance(s, str):
        error = TypeError("expected a string")
        raise error
    
    if _sys.version_info >= (3, 9):
        return s.removeprefix(prefix)
    else:
        if not isinstance(prefix, str):
            error = TypeError("expected 'prefix' parameter to have a string value")
            raise error
        return s[len(prefix):] if s.startswith(prefix) else s[:]
    
def str_removesuffix(
    s: str,
    suffix: str,
    /
): # -> str
    """
    @lifetime >= 0.3.60
    
    `str.removesuffix()` (backporting the method before Python 3.9; see PEP 616)
    """
    
    if not isinstance(s, str):
        error = TypeError("expected a string")
        raise error
    
    if _sys.version_info >= (3, 9):
        return s.removesuffix(suffix)
    else:
        if not isinstance(prefix, str):
            error = TypeError("expected 'prefix' parameter to have a string value")
            raise error
        return s[:len(suffix)] if suffix and s.endswith(suffix) else s[:]

# Abbreviating to 'bt' to be more consistent for 'bytes' and 'bytearray' simultaneously.
# If 'bytes' prefix replaced 'bt', then users might be confused this function is for
# 'bytes' objects only and not for 'bytearray' ('bytearray' objects also have methods
# 'removesuffix' and 'removeprefix' since Python 3.9), and this will force them to do
# such as:
# -----
# bytearray(<func>(bytes(<bytearray object>)))
# -----
# if they want to focus on 'bytearray' objects.
@overload
def bt_removeprefix(b: bytes, prefix: ReadableBuffer, /) -> bytes: ...
@overload
def bt_removeprefix(b: bytearray, prefix: ReadableBuffer, /) -> bytearray: ...
def bt_removeprefix(b, prefix, /):
    """
    @lifetime >= 0.3.60
    
    `[bytes|bytearray].removeprefix()` (backporting the method before Python 3.9; see PEP 616)
    """
    
    if not isinstance(b, (bytes, bytearray)):
        error = TypeError("expected a bytes or bytearray object")
        raise error
    
    if _sys.version_info >= (3, 9):
        return b.removeprefix(prefix)
    else:
        if not isinstance(prefix, ReadableBuffer):
            error = TypeError("expected 'prefix' parameter to have a string value")
            raise error
        return b[len(prefix):] if b.startswith(prefix) else b[:]
    
    
@overload
def bt_removesuffix(b: bytes, suffix: ReadableBuffer, /) -> bytes: ...
@overload
def bt_removesuffix(b: bytearray, suffix: ReadableBuffer, /) -> bytearray: ...
def bt_removesuffix(b, suffix, /):
    """
    @lifetime >= 0.3.60
    
    `[bytes|bytearray].removesuffix()` (backporting the method before Python 3.9; see PEP 616)
    """
    
    if not isinstance(b, (bytes, bytearray)):
        error = TypeError("expected a bytes or bytearray object")
        raise error
    
    if _sys.version_info >= (3, 9):
        return b.removesuffix(suffix)
    else:
        if not isinstance(prefix, ReadableBuffer):
            error = TypeError("expected 'prefix' parameter to have a string value")
            raise error
        return b[:len(suffix)] if suffix and b.endswith(suffix) else b[:]
    
def aiter(async_iterable: _AsyncIterOperable[_T_anext_cov], /):
    """
    @lifetime >= 0.3.60
    
    Backport of `aiter()` inbuilt function (allow use before Python 3.10)
    """
    
    if _sys.version_info >= (3, 10):
        import builtins
        return builtins.aiter(async_iterable)
    
    else:
        return async_iterable.__aiter__()

@overload
def anext(i: _SynchronousAsyncNextOperable[_T_awaitable], /) -> _T_awaitable: ...

if _sys.version_info >= (3, 10):
    @overload
    async def anext(i: AsyncNextOperable[_T1], default: _T2, /) -> Union[_T1, _T2]: ...

def anext(*params):
    """
    @lifetime >= 0.3.60
    
    Backport of `anext()` inbuilt function (allow use before Python 3.10)
    
    Overload with `default` however isn't currently supported before Python 3.10
    """
    
    if len(params) not in (1, 2):
        error = TypeError("expected 1-2 parameter(s), got {}".format(len(params)))
        raise error
    
    if _sys.version_info >= (3, 10):
        import builtins
        
        if len(params) == 1:
            return builtins.anext(params[0])
        else:
            return builtins.anext(params[0], params[1])
        
    else:
        
        if len(params) == 1: # cannot rebuild version with 2 parameters for now 
            return params[0].__anext__()
        
        else:
            error = TypeError("expected 1 parameter, got 2")
            raise error
        
# Re-declaring eval() and exec() with every argument except 'source' as universal arguments before 3.13. Yet I don't know how to re-declare exec() with 'closure' parameter before Python 3.11
def eval(
    source: Union[str, ReadableBuffer, CodeType],
    /,
    globals: Optional[AVT_Dict[str, Any]] = None,
    locals: Optional[AVT_Mapping[str, object]] = None
):
    """
    @lifetime >= 0.3.60
    
    `eval()` inbuilt function with backported update concerning `globals` and `locals` parameters prior to Python 3.13 (both were positional-only)
    """
        
    import builtins
    return builtins.eval(source, globals, locals)

if _sys.version_info >= (3, 11):
    
    def exec(
        source: Union[str, ReadableBuffer, CodeType],
        /,
        globals: Optional[AVT_Dict[str, Any]] = None,
        locals: Optional[AVT_Mapping[str, object]] = None,
        *,
        closure: Optional[AVT_Tuple[CellType, ...]] = None
    ):
        """
        @lifetime >= 0.3.60

        `exec()` inbuilt function with backported update concerning `globals` and `locals` parameters prior to Python 3.13 (both were positional-only)
        """
            
        import builtins
        builtins.exec(source, globals, locals, closure = closure)
            
else:
    
    def exec(
        source: Union[str, ReadableBuffer, CodeType],
        /,
        globals: Optional[AVT_Dict[str, Any]] = None,
        locals: Optional[AVT_Mapping[str, object]] = None
    ):
        """
        @lifetime >= 0.3.60

        `exec()` inbuilt function with backported update concerning `globals` and `locals` parameters prior to Python 3.13 (both were positional-only)
        """
            
        import builtins
        builtins.exec(source, globals, locals)

__all__ = sorted([k for k in globals() if not k.startswith("_")])
__all_deprecated__ = sorted([k for k in globals() if hasattr(globals()[k], "__deprecated__")]) # 0.3.44

if __name__ == "__main__":
    error = RuntimeError("Import-only module")
    raise error