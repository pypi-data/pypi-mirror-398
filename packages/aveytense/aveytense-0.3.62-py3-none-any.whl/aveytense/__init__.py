"""
# AveyTense

@lifetime >= 0.3.24; @pypi >= 0.3.26rc2 \\
© 2024-Present Aveyzan // License: MIT \\
https://aveyzan.xyz/aveytense

Multipurpose library with several extensions, including for built-ins.

Submodules:
- `aveytense.exceptions` - exception classes
- `aveytense.extensions` - extensions (types, functions etc.)
- `aveytense.constants` - constants collection
- `aveytense.operators` - extension of `operator` library
- `aveytense.util` - utility declarations
"""

from __future__ import annotations
import sys as _sys

if hasattr(_sys, "set_int_max_str_digits"): # < 0.3.46: sys.version_info >= (3, 11)
    _sys.set_int_max_str_digits(0) # type: ignore

# 0.3.34: Prevent internal imports and prevent these imported subsequently
import copy as _copy
import dis as _dis
import inspect as _inspect
import io as _io
import math as _math
import os as _os
import platform as _platform
import random as _random
import re as _re
import socket as _socket
import time as _time
import types as _types

from ._collection import _abroad as _ab_mod
from ._collection import _constants as _cl
from ._collection._primal import *
from ._collection._extensions import Any as _Any
from ._collection._util import _TenseImmutableMeta
from ._collection import _version
from . import constants as _cp
from . import exceptions
from . import operators as _op
from . import extensions as __
from . import util as _util

constants = _cp # 0.3.41
extensions = __ # 0.3.41; rename 0.3.57 from 'types'
operators = _op # 0.3.41
util = _util # 0.3.41

__author__ = "Aveyzan (aveyzan@gmail.com)" # >= 0.3.26rc3
__license__ = "MIT" # >= 0.3.26rc3
__version__ = _version.VERSION # >= 0.3.26rc3

_uni = __.Union
_lit = __.Literal
_opt = __.Optional
_cal = __.AVT_Callable

# local variables (0.3.39)
_MODE_AND = constants._ModeSelection.AND
_MODE_OR = constants._ModeSelection.OR
_PROBABILITY_COMPUTE = constants._ProbabilityLength.COMPUTE

# gimmick from enum standard module
Color = RGB = None

# TypeVars, TypeVarTuples, ParamSpecs
_S = __.TypeVar("_S")
_T = __.TypeVar("_T")
_T1 = __.TypeVar("_T1")
_T2 = __.TypeVar("_T2")
_T3 = __.TypeVar("_T3")
_KT = __.TypeVar("_KT")
_KT1 = __.TypeVar("_KT1")
_KT2 = __.TypeVar("_KT2")
_VT = __.TypeVar("_VT")
_VT1 = __.TypeVar("_VT1")
_VT2 = __.TypeVar("_VT2")
_Ts = __.TypeVarTuple("_Ts")
_T_func = __.TypeVar("_T_func", bound = _cal[..., __.Any])
_T_yield_cov = __.TypeVar("_T_yield_cov", covariant = True) # >= 0.3.53
_T_send_con = __.TypeVar("_T_send_con", contravariant = True, default = None) # >= 0.3.53
_T_return_cov = __.TypeVar("_T_return_cov", covariant = True, default = None) # >= 0.3.53

# 'types.UnionType' was introduced on Python 3.10.
# For backward-compatibility we need to use 'typing._UnionGenericAlias' before this version.
if _sys.version_info >= (3, 10):
    
    _U = __.TypeVar("_U", bound = __.UnionType)
    _UKT = __.TypeVar("_UKT", bound = __.UnionType)
    _UVT = __.TypeVar("_UVT", bound = __.UnionType)

else:
        
    _U = __.TypeVar("_U", bound = __.TypingUnionType) # type: ignore
    _UKT = __.TypeVar("_UKT", bound = __.TypingUnionType) # type: ignore
    _UVT = __.TypeVar("_UVT", bound = __.TypingUnionType) # type: ignore

# local enums

# class _ColorStyling(_tc.IntegerFlag): ### to 0.3.27
class _ColorStyling(__.Enum):
    """@lifetime >= 0.3.26rc1. Internal class for `%` operator in class `aveytense.Color`."""
    NORMAL = 0
    BOLD = 1
    FAINT = 2
    ITALIC = 3
    UNDERLINE = 4
    SLOW_BLINK = 5
    RAPID_BLINK = 6
    REVERSE = 7
    HIDE = 8
    STRIKE = 9
    # PRIMARY_FONT = 10
    ## 11-19 alternative font
    # GOTHIC = 20
    DOUBLE_UNDERLINE = 21
    # NORMAL_INTENSITY = 22
    # NO_ITALIC = 23
    # NO_UNDERLINE = 24
    # NO_BLINK = 25
    # PROPORTIONAL = 26 # corrected mistake! 0.3.26rc2
    # NO_REVERSE = 27
    # UNHIDE = 28
    # NO_STRIKE = 29
    ## 30-37 foreground color, 3-bit
    # 38 foreground color, 3 4 8 24-bit
    # FOREGROUND_DEFAULT = 39
    ## 40-47 background color, 3-bit
    ## 48 background color, 3 4 8 24-bit
    # BACKGROUND_DEFAULT = 49
    # NO_PROPORTIONAL = 50
    FRAME = 51
    ENCIRCLE = 52
    OVERLINE = 53
    # NO_FRAME = 54 # including "no encircle"
    # NO_OVERLINE = 55
    ## 56 and 57 undefined
    ## 58 underline color, 3 4 8 24-bit
    # UNDERLINE_DEFAULT = 59
    # IDEOGRAM_UNDERLINE = 60
    # IDEOGRAM_DOUBLE_UNDERLINE = 61
    # IDEOGRAM_OVERLINE = 62
    # IDEOGRAM_DOUBLE_OVERLINE = 63
    # IDEOGRAM_STRESS = 64
    # NO_IDEOGRAM = 65
    ## 66-72 undefined
    SUPERSCRIPT = 73
    SUBSCRIPT = 74
    # NO_SUPERSCRIPT = 75 # also counts as no subscript
    ## 76 undefined but recommended value: no subscript
    ## 77-89 undefined
    ## 90-97 bright foreground color, 4-bit
    ## 100-107 bright background color, 4-bit

# class _ColorAdvancedStyling(_tc.IntegerFlag): ### to 0.3.27
class _ColorAdvancedStyling(__.Enum):
    """@lifetime >= 0.3.26rc2. Internal class for `%` operator in class `aveytense.Color`."""
    
    # 2x
    BOLD_ITALIC = 1000
    BOLD_UNDERLINE = 1001
    BOLD_STRIKE = 1002
    BOLD_OVERLINE = 1003
    ITALIC_UNDERLINE = 1004
    ITALIC_STRIKE = 1005
    ITALIC_OVERLINE = 1006
    UNDERLINE_STRIKE = 1007
    UOLINE = 1008
    STRIKE_OVERLINE = 1009
    
    # 3x
    BOLD_ITALIC_UNDERLINE = 1100
    BOLD_ITALIC_STRIKE = 1101
    BOLD_ITALIC_OVERLINE = 1102
    BOLD_UNDERLINE_STRIKE = 1103
    BOLD_UOLINE = 1104
    ITALIC_UNDERLINE_STRIKE = 1105
    ITALIC_UOLINE = 1106
    ITALIC_STRIKE_OVERLINE = 1107
    STRIKE_UOLINE = 1108
    
@__.runtime
class _ClearableAbc(__.Protocol[_T]):
    """
    @since 0.3.42
    
    An internal ABC providing a `clear()` method. Used in `~.Tense.clear()`
    """
    
    def clear() -> _T: ...
    
class AbroadType: 
    """
    @lifetime >= 0.3.52

    Represents type of `abroad()`
    """
    ...

# local type aliases
_Bits = _lit[3, 4, 8, 24]
_Clearable = _uni[str, Color, _ClearableAbc[_Any], util.MutableString, __.AVT_MutableMapping[_Any, _Any], __.AVT_MutableSequence[_Any], __.AVT_MutableUniqual[_Any], __.IO[_Any], __.FrameType] # 0.3.42
_Color = _uni[__.ColorType, RGB]
_Mode = _uni[_cl.ModeSelection, _lit["and", "or"]] # 0.3.36
_Pattern = __.PatternType # 0.3.42
_Target = _uni[str, bytes] # 0.3.42

_AbroadValue1 = _ab_mod.AbroadValue1[_T]
_AbroadValue2 = _ab_mod.AbroadValue2[_T]
_AbroadModifier = _ab_mod.AbroadModifier[_T]
_AbroadPackType = _ab_mod.ReckonType[_T]
_AbroadConvectType = _ab_mod.AbroadConvectType[_T]
AbroadType = _ab_mod.AbroadInitializer # >= 0.3.52
_AbroadEachInitializer = __.AVT_List[_T]
_AbroadMultiInitializer = __.AVT_List[__.AVT_List[int]]

_ColorStylingType = _uni[_ColorStyling, _ColorAdvancedStyling]
_FlagsType = __.FlagsType # 0.3.42
_HaveCodeType = __.HaveCodeType
_ProbabilityLengthType = _uni[int, _lit[_cp._ProbabilityLength.COMPUTE]]
        
_ProbabilityType = _uni[
    _T,
    __.AVT_Sequence[_uni[_T, int, __.EllipsisType, None]], # Sequence => _AVT; 0.3.53
    __.AVT_Uniqual[_uni[_T, int, __.EllipsisType, None]], # Uniqual => _AVT; 0.3.53
    __.AVT_Mapping[_T, _uni[int, __.EllipsisType, None]] # Mapping => _AVT; 0.3.53
] # change 0.3.36, 0.3.46
    
_ReckonNGT = _ab_mod.ReckonNGT

if _sys.version_info >= (3, 10):
    _UnionTypes = (__.TypingUnionType, __.UnionType)
else:
    _UnionTypes = (__.TypingUnionType,)

if _sys.version_info >= (3, 9):
    _GenericTypes = (__.TypingGenericType, __.GenericAlias)
else:
    _GenericTypes = (__.TypingGenericType,)

# This tuple will be used as a type tuple to inspect via isinstance()
# in various functions

# 0.3.35: builtins.type
# 0.3.36: 'types.GenericAlias' and 'types.UnionType'
# 0.3.40: internal class for 'typing.Union' and class 'typing._GenericAlias'
_SupportedTypes = (type, *_GenericTypes, *_UnionTypes)

_Type = type # note for this alias (>= 0.3.35): must be used since it obscures with parameter with exact 'type' built-in name

def _is_hexadecimal(target: str, /):
    _t = target
    
    if target.lower().startswith(("0x", "#")):
        _t = _re.sub(r"^(0[xX]|#)", "", _t)
    
    for c in _t:
        
        if c not in constants.STRING_HEXADECIMAL:
            return False
        
    return True

def _is_decimal(target: str, /):
    
    for c in target:
        
        if c not in constants.STRING_DIGITS:
            return False
        
    return True

def _is_octal(target: str, /):
    _t = target
    
    if target.lower().startswith("0o"):
        _t = _re.sub(r"^0[oO]", "", _t)
    
    for c in _t:
        
        if c not in constants.STRING_OCTAL:
            return False
        
    return True

def _is_binary(target: str, /):
    _t = target
    
    if target.lower().startswith("0b"):
        _t = _re.sub(r"^0[bB]", "", _t)
    
    for c in _t:
        
        if c not in constants.STRING_BINARY:
            return False
        
    return True

def _is_bool_callback(v: _Any, /) -> __.TypeIs[__.AVT_Callable[[_Any], bool]]:
    
    # Unfortunately, it may not be possible to check if specific function has desired amount of parameters of correct types.
    # Best practice would be checking function annotation and passed types to parameters, so it will work correctly.
    # 02.02.2025
    #
    # 0.3.51: Perceived emptiness in ~.util.ParamVar.
    # Gimmick on this part was passing empty list and we expected a callable with one parameter only.
    # Verifying the return type was addicted to functions/methods that used this local function.
    # 0.3.53: allow any functions excluding lambda expressions only.
    return callable(v) and v.__code__.co_argcount == 1 and v.__code__.co_kwonlyargcount == 0 and v.__defaults__ is None
        
def _is_try_callback(v: _Any, /) -> __.TypeIs[__.AVT_Callable[[], _Any]]: # 0.3.58
    
    return callable(v) and v.__code__.co_argcount == 0 and v.__code__.co_kwonlyargcount == 0 and v.__defaults__ is None
        
# Following Python's advice instead of using isinstance(obj, collections.abc.Iterable)
def _is_iterable(target: object, /): # 0.3.57
    
    if hasattr(target, "__iter__") and isinstance(getattr(target, "__iter__", None), extensions.Iterator):
        return True
    
    # Checking for __getitem__() with integer indexes starting with 0
    try: 
        iter(target)
    except Exception:
        return False
    
    return True

def _architecture(executable = _sys.executable, bits = "", linkage = ""):
    "@lifetime >= 0.3.26rc2"
    
    return _platform.architecture(executable, bits, linkage)[0]

def _get_all_params(f: _T_func, /):
    
    # if we don't want to use 'inspect' module components, we can use function's __code__ attribute,
    # and access parameters via 'co_varnames' (which also returns tuple of names defined within its body).
    # to return tuple of arguments only, we can use slicing, as co_varnames[:co_argcount + co_kwonlyargcount]
    
    # co_argcount gets amount of non-keyword-only parameters, meanwhile co_kwonlyargcount counts all keyword-only arguments
    # To use in normal code, see ~.util.ParamVar.
    
    # 19.03.2025
    
    return [k for k in f.__code__.co_varnames[:f.__code__.co_argcount + f.__code__.co_kwonlyargcount] if k not in ("self", "return")] # 0.3.42

def _get_all_item_types(i: __.AVT_Iterable[_T], /, distinct = True): # 0.3.51
    
    if not _is_iterable(i):
        error = TypeError("expected an iterable")
        raise error
    
    # 0.3.52: Deduce 'typing.Any' from itself and 'StopIteration.value' (type hints 'typing.Any')
    # 0.3.53: The 'distinct' parameter
    
    if distinct:
        t = _util.uniquetuple
    else:
        t = tuple
        
    return t([(
        __.cast(__.AVT_Type[_T], e)
        if type(e) in (type(extensions.Protocol),) else __.cast(__.AVT_Type[_T], _Any)
        if e in (StopIteration.value, _Any) else type(e)
    ) for e in i])

##### Functions for Tense.getGeneric() // 0.3.53 #####

# applied to Tense.generator() since 0.3.55
def _extract_from_async_iterable(a: __.AVT_AsyncIterable[_T]): # 0.3.53
    
    if not isinstance(a, __.AsyncIterable): 
        error = TypeError("expected an asynchronous iterable")
        raise error
    
    # AsyncIterator and AsyncGenerator have __anext__, but AsyncIterable can access it via __aiter__
    if isinstance(a, __.AsyncIterator): 
        _async_ = a
    else:
        _async_ = a.__aiter__()
    
    # if you were about to ask about this statement, it may be possible to backport AveyTense to Python 3.6,
    # but this will require time and code revamp, especially resignation from pep 570 '/' operator in every
    # function since 3.7
    if _sys.version_info >= (3, 7):
        from asyncio import run
        
    else:
        def run(main: __.AVT_Coroutine[__.Any, __.Any, _T]):
            
            import asyncio
            
            if not isinstance(main, __.Coroutine):
                error = TypeError("expected a coroutine")
                raise error
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(main)
            
            finally:
                loop.close()
                asyncio.set_event_loop(None)
    
    # asyncio.run() Py>=3.7
    while True:
        try:
            yield __.cast(_T, run(_async_.__anext__()))
        except StopAsyncIteration:
            break
        
# Hidden type aliases in _collections_abc.py. These have module name 'builtins',
# but Python can always change that, so doing magic with 'dict_items.__module__'
# then (0.3.58; 20.10.2025)
def _hidden_collections_abc_def_check(v, t = ""): # 0.3.53
    
    return type(v).__module__ == type({}.items()).__module__ and type(v).__name__ == t

##### END Functions for Tense.getGeneric() #####

def _int_conversion(target: str, /):
        
    if _is_hexadecimal(target):
        return int(target, 16)
    
    elif _is_decimal(target):
        return int(target, 10)
    
    elif _is_octal(target):
        return int(target, 8)
    
    elif _is_binary(target):
        return int(target, 2)
    
    else:
        return int(target)
    
def _itu_perform(s: str, v = False): # 0.3.58
    
    return s.replace(";", ":") if v else s
    
def _colorize(text: str, bits: _Bits, fg: _uni[int, None], bg: _uni[int, None], itu = False, /): # 0.3.37 (0.3.37a1)
        
    _s = "\x1b["
    # for e in (self.__fg, self.__bg, self.__un): ### removed 0.3.27
    _msg = {
        3: "for 3-bit colors expected integer or string value in range 0-7. One of foreground or background values doesn't match this requirement",
        4: "for 4-bit colors expected integer or string value in range 0-15. One of foreground or background values doesn't match this requirement",
        8: "for 8-bit colors expected integer or string value in range 0-255. One of foreground or background values doesn't match this requirement",
        24: "for 24-bit colors expected integer, string, or RGB/CMYK tuple value in range 0-16777215. One of foreground or background values doesn't match this requirement"
    }
    
    for e in (fg, bg):
        
        if e is not None:
            if bits == 3 and e not in abroad(0x8):
                error = ValueError(_msg[3])
                raise error
            
            elif bits == 4 and e not in abroad(0x10):
                error = ValueError(_msg[4])
                raise error
            
            elif bits == 8 and e not in abroad(0x100):
                error = ValueError(_msg[8])
                raise error
        
            elif bits == 24 and e not in abroad(0x1000000):
                error = ValueError(_msg[24])
                raise error
    
    if bits == 3:
        # 2 ** 3 = 8 (0x8 in hex)
        _s += str(30 + fg) + ";" if fg is not None else ""
        _s += str(40 + bg) + ";" if bg is not None else ""
    
    elif bits == 4:
        # 2 ** 4 = 16 (0x10 in hex); WARNING: bright colors notation isn't official
        _s += str(30 + fg) + ";" if fg is not None and fg in abroad(0x8) else ""
        _s += str(40 + bg) + ";" if bg is not None and bg in abroad(0x8) else ""
        _s += str(90 + fg) + ";" if fg is not None and fg in abroad(0x8, 0x10) else ""
        _s += str(100 + bg) + ";" if bg is not None and bg in abroad(0x8, 0x10) else ""
    
    elif bits == 8:
        # 2 ** 8 = 256 (0x100 in hex)
        _s += "38;5;" + str(fg) + ";" if fg is not None else ""
        _s += "48;5;" + str(bg) + ";" if bg is not None else ""
    
    elif bits == 24:
        # 2 ** 24 = 16777216 (0x1000000 in hex)
        # code reconstructed on 0.3.26rc2
        # acknowledgements: equivalent to rgb
        _f = hex(fg) if fg is not None else ""
        _b = hex(bg) if bg is not None else ""
        _f = _re.sub(r"^(0x|#)", "", _f) if reckon(_f) > 0 else ""
        _b = _re.sub(r"^(0x|#)", "", _b) if reckon(_b) > 0 else ""
        _hf, _hb = [None, None]
        for s in (_f, _b):
            
            if reckon(s) == 6:
                if s == _f:
                    _hf = tuple(int(s[i : i + 2], 16) for i in abroad(0, 5, 2))
                else:
                    _hb = tuple(int(s[i : i + 2], 16) for i in abroad(0, 5, 2))
                # else:
                #    _hu = tuple(int(s[i : i + 2], 16) for i in abroad(0, 5, 2)) ### removed 0.3.27
                
            elif reckon(s) == 5:
                s = "0" + s
                if s == "0" + _f:
                    _hf = tuple(int(s[i : i + 2], 16) for i in abroad(0, 5, 2))
                else:
                    _hb = tuple(int(s[i : i + 2], 16) for i in abroad(0, 5, 2))
                
            elif reckon(s) == 4:
                s = "00" + s
                if s == "00" + _f:
                    _hf = tuple(int(s[i : i + 2], 16) for i in abroad(0, 5, 2))
                else:
                    _hb = tuple(int(s[i : i + 2], 16) for i in abroad(0, 5, 2))
                
            elif reckon(s) == 3:
                _tmp = "".join(s[i] * 2 for i in abroad(s)) # aliased according to css hex fff notation
                s = _tmp
                if s == _f:
                    _hf = tuple(int(s[i : i + 2], 16) for i in abroad(0, 5, 2))
                else:
                    _hb = tuple(int(s[i : i + 2], 16) for i in abroad(0, 5, 2))
                
            elif reckon(s) == 2:
                s = "0000" + s
                if s == "0000" + _f:
                    _hf = tuple(int(s[i : i + 2], 16) for i in abroad(0, 5, 2))
                else:
                    _hb = tuple(int(s[i : i + 2], 16) for i in abroad(0, 5, 2))
                
            elif reckon(s) == 1:
                s = "00000" + s
                if s == "00000" + _f:
                    _hf = tuple(int(s[i : i + 2], 16) for i in abroad(0, 5, 2))
                else:
                    _hb = tuple(int(s[i : i + 2], 16) for i in abroad(0, 5, 2))
        
        _s += "38;2;" + str(_hf[0]) + ";" + str(_hf[1]) + ";" + str(_hf[2]) + ";" if _hf is not None else ""
        _s += "48;2;" + str(_hb[0]) + ";" + str(_hb[1]) + ";" + str(_hb[2]) + ";" if _hb is not None else ""
    else:
        error = ValueError("internal 'bits' variable value is not one from following: 3, 4, 8, 24")
        raise error
    
    _s = _itu_perform(_s, itu)
    
    if _s != "\x1b[":
        _s = _re.sub(r"[:;]$", "m", _s)
        _s += text + "\x1b[0m"
    else:
        _s = text
    return _s

# This function can sometimes hint 'typing.Any' as the return annotation, but in reality it will always return
# a boolean value. Keep that on mind!
def _is_sequence_helper(v, /, type = ()): # 0.3.36
    
    # START 0.3.35
    
    _v = list(v) if not isinstance(v, list) else v
    
    if reckon(_v) == 0:
        
        # Since 'typing.Any' cannot be used with isinstance(), as it throws an error (but it should normally return 'True'),
        # the only way to determine if we are dealing with 'typing.Any' is inspecting variable with the 'is' keyword
        if type is _Any:
            return True
        
        return False
    
    # END 0.3.35
    
    if not isinstance(type, (tuple, *_SupportedTypes)):
        error = TypeError("passed value to parameter '{}' must be a type, tuple of types, union or generic type".format("type"))
        raise error
        
    _placeholder = True
    
    # 0.3.52: Code revamp
    if isinstance(type, (_UnionTypes, tuple)):
        
        # Flattening union types within a tuple is currently rethought, you should use either types in
        # a tuple or union type before this solution will be ever implemented
        if isinstance(type, _UnionTypes):
            _unique_ = _util.uniquetuple(type.__args__)
        else:
            if reckon(type) == 0: # behavior for '<seqCheckFunc>(v, ())' from 0.3.35
                return True
            
            _unique_ = _util.uniquetuple(type)
            
            for e in _unique_:
                if not isinstance(e, _Type):
                    error = TypeError("expected only types in the tuple or union type") 
                    raise error
            
        _exclude_generics_ = tuple([e for e in _unique_ if not isinstance(e, _GenericTypes) and e not in (None, Ellipsis)])
        _generics_ = tuple([e for e in _unique_ if isinstance(e, _GenericTypes)])
        
        # 0.3.52: 'typing.Any' is not a generic type. once 'typing.Any' is found, always return 'True'
        if _Any in _exclude_generics_: 
            return True
        
        for e in _v:
            if _placeholder:
                _placeholder = _placeholder and isinstance(e, _exclude_generics_)
                for e2 in _generics_:
                    if _is_iterable(e) and issubclass(e2.__origin__, __.Iterable):
                        _placeholder = _placeholder and isinstance(e, e2.__origin__)
                        for e3 in e:
                            _placeholder = _placeholder and isinstance(e3, e2.__args__)
                    else:
                        break
            else:
                break
            
    elif isinstance(type, _GenericTypes):
        
        # E.g. begin with '<seqCheckFunc>(v, <generic alias>)' as '<seqCheckFunc>(v, list[int])', then we want 'v'
        # to be duo-dimensional list with internal list being integers only
        for e in _v:
            # Notice if the item isn't iterable, then __args__ isn't used, it is simply considered as inspecting only
            # origin of generic alias instead. Reason of this behavior comes from fact that there are many various ways
            # to retrieve type arguments from a generic alias, especially from concrete attributes
            if _placeholder:
                _placeholder = _placeholder and isinstance(e, type.__origin__)
                if _is_iterable(e) and issubclass(type.__origin__, __.Iterable):
                    if _Any in type.__args__:
                        return True
                    for e2 in e:
                        _placeholder = _placeholder and isinstance(e2, type.__args__)
            else:
                break
                
    else:
        
        if type is _Any: # behavior for '<seqCheckFunc>(v, typing.Any)' from 0.3.35
            return True
        
        # Alternatively, it would be 'return all([isinstance(e, type) for e in _v])',
        # but 'for' loop will not stop even if 'False' dropped in at least one iteration
        # from isinstance(). That would decrease performance, and a little greater execution time.
        for e in _v:
            if _placeholder:
                _placeholder = _placeholder and isinstance(e, type)
            else:
                break
        
    return _placeholder

def _inspect_many(*v, type = _Any, mode: _Mode = _MODE_AND): # 0.3.36
    
    if reckon(v) == 0:
        return False
    
    else:
        
        _placeholder = True
        
        for e in v:
            
            try:
                
                if type is not None:
                    
                    if mode in (_MODE_AND, "and"):
                        _placeholder = _placeholder and isinstance(e, type)
                        
                    elif mode in (_MODE_OR, "or"):
                        _placeholder = _placeholder or isinstance(e, type)
                        
                    else:
                        return False
                    
                else:
                    
                    if mode in (_MODE_AND, "and"):
                        _placeholder = _placeholder and e is None
                        
                    elif mode in (_MODE_OR, "or"):
                        _placeholder = _placeholder or e is None
                        
                    else:
                        return False
            
            except:
                
                if mode in (_MODE_AND, "and"):
                    _placeholder = _placeholder and _Type(e) is type
                    
                elif mode in (_MODE_OR, "or"):
                    _placeholder = _placeholder or _Type(e) is type
                    
                else:
                    return False
                    
        return _placeholder
    
    
def _inspect_numerics(*v, mode = "b", lmode: _Mode = _MODE_AND): # 0.3.38
    
    if reckon(v) == 0:
        return False
    
    else:
        
        _placeholder = True
        
        for e in v:
            
            if lmode in (_MODE_AND, "and"):
                
                if mode == "b":
                    _placeholder = _placeholder and (type(e) is str and _is_binary(e))
                    
                elif mode == "o":
                    _placeholder = _placeholder and (type(e) is str and _is_octal(e))
                    
                elif mode == "d":
                    _placeholder = _placeholder and (type(e) is str and _is_decimal(e))
                    
                elif mode == "h":
                    _placeholder = _placeholder and (type(e) is str and _is_hexadecimal(e))
                    
                else:
                    return False
                
            elif lmode in (_MODE_OR, "or"):
                
                if mode == "b":
                    _placeholder = _placeholder or (type(e) is str and _is_binary(e))
                    
                elif mode == "o":
                    _placeholder = _placeholder or (type(e) is str and _is_octal(e))
                    
                elif mode == "d":
                    _placeholder = _placeholder or (type(e) is str and _is_decimal(e))
                    
                elif mode == "h":
                    _placeholder = _placeholder or (type(e) is str and _is_hexadecimal(e))
                    
                else:
                    return False
                
            else:
                return False
            
        return _placeholder

class Tense(Time, Math, metaclass = _TenseImmutableMeta): # 0.3.24
    """
    @lifetime >= 0.3.24 \\
    @standard-lifetime >= 0.3.24 \\
    https://aveyzan.xyz/aveytense#aveytense.Tense
    
    Root of AveyTense. Subclassing since 0.3.26b3
    """
    
    constants = _cp # 0.3.39
    exceptions = exceptions # 0.3.44
    extensions = __ # 0.3.42; renamed 0.3.57 from 'types'
    operators = _op # 0.3.42
    util = _util # 0.3.42
    
    version = _version.VERSION
    versionInfo = _version.VERSION_INFO
    
    AND = _MODE_AND
    "@lifetime >= 0.3.36"
    
    OR = _MODE_OR
    "@lifetime >= 0.3.36"
    
    PROBABILITY_COMPUTE = _PROBABILITY_COMPUTE
    "@lifetime >= 0.3.26rc2"
    
    PROBABILITY_MIN = constants._ProbabilityLength.MIN # 0.3.62
    PROBABILITY_MAX = constants._ProbabilityLength.MAX # 0.3.62
    PROBABILITY_DEFAULT = constants._ProbabilityLength.DEFAULT # 0.3.62
        
    def __init__(self): # 0.3.40
            
        _tmp = _inspect.currentframe().f_back.f_lineno
        self.__frame = _tmp if type(_tmp) is int else -1
            
    def __str__(self): # 0.3.40
        return "<{}.{} object with id {}>".format(self.__module__, type(self).__name__, id(self))
        
    def __repr__(self): # 0.3.40
        return "<{} defined in line {}, id {}>".format(self.__str__(), self.__frame, id(self))
    
    if versionInfo >= (0, 3, 43) and versionInfo < (0, 3, 45) and False:
        
        none = None
        """@since 0.3.32"""
        
    else:
    
        @_util.finalproperty
        def none(self):
            """
            @lifetime >= 0.3.32
            
            This property is console-specific, and simply returns `None`.
            """
            return None
    
    ABROAD_HEX_INCLUDE = constants.ABROAD_HEX_INCLUDE
    "@lifetime >= 0.3.26rc2"
    
    ABROAD_HEX_HASH = constants.ABROAD_HEX_HASH
    "@lifetime >= 0.3.26rc2"
    
    ABROAD_HEX_EXCLUDE = constants.ABROAD_HEX_EXCLUDE
    "@lifetime >= 0.3.26rc2"
    
    @classmethod
    def license(cls): # declare here instead of overriding license() built-in if wildcard import was used
        """
        @lifetime >= 0.3.54
        
        Prints AveyTense license information.
        """
        
        print(
            "Copyright © 2024-Present Aveyzan // License: MIT",
            "Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the \"Software\"), " + \
            "to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, " + \
            "and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:",
            "The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.",
            "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, " + \
            "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, " + \
            "WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.",
            sep = "\n\n"
        )
    
    @classmethod
    def toList(cls, v: __.Union[__.AVT_Iterable[_T], __.AVT_AsyncIterable[_T], __.ListConvertible[_T], __.TupleConvertible[_T], __.SetConvertible[_T]], /):
        """
        @lifetime >= 0.3.26rc3
        
        Converts a value to a `list` built-in. Since 0.3.55a1 asynchronous iterable objects are now allowed.
        """
        
        if isinstance(v, __.ListConvertible):
            return v.__tlist__()
        
        elif isinstance(v, __.TupleConvertible):
            return list(v.__ttuple__())
        
        elif isinstance(v, __.SetConvertible):
            return list(v.__tset__())
        
        elif isinstance(v, __.AsyncIterable): # >= 0.3.55
            return list(_extract_from_async_iterable(v))
        
        elif isinstance(v, __.Iterable):
            return list(v)
        
        else:
            error = TypeError("expected an iterable or async iterable object, or an object of a subclass of '{}', '{}', '{}'".format(
                __.ListConvertible.__name__,
                __.TupleConvertible.__name__,
                __.SetConvertible.__name__
            ))
            raise error
    
    @classmethod # type hint should use TypeVar instead but it doesn't change anything really.
    def isIn(cls, seq: __.AVT_Sequence[_Any], *values: _Any): 
        """
        @lifetime >= 0.3.61
        
        Returns `True` whether one of `values` exist in a `seq`uence. If `seq` isn't a sequence, `False` is returned.
        """
        
        if not isinstance(seq, __.Sequence):
            return False
        
        for value in values:
            if value in seq:
                return True
            
        return False
    
    @classmethod
    @__.overload
    def isType(cls, v: _Any, t: __.AVT_Type[_T] = _Any, /) -> __.TypeIs[__.AVT_Type[_T]]: ...

    @classmethod
    @__.overload
    def isType(cls, v: _Any, t: __.AVT_Tuple[__.AVT_Type[_T], ...], /) -> __.TypeIs[__.AVT_Type[_T]]: ...

    @classmethod
    def isType(cls, v, t, /):
        """
        @lifetime >= 0.3.59
        
        Check whether a value is a desired type or equal to one of types specified in tuple of types. This is similar how `isinstance()`
        works with the form `isinstance(type(v), t)`.
        
        Difference between this class method and `isinstance()` is that the target object isn't used as the first argument in `isinstance()`,
        what means `__instancecheck__()` method has practically no influence on it. `isinstance()` is used on the second parameter instead, to
        determine whether it is a tuple of types or type itself. If this verification raises an exception, then `False` is returned.
        """
        
        try:
            isinstance(t, (type, tuple))
        except Exception:
            return False
        
        return v is t if isinstance(t, type) else v in t if (isinstance(t, tuple) and cls.all(t, lambda x: isinstance(x, type))) else False
    
    @classmethod
    @__.overload
    def isAbroad(cls, v: _Any, /) -> __.TypeIs[_ab_mod.AbroadInitializer]: ...
    
    @classmethod
    @__.overload
    def isAbroad(cls, v: _Any, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isAbroad(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.50 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isAbroad
        
        Determine whether passed object is instance of internal class returned by function `aveytense.abroad()`.
        """
        
        _many = (v,) + _
        return _inspect_many(*_many, type = _ab_mod.AbroadInitializer, mode = mode)
    
    @classmethod
    @__.overload
    def isNone(cls, v: _Any, /) -> __.TypeIs[None]: ...
    
    @classmethod
    @__.overload
    def isNone(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isNone(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.26b3 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isNone
        
        Determine whether a value is `None`
        
        - 0.3.36: Many values may be now inspected
        """
        _many = (v,) + _
        return _inspect_many(*_many, type = None, mode = mode)
    
    @classmethod
    @__.overload
    def isEllipsis(cls, v: _Any, /) -> __.TypeIs[__.EllipsisType]: ...
    
    @classmethod
    @__.overload
    def isEllipsis(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isEllipsis(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.26 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isEllipsis
        
        Determine whether a value is `...`
        
        - 0.3.36: Many values may be now inspected
        """
        _many = (v,) + _
        return _inspect_many(*_many, type = __.EllipsisType, mode = mode)
    
    @classmethod
    @__.overload
    def isBool(cls, v: _Any, /) -> __.TypeIs[bool]: ...
    
    @classmethod
    @__.overload
    def isBool(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isBool(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.26b3 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isBoolean
        
        Determine whether a value is of type `bool`
        
        - 0.3.36: Many values may be now inspected
        """
        _many = (v,) + _
        return _inspect_many(*_many, type = bool, mode = mode)
    
    @classmethod
    @__.overload
    def isBoolean(cls, v: _Any, /) -> __.TypeIs[bool]: ...
    
    @classmethod
    @__.overload
    def isBoolean(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isBoolean(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.26rc1 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isBoolean
        
        Alias to `Tense.isBool()`

        Determine whether a value is of type `bool`
        
        - 0.3.36: Many values may be now inspected
        """
        _many = (v,) + _
        return _inspect_many(*_many, type = bool, mode = mode)
    
    @classmethod
    @__.overload
    def isInt(cls, v: _Any, /) -> __.TypeIs[int]: ...
    
    @classmethod
    @__.overload
    def isInt(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isInt(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.26b3 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isInteger
        
        Determine whether a value is of type `int`
        
        - 0.3.36: Many values may be now inspected
        """
        _many = (v,) + _
        return _inspect_many(*_many, type = int, mode = mode)
    
    @classmethod
    @__.overload
    def isInteger(cls, v: _Any, /) -> __.TypeIs[int]: ...
    
    @classmethod
    @__.overload
    def isInteger(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isInteger(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.26rc1 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isInteger
        
        Alias to `Tense.isInt()`

        Determine whether a value is of type `int`
        
        - 0.3.36: Many values may be now inspected
        """
        _many = (v,) + _
        return _inspect_many(*_many, type = int, mode = mode)
    
    @classmethod
    @__.overload
    def isFloat(cls, v: _Any, /) -> __.TypeIs[float]: ...
    
    @classmethod
    @__.overload
    def isFloat(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isFloat(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.26b3 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isFloat
        
        Determine whether a value is of type `float`
        
        - 0.3.36: Many values may be now inspected
        """
        _many = (v,) + _
        return _inspect_many(*_many, type = float, mode = mode)
    
    @classmethod
    @__.overload
    def isComplex(cls, v: _Any, /) -> __.TypeIs[complex]: ...
    
    @classmethod
    @__.overload
    def isComplex(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isComplex(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.26b3 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isComplex
        
        Determine whether a value is of type `complex`
        
        - 0.3.36: Many values may be now inspected
        """
        _many = (v,) + _
        return _inspect_many(*_many, type = complex, mode = mode)
    
    @classmethod
    @__.overload
    def isStr(cls, v: _Any, /) -> __.TypeIs[str]: ...
    
    @classmethod
    @__.overload
    def isStr(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isStr(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.26b3 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isString
        
        Determine whether a value is of type `str`
        
        - 0.3.36: Many values may be now inspected
        """
        _many = (v,) + _
        return _inspect_many(*_many, type = str, mode = mode)
    
    @classmethod
    @__.overload
    def isString(cls, v: _Any, /) -> __.TypeIs[str]: ...
    
    @classmethod
    @__.overload
    def isString(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isString(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.26rc1 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isString
        
        Alias to `Tense.isStr()`

        Determine whether a value is of type `str`
        
        - 0.3.36: Many values may be now inspected
        """
        _many = (v,) + _
        return _inspect_many(*_many, type = str, mode = mode)
    
    @classmethod
    @__.overload
    def isTuple(cls, v: _Any, /, type: __.AVT_Type[_T] = _Any) -> __.TypeIs[__.AVT_Tuple[_T, ...]]: ...
    
    @classmethod
    @__.overload
    def isTuple(cls, v: _Any, /, type: __.AVT_Tuple[__.AVT_Type[_T], ...]) -> __.TypeIs[__.AVT_Tuple[_T, ...]]: ...
    
    @classmethod
    @__.overload
    def isTuple(cls, v: _Any, /, type: _U) -> __.TypeIs[__.AVT_Tuple[_U, ...]]: ...
    
    @classmethod
    def isTuple(cls, v, /, type = _Any):
        """
        @lifetime >= 0.3.26rc1 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isTuple
        
        Determine whether a value is a tuple built-in.
        
        - 0.3.34: Added new parameter `type`, allowing to restrict the tuple type. Default value is `Any`.
        
        - 0.3.35: Overload; `type` now can be a tuple of types, code will count them as union type to match against. \\
        Hence the experiments concerning `types` parameter are over (parameter isn't included).
        
        - 0.3.36: Generic types are now allowed. Warning: this feature is experimental
        """
        return _is_sequence_helper(v, type = type) if _Type(v) is tuple else False
    
    @classmethod
    @__.overload
    def isTuple2(cls, v1: __.AVT_Tuple[_Any, ...], v2: __.AVT_Tuple[__.AVT_Type[_T], ...], /) -> __.TypeIs[__.AVT_Tuple[_T, ...]]: ...
    
    @classmethod
    @__.overload
    def isTuple2(cls, v1: __.AVT_Tuple[_Any, ...], v2: __.AVT_Tuple[__.AVT_Tuple[__.AVT_Type[_T], ...], ...], /) -> __.TypeIs[__.AVT_Tuple[_T, ...]]: ...
    
    @classmethod
    @__.overload
    def isTuple2(cls, v1: __.AVT_Tuple[_Any, ...], v2: __.AVT_Tuple[__.Union[__.AVT_Type[_T], __.AVT_Tuple[__.AVT_Type[_T], ...]], ...], /) -> __.TypeIs[__.AVT_Tuple[_T, ...]]: ...
    
    @classmethod
    @__.overload
    def isTuple2(cls, v1: __.AVT_Tuple[_Any, ...], v2: __.AVT_Tuple[_U, ...], /) -> __.TypeIs[__.AVT_Tuple[_U, ...]]: ...
    
    @classmethod
    @__.overload
    def isTuple2(cls, v1: __.AVT_Tuple[_Any, ...], v2: __.AVT_Tuple[__.AVT_Tuple[_U, ...], ...], /) -> __.TypeIs[__.AVT_Tuple[_U, ...]]: ...
    
    @classmethod
    @__.overload
    def isTuple2(cls, v1: __.AVT_Tuple[_Any, ...], v2: __.AVT_Tuple[__.Union[__.AVT_Type[_T], __.AVT_Tuple[_U, ...]], ...], /) -> __.TypeIs[__.AVT_Tuple[__.Union[_T, _U], ...]]: ...
    
    @classmethod
    @__.overload
    def isTuple2(cls, v1: __.AVT_Tuple[_Any, ...], v2: __.AVT_Tuple[__.Union[__.AVT_Tuple[__.AVT_Type[_T], ...], __.AVT_Tuple[_U, ...]], ...], /) -> __.TypeIs[__.AVT_Tuple[__.Union[_T, _U], ...]]: ...
    
    @classmethod
    @__.overload
    def isTuple2(cls, v1: __.AVT_Tuple[_Any, ...], v2: __.AVT_Tuple[__.Union[__.AVT_Type[_T], __.AVT_Tuple[__.AVT_Type[_T], ...], __.AVT_Tuple[_U, ...]], ...], /) -> __.TypeIs[__.AVT_Tuple[__.Union[_T, _U], ...]]: ...
    
    @classmethod
    @__.overload
    def isTuple2(cls, v1: __.AVT_Tuple[_Any, ...], v2: __.AVT_Tuple[__.Unpack[_Ts]], /) -> __.TypeIs[__.AVT_Tuple[__.Unpack[_Ts]]]: ...
            
    @classmethod
    def isTuple2(cls, v1, v2, /):
        """
        @lifetime >= 0.3.43 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isTuple2
        
        Extension of `aveytense.Tense.isTuple()` and also `isinstance()`. Usage is following::

            Tense.isTuple2((132, 342), (int,)) # True; same as ~.isTuple((132, 342), int)
            Tense.isTuple2((132, 342), (int, int)) # True (both items are integers)
            Tense.isTuple2((132, 342), (int, int, int)) # throws TypeError
            Tense.isTuple2((132, 342), ((int, str),))) # True; same as ~.isTuple((132, 342), (int, str))
            Tense.isTuple2((132, 342), (int, str)) # False (NOT the same as ~.isTuple((132, 342), (int, str)))
            Tense.isTuple2((132, 342), (str,)) # False
            Tense.isTuple2((132, 342), ((int, str), int)) # True
            Tense.isTuple2((132, 342), ((int, str), str)) # False
            Tense.isTuple2((132, 342), ((int, str), (int, str))) # True
        """
        
        if cls.isTuple(v1) and cls.isTuple(v2) and reckon(v2) == 0:
            return True
        
        elif cls.isTuple(v1) and cls.isTuple(v2, (tuple, *_SupportedTypes)):
            
            if reckon(v1) == 0:
                
                if reckon(v2) == 0 or (reckon(v2) == 1 and v2[0] is _Any):
                    return True
                
                return False
            
            _placeholder = True
            
            if reckonIsLeast(v1, v2):
                
                error = TypeError("expected first tuple having same as or bigger amount of items than second tuple")
                raise error
            
            elif reckon(v1) == reckon(v2):
                
                for i in abroad(v1):
                    _placeholder = _placeholder and bool(cls.isTuple((v1[i],), v2[i]))
                    
                return _placeholder
            
            else:
                
                for i in abroad(reckon(v2) - 1):
                    _placeholder = _placeholder and bool(cls.isTuple((v1[i],), v2[i]))
                    
                for i in abroad(v1[reckon(v2) - 1 :]):
                    _placeholder = _placeholder and bool(cls.isTuple((v1[i],), v2[-1]))
                    
                return _placeholder
            
        return False
            
    @classmethod
    @__.overload
    def isList(cls, v: _Any, /, type: __.AVT_Type[_T] = _Any) -> __.TypeIs[__.AVT_List[_T]]: ...
    
    @classmethod
    @__.overload
    def isList(cls, v: _Any, /, type: __.AVT_Tuple[__.AVT_Type[_T], ...]) -> __.TypeIs[__.AVT_List[_T]]: ...
        
    @classmethod
    @__.overload
    def isList(cls, v: _Any, /, type: _U) -> __.TypeIs[__.AVT_List[_U]]: ...
                    
    @classmethod
    def isList(cls, v, /, type = _Any):
        """
        @lifetime >= 0.3.26rc1 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isList
        
        Determine whether a value is a list built-in.
        
        - 0.3.34: Added new parameter `type`, allowing to restrict the list type. Default value is `Any`
        - 0.3.35: Overload; `type` now can be a tuple of types, code will count them as union type to match against
        - 0.3.36: Generic types are now allowed. Warning: this feature is experimental
        """
        return _is_sequence_helper(v, type = type) if _Type(v) is list else False
        
    @classmethod
    @__.overload
    def isDict(cls, v: _Any, /, ktype: __.AVT_Type[_KT] = _Any, vtype: __.AVT_Type[_VT] = _Any) -> __.TypeIs[__.AVT_Dict[_KT, _VT]]: ...
    
    @classmethod
    @__.overload
    def isDict(cls, v: _Any, /, ktype: __.AVT_Type[_KT], vtype: __.AVT_Tuple[__.AVT_Type[_VT], ...]) -> __.TypeIs[__.AVT_Dict[_KT, _VT]]: ...
    
    @classmethod
    @__.overload
    def isDict(cls, v: _Any, /, ktype: __.AVT_Type[_KT], vtype: _UVT) -> __.TypeIs[__.AVT_Dict[_KT, _UVT]]: ...
    
    @classmethod
    @__.overload
    def isDict(cls, v: _Any, /, ktype: __.AVT_Tuple[__.AVT_Type[_KT], ...], vtype: type[_VT] = _Any) -> __.TypeIs[__.AVT_Dict[_KT, _VT]]: ...
    
    @classmethod
    @__.overload
    def isDict(cls, v: _Any, /, ktype: __.AVT_Tuple[__.AVT_Type[_KT], ...], vtype: __.AVT_Tuple[__.AVT_Type[_VT], ...]) -> __.TypeIs[__.AVT_Dict[_KT, _VT]]: ...
    
    @classmethod
    @__.overload
    def isDict(cls, v: _Any, /, ktype: __.AVT_Tuple[__.AVT_Type[_KT], ...], vtype: _UVT) -> __.TypeIs[__.AVT_Dict[_KT, _UVT]]: ...
    
    @classmethod
    @__.overload
    def isDict(cls, v: _Any, /, ktype: _UKT, vtype: __.AVT_Type[_VT] = _Any) -> __.TypeIs[__.AVT_Dict[_UKT, _VT]]: ...
    
    @classmethod
    @__.overload
    def isDict(cls, v: _Any, /, ktype: _UKT, vtype: __.AVT_Tuple[__.AVT_Type[_VT], ...]) -> __.TypeIs[__.AVT_Dict[_UKT, _VT]]: ...
    
    @classmethod
    @__.overload
    def isDict(cls, v: _Any, /, ktype: _UKT, vtype: _UVT) -> __.TypeIs[__.AVT_Dict[_UKT, _UVT]]: ...
    
    @classmethod
    def isDict(cls, v, /, ktype = _Any, vtype = _Any):
        """
        @lifetime >= 0.3.31 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isDict
        
        Determine whether a value is a dictionary built-in.
        
        - 0.3.34: Added 2 parameters `ktype` and `vtype`, restricting types for, respectively, keys and values. Both have default values `Any`.
        - 0.3.35: Overload; `ktype` and `vtype` now can be tuples of types, code will count them as union type to match against, respectively, keys and values.
        - 0.3.36: Generic types are now allowed. Warning: this feature is experimental
        """
        
        if type(v) is dict:
            
            vk, vv = ([k for k in v], [v[k] for k in v])
            return _is_sequence_helper(vk, type = ktype) and _is_sequence_helper(vv, type = vtype)
            
        else:
            return False
    
    @classmethod
    @__.overload
    def isSet(cls, v: _Any, /, type: __.AVT_Type[_T] = _Any) -> __.TypeIs[__.AVT_Set[_T]]: ...
    
    @classmethod
    @__.overload
    def isSet(cls, v: _Any, /, type: __.AVT_Tuple[__.AVT_Type[_T], ...]) -> __.TypeIs[__.AVT_Set[_T]]: ...
    
    @classmethod
    @__.overload
    def isSet(cls, v: _Any, /, type: _U) -> __.TypeIs[__.AVT_Set[_U]]: ...
            
    @classmethod
    def isSet(cls, v, /, type = _Any):
        """
        @lifetime >= 0.3.35 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isSet
        
        Determine whether a value is a set built-in.
        
        Parameter `type` allows to restrict the set type.
        
        - 0.3.36: Generic types are now allowed. Warning: this feature is experimental
        """
        return _is_sequence_helper(v, type = type) if _Type(v) is set else False
    
    @classmethod
    @__.overload
    def isFrozenSet(cls, v: _Any, /, type: __.AVT_Type[_T] = _Any) -> __.TypeIs[__.AVT_FrozenSet[_T]]: ...
    
    @classmethod
    @__.overload
    def isFrozenSet(cls, v: _Any, /, type: __.AVT_Tuple[__.AVT_Type[_T], ...]) -> __.TypeIs[__.AVT_FrozenSet[_T]]: ...
    
    @classmethod
    @__.overload
    def isFrozenSet(cls, v: _Any, /, type: _U) -> __.TypeIs[__.AVT_FrozenSet[_U]]: ...
        
    @classmethod
    def isFrozenSet(cls, v, /, type = _Any):
        """
        @lifetime >= 0.3.35 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isFrozenSet
        
        Determine whether a value is a frozenset built-in.
        
        Parameter `type` allows to restrict the frozenset type.
        
        - 0.3.36: Generic types are now allowed. Warning: this feature is experimental
        """
        return _is_sequence_helper(v, type = type) if _Type(v) is frozenset else False
    
    @classmethod
    @__.overload
    def isDeque(cls, v: _Any, /, type: __.AVT_Type[_T] = _Any) -> __.TypeIs[__.AVT_Deque[_T]]: ...
    
    @classmethod
    @__.overload
    def isDeque(cls, v: _Any, /, type: __.AVT_Tuple[__.AVT_Type[_T], ...]) -> __.TypeIs[__.AVT_Deque[_T]]: ...
    
    @classmethod
    @__.overload
    def isDeque(cls, v: _Any, /, type: _U) -> __.TypeIs[__.AVT_Deque[_U]]: ...
    
    @classmethod
    def isDeque(cls, v, /, type = _Any):
        """
        @lifetime >= 0.3.37 (added on 0.3.37a1) \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isDeque
        
        Determine whether a value is a deque.
        
        Parameter `type` allows to restrict the deque type.
        """
        return _is_sequence_helper(v, type = type) if _Type(v) is __.deque else False
    
    @classmethod
    @__.overload
    def isBytes(cls, v: _Any, /) -> __.TypeIs[bytes]: ... # not generic
    
    @classmethod
    @__.overload
    def isBytes(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
        
    @classmethod
    def isBytes(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.35 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isBytes
        
        Determine whether a value is a bytes built-in.
        
        - 0.3.37 (0.3.37a1): many values may be now inspected
        """
        _many = (v,) + _
        return _inspect_many(*_many, type = bytes, mode = mode)
    
    @classmethod
    @__.overload
    def isByteArray(cls, v: _Any, /) -> __.TypeIs[bytearray]: ... # not generic
    
    @classmethod
    @__.overload
    def isByteArray(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isByteArray(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.35 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isByteArray
        
        Determine whether a value is a bytearray built-in.
        
        - 0.3.37 (0.3.37a1): many values may be now inspected
        """
        _many = (v,) + _
        return _inspect_many(*_many, type = bytearray, mode = mode)
    
    # 0.3.54: 'memoryview' generic check (generic since 3.14).
    # type cannot be an union, and only from 4 of these: 'int' (default), 'float', 'bytes' and 'bool'
    if _sys.version_info >= (3, 14): 
        
        @classmethod
        @__.overload
        def isMemoryView(cls, v: _Any, /, type: __.AVT_Type[_T] = int) -> __.TypeIs[__.AVT_MemoryView[_T]]: ...
        
        @classmethod
        @__.overload
        def isMemoryView(cls, v: _Any, /, *_: _Any, type: __.AVT_Type[__.Union[int, float, bytes, bool]] = int) -> bool: ...
            
        @classmethod
        def isMemoryView(cls, v, /, *_, type: __.AVT_Type[_Any] = int):
            """
            @lifetime >= 0.3.35 \\
            https://aveyzan.xyz/aveytense#aveytense.Tense.isMemoryView
            
            Determine whether a value is a memoryview built-in.
            
            - 0.3.37 (0.3.37a1): many values may be now inspected
            - 0.3.59 - 0.3.60: Amendments to integer and floating-point formats
            """
            
            if not cls.isType(type, (int, float, bool, bytes)):
                return False
            
            _many = __.cast(__.AVT_Tuple[__.AVT_MemoryView, ...], (v,) + _)
            
            if _inspect_many(*_many, type = memoryview, mode = _MODE_AND):
                
                _inspect_formats_ = {
                    ["?"]: bool,
                    ["b", "B", "@b", "@B", "h", "H", "@h", "@H", "i", "I", "@i", "@I", "l", "L", "@l", "@L", "q", "Q", "@q", "@Q", "P", "@P"]: int,
                    ["f", "@f", "d", "@d"]: float,
                    ["w"]: bytes
                }
                
                _placeholder = True
                
                for e in _many:
                    for key in _inspect_formats_:
                        if e.format in key:
                            _placeholder = _placeholder and _inspect_formats_[key] is type
                            break
                
                return _placeholder
            
            return False
    
    else:
        @classmethod
        @__.overload
        def isMemoryView(cls, v: _Any, /) -> __.TypeIs[memoryview]: ...
        
        @classmethod
        @__.overload
        def isMemoryView(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
            
        @classmethod
        def isMemoryView(cls, v, /, *_, mode = _MODE_AND):
            """
            @lifetime >= 0.3.35 \\
            https://aveyzan.xyz/aveytense#aveytense.Tense.isMemoryView
            
            Determine whether a value is a memoryview built-in.
            
            - 0.3.37 (0.3.37a1): many values may be now inspected
            - 0.3.59 - 0.3.60: Amendments to integer and floating-point formats
            """
            _many = (v,) + _
            return _inspect_many(*_many, type = memoryview, mode = mode)
        
    if _sys.version_info >= (3, 12):
        
        @classmethod
        @__.overload
        def isArray(cls, v: _Any, /, type: __.AVT_Type[_T] = int) -> __.TypeIs[__.AVT_Array[_T]]: ...
        
        @classmethod
        @__.overload
        def isArray(cls, v: _Any, /, *_: _Any, type: __.AVT_Type[__.Union[int, float, str]] = int) -> bool: ...
            
        @classmethod
        def isArray(cls, v, /, *_, type: __.AVT_Type[_Any] = int):
            """
            @lifetime >= 0.3.37 \\
            https://aveyzan.xyz/aveytense#aveytense.Tense.isArray
            
            Determine whether a value is an array.
            
            - 0.3.59 - 0.3.60: Fixed to support generic version since Python 3.12
            """
            
            if not cls.isType(type, (int, float, bool, str)):
                return False
            
            _many = __.cast(__.AVT_Tuple[__.array[_Any], ...], (v,) + _)
            
            if _inspect_many(*_many, type = __.array, mode = _MODE_AND):
                
                _inspect_typecodes_ = {
                    ["?"]: bool,
                    ["b", "B", "h", "H", "i", "I", "l", "L", "q", "Q"]: int,
                    ["f", "d"]: float
                }
                
                if _sys.version_info >= (3, 16):
                    _inspect_typecodes_.update({ ["w"]: str })
                elif _sys.version_info >= (3, 13):
                    _inspect_typecodes_.update({ ["u", "w"]: str })
                else:
                    _inspect_typecodes_.update({ ["u"]: str })
                
                _placeholder = True
                
                for e in _many:
                    for key in _inspect_typecodes_:
                        if e.typecode in key:
                            _placeholder = _placeholder and _inspect_typecodes_[key] is type
                            break
                
                return _placeholder
            
            return False
            
    else:
    
        @classmethod
        @__.overload
        def isArray(cls, v: _Any, /) -> __.TypeIs[__.array]: ... # generic since 3.12
        
        @classmethod
        @__.overload
        def isArray(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
            
        @classmethod
        def isArray(cls, v, /, *_, mode = _MODE_AND):
            """
            @lifetime >= 0.3.37 \\
            https://aveyzan.xyz/aveytense#aveytense.Tense.isArray
            
            Determine whether a value is an array.
            
            - 0.3.59 - 0.3.60: Fixed to support generic version since Python 3.12
            """
            _many = (v,) + _
            return _inspect_many(*_many, type = __.array, mode = mode)
    
    @classmethod
    @__.overload
    def isClass(cls, v: _Any, /) -> __.TypeIs[__.AVT_Type[_Any]]: ... # >= 0.3.43
        
    @classmethod
    @__.overload
    def isClass(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ... # >= 0.3.43
    
    @classmethod
    def isClass(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.35
        
        Equivalent to `inspect.isclass()`.
        Determine whether a value is a class.
        """
        _many = (v,) + _
        return _inspect_many(*_many, type = type, mode = mode)
    
    @classmethod
    @__.overload
    def isFunction(cls, v: _Any, /) -> __.TypeIs[_types.FunctionType]: ... # >= 0.3.43
        
    @classmethod
    @__.overload
    def isFunction(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ... # >= 0.3.43
    
    @classmethod
    def isFunction(cls, v, /, *_, mode = _MODE_AND): # not generic
        """
        @lifetime >= 0.3.35
        
        Equivalent to `inspect.isfunction()`.
        Determine whether a value is a function.
        """
        _many = (v,) + _
        return _inspect_many(*_many, type = _types.FunctionType, mode = mode)
    
    @classmethod
    @__.overload
    def isBinary(cls, v: _Any, /) -> bool: ...
    
    @classmethod
    @__.overload
    def isBinary(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isBinary(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.38
        
        Returns `True`, if value is a number in binary notation in a string.
        Many values can be inspected at once as well. Prefix `0b` is ignored.
        """
        _many = (v,) + _
        return _inspect_numerics(*_many, mode = "b", lmode = mode)
    
    @classmethod
    @__.overload
    def isOctal(cls, v: _Any, /) -> bool: ...
    
    @classmethod
    @__.overload
    def isOctal(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isOctal(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.38
        
        Returns `True`, if value is a number in octal notation in a string.
        Many values can be inspected at once as well. Prefix `0o` is ignored.
        """
        _many = (v,) + _
        return _inspect_numerics(*_many, mode = "o", lmode = mode)
    
    @classmethod
    @__.overload
    def isNumeric(cls, v: _Any, /) -> bool: ...
    
    @classmethod
    @__.overload
    def isNumeric(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isNumeric(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.41
        
        Returns `True`, if value is a number in decimal notation in a string.
        Many values can be inspected at once as well. 0.3.43: Renamed from `isDecimal2`
        
        In reality returned is `True` when `re.match(r"\\d", value)` is satisfied.
        """
        _many = (v,) + _
        return _inspect_numerics(*_many, mode = "d", lmode = mode)
    
    @classmethod
    @__.overload
    def isHexadecimal(cls, v: _Any, /) -> bool: ...
    
    @classmethod
    @__.overload
    def isHexadecimal(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isHexadecimal(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.38
        
        Returns `True`, if value is a number in hexadecimal notation in a string.
        Many values can be inspected at once as well. Prefix `0x` is ignored.
        """
        
        _many = (v,) + _
        return _inspect_numerics(*_many, mode = "h", lmode = mode)
    
    @classmethod
    @__.overload
    def isFinalVar(cls, v: _Any, /) -> __.TypeIs[_util.FinalVarType]: ...
    
    @classmethod
    @__.overload
    def isFinalVar(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isFinalVar(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.38 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isFinalVar
        
        Returns `True`, if value is a final variable (instance of `aveytense.util.FinalVar`).
        
        Restricting final variable type is currently rethought, for now use:
        `self.isFinalVar(v) and type(v.x) is int`
        """
        
        _many = (v,) + _
        return _inspect_many(*_many, type = _util.FinalVarType, mode = mode)
    
    @classmethod
    @__.overload
    def isSlice(cls, v: _Any, /) -> __.TypeIs[slice]: ...
    
    @classmethod
    @__.overload
    def isSlice(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isSlice(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.41 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isSlice
        
        Determine whether a value is a slice object.
        """
        _many = (v,) + _
        return _inspect_many(*_many, type = slice, mode = mode)
    
    @classmethod
    @__.overload
    def isProperty(cls, v: _Any, /) -> __.TypeIs[property]: ...
    
    @classmethod
    @__.overload
    def isProperty(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isProperty(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.41 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isProperty
        
        Determine whether a value is a property in a class. It can be done only, if property is accessed via reference.
        """
        _many = (v,) + _
        return _inspect_many(*_many, type = property, mode = mode)
    
    if versionInfo >= (0, 3, 42) or True:
        
        @classmethod
        @__.overload
        def isFinalProperty(cls, v: __.AVT_Tuple[type, str], /) -> bool: ...
        
        @classmethod
        @__.overload
        def isFinalProperty(cls, v: __.AVT_Tuple[type, str], /, *_: __.AVT_Tuple[type, str], mode: _Mode = _MODE_AND) -> bool: ...
        
        @classmethod
        @__.overload
        def isFinalProperty(cls, v: __.AVT_Tuple[type, str], /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
        
    if versionInfo >= (0, 3, 43) or True:
        
        @classmethod
        @__.overload
        def isFinalProperty(cls, v: _Any, /) -> __.TypeIs[_util.finalproperty[__.Any]]: ...
        
    else:
        
        @classmethod
        @__.overload
        def isFinalProperty(cls, v: _Any, /) -> bool: ...
        
    @classmethod
    @__.overload
    def isFinalProperty(cls, v: _Any, /, *_: __.AVT_Tuple[type, str], mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    @__.overload
    def isFinalProperty(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isFinalProperty(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.41 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isFinalProperty
        
        Returns `True`, if a property is final. It can be done only, if property is accessed via reference.
        
        See `~.util.finalproperty` decorator for more details.
        """
        
        _many = (v,) + _
        _placeholder = True    
        
        for one in _many:
            
            # If we referred to class member from a class instance directly, we would already obtain a value from final property,
            # and this also works for accessing via class reference. That makes it practically impossible to check without the property's
            # parent in separate parameter, hence we need a tuple with the class and its member as a string. This was troublesome before
            # 0.3.43. However, this technique will be kept for backward-compatibility with 0.3.42.
            # 29.03.2025
            
            if cls.isTuple(one, (type, str)) and reckon(one) == 2 and isinstance(one[0], type) and isinstance(one[1], str):
                
                # Much simplier than 'not ~.isNone(one[0].__dict__.get(one[1], None))'
                if one[1] in one[0].__dict__:
                    
                    t = one[0].__dict__[one[1]]
                
                    if mode in (_MODE_AND, "and"):
                        _placeholder = _placeholder and bool(isinstance(t, _util.finalproperty) or (cls.isProperty(t) and (t.fset, t.fdel) == (None, None)))
                        
                    elif mode in (_MODE_OR, "or"):
                        _placeholder = _placeholder or bool(isinstance(t, _util.finalproperty) or (cls.isProperty(t) and (t.fset, t.fdel) == (None, None)))
                        
                    else:
                        return False
                    
                else:
                    return False
            
            else:
                
                if mode in (_MODE_AND, "and"):
                    _placeholder = _placeholder and bool(isinstance(one, _util.finalproperty) or (cls.isProperty(one) and (one.fset, one.fdel) == (None, None)))
                    
                elif mode in (_MODE_OR, "or"):
                    _placeholder = _placeholder or bool(isinstance(one, _util.finalproperty) or (cls.isProperty(one) and (one.fset, one.fdel) == (None, None)))
                    
                else:
                    return False
            
        return _placeholder
            
    @classmethod
    @__.overload
    def isFinalClass(cls, v: _Any, /) -> bool: ...
    
    @classmethod
    @__.overload
    def isFinalClass(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isFinalClass(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.41
        
        Returns `True`, if provided class is final (cannot be subclassed).
        
        It is true when class inherits from `~.util.Final`.
        """
        
        def _check_if_final(value):
            
            if cls.isClass(value):
                
                # In this attempt, we try to subclass the class - on failure it returns True
                try:
                    class _test(value): ...
                    
                except exceptions.SubclassedError:
                    return True
                
                else:
                    return (
                        (_util.Final in value.__bases__) or
                        ("__final__" in value.__dict__ and value.__final__ is True) or issubclass(value, _util.Final)
                    )
                
            else:
                return False
        
        if reckon(_) == 0:
            
            return _check_if_final(v)
            
        else:
            
            _many = (v,) + _
            
            if mode in (cls.AND, "and"):
                
                return all([_check_if_final(e) for e in _many])
            
            elif mode in (cls.OR, "or"):
                
                return any([_check_if_final(e) for e in _many])
            
            else:
                
                return False
            
    @classmethod
    def isUnbound(cls, f: __.AVT_Callable[..., _Any], v: str, /):
        """
        @lifetime >= 0.3.44 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isUnbound
        
        Returns `True`, if variable `v` in function `f` is unbound.
        
        It is `False` for nondescript variables. To return `True`, concerned
        variable must be referenced in the function's code, and defined in a
        statement (or more, and not outside) which won't be invoked at runtime.
        Other way is referencing the variable before its definition.
        
        This method cannot be invoked in function, which was passed as a parameter
        in this method, as this method may not return any value.
        
        It is `True` for the following example::
        
            from aveytense import Tense
            
            def test():
            
                if False:
                    e = 62
                    
                e # if it was lacking, False would be returned
                    
            print(Tense.isUnbound(test, "e")) # True
        """
        
        # 0.3.46
        if _inspect.ismethod(f) and cls.test(str(f), r"<unbound method '{}'>".format(f.__qualname__)):
            return True
        
        if not callable(f):
            error = TypeError("first parameter must be a callable") # edit 0.3.46. previous ending: must be parameter-less callable
            raise error
        
        try:
            
            if not cls.isString(v):
                error = TypeError("second parameter must be a string")
                raise error
            
        except RecursionError:
            return False
            
        try:
            f()
            
        except RecursionError:
            return False
        
        except TypeError as exc: # >= 0.3.46
            
            if str(exc).startswith("unbound method"):
                return True
            
        # don't permit custom messages
        except UnboundLocalError as exc:
            
            from ._collection import _exceptions
            
            _exception_ = lambda v: [e.format(v) for e in _exceptions._unbound_local_messages]
                
            if str(exc) in _exception_(v):
                return True
            
        return False
    
    @classmethod
    @__.overload
    def isLambda(cls, v: _Any, /) -> __.TypeIs[__.FunctionType]: ...
    
    @classmethod
    @__.overload
    def isLambda(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isLambda(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.52
        
        Check if value is a lambda expression
        """
        
        _all_ = (v,) + _
        _use_ = all if mode in ("and", _MODE_AND) else any
        
        return _use_([isinstance(e, __.LambdaType) for e in _all_])
    
    @classmethod
    @__.overload
    def isIterable(cls, v: _Any, /) -> __.TypeIs[__.AVT_Iterable[_Any]]: ...
    
    @classmethod
    @__.overload
    def isIterable(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isIterable(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.52
        
        Check if value is an iterable object
        """
        
        _all_ = (v,) + _
        _use_ = all if mode in ("and", _MODE_AND) else any
        
        return _use_([_is_iterable(e) for e in _all_])
    
    @classmethod
    @__.overload
    def isIterator(cls, v: _Any, /) -> __.TypeIs[__.AVT_Iterator[_Any]]: ...
    
    @classmethod
    @__.overload
    def isIterator(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isIterator(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.52
        
        Check if value is an iterator
        """
        
        _all_ = (v,) + _
        _use_ = all if mode in ("and", _MODE_AND) else any
        
        return _use_([isinstance(e, __.Iterator) for e in _all_])
    
    @classmethod
    @__.overload
    def isAwaitable(cls, v: _Any, /) -> __.TypeIs[__.AVT_Awaitable[_Any]]: ...
    
    @classmethod
    @__.overload
    def isAwaitable(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isAwaitable(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.52
        
        Check if value is an awaitable object
        """
        
        _all_ = (v,) + _
        _use_ = all if mode in ("and", _MODE_AND) else any
        
        return _use_([isinstance(e, __.Awaitable) for e in _all_])
    
    @classmethod
    @__.overload
    def isGenerator(cls, v: _Any, /) -> __.TypeIs[__.AVT_Generator[_Any, _Any, _Any]]: ...
    
    @classmethod
    @__.overload
    def isGenerator(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isGenerator(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.52
        
        Check if value is an generator object
        """
        
        _all_ = (v,) + _
        _use_ = all if mode in ("and", _MODE_AND) else any
        
        return _use_([isinstance(e, __.Generator) for e in _all_])
    
    @classmethod
    @__.overload
    def isGenExpr(cls, v: _Any, /) -> __.TypeIs[__.AVT_Generator[_Any, None, None]]: ...
    
    @classmethod
    @__.overload
    def isGenExpr(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isGenExpr(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.52
        
        Check if value is a generator object from generator expression
        """
        
        _all_ = (v,) + _
        _use_ = all if mode in ("and", _MODE_AND) else any
        
        return _use_([isinstance(e, __.GenExprType) for e in _all_])
    
    @classmethod
    @__.overload
    def isCoroutine(cls, v: _Any, /) -> __.TypeIs[__.AVT_Coroutine[_Any, _Any, _Any]]: ...
    
    @classmethod
    @__.overload
    def isCoroutine(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isCoroutine(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.52
        
        Check if value is a coroutine object
        """
        
        _all_ = (v,) + _
        _use_ = all if mode in ("and", _MODE_AND) else any
        
        return _use_([isinstance(e, __.Coroutine) for e in _all_])
    
    @classmethod
    @__.overload
    def isAsyncGenerator(cls, v: _Any, /) -> __.TypeIs[__.AVT_AsyncGenerator[_Any, _Any]]: ...
    
    @classmethod
    @__.overload
    def isAsyncGenerator(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isAsyncGenerator(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.53
        
        Check if value is an asynchronous generator
        """
        
        _all_ = (v,) + _
        _use_ = all if mode in ("and", _MODE_AND) else any
        
        return _use_([isinstance(e, __.AsyncGenerator) for e in _all_])
    
    @classmethod
    @__.overload
    def isGeneric(cls, v: type, /) -> bool: ...
    
    @classmethod
    @__.overload
    def isGeneric(cls, v: type, /, *_: type, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isGeneric(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.53 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.isGeneric
        
        Check if value is a generic class, or subscriptable type overall.
        
        This does not include special forms of `typing`, use
        `isSpecialForm()` instead
        """
        
        _all_ = (v,) + _
        _use_ = all if mode in ("and", _MODE_AND) else any
        
        def _internals(v):
            
            if isinstance(v, __.TypingGenericType) and _sys.version_info < (3, 9):
                return True
            
            if not isinstance(v, type):
                error = TypeError("expected type(s)")
                raise error
            
            _val_ = issubclass(v, __.Generic)
            
            if _sys.version_info >= (3, 9):
                _val_ = _val_ or hasattr(v, "__class_getitem__")
                
            if not _val_:
            
                try:
                    extensions.exec("{}[__.Any]".format(v.__qualname__), globals = globals())
                except Exception as exc:
                    
                    if isinstance(exc, TypeError) and _sys.version_info < (3, 9):
                        
                        if str(exc).startswith("Too few parameters for"):
                            return True
                        
                    return False
                
            return True
        
        return _use_([_internals(t) for t in _all_])
    
    @classmethod
    @__.overload
    def isSpecialForm(cls, v: _Any, /) -> bool: ...
    
    @classmethod
    @__.overload
    def isSpecialForm(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isSpecialForm(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.53
        
        Special forms/typings on `typing` module
        """
        
        _all_ = (v,) + _
        _use_ = all if mode in ("and", _MODE_AND) else any
        
        return _use_([isinstance(e, __.SpecialForm) for e in _all_])
    
    if _sys.version_info >= (3, 10):
    
        @classmethod
        @__.overload
        def isUnion(cls, v: _Any, /) -> __.TypeIs[__.Union[__.TypingUnionType, __.UnionType]]: ...
        
    else:
        
        @classmethod
        @__.overload
        def isUnion(cls, v: _Any, /) -> __.TypeIs[__.TypingUnionType]: ...
        
    @classmethod
    @__.overload
    def isUnion(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND) -> bool: ...
    
    @classmethod
    def isUnion(cls, v, /, *_, mode = _MODE_AND):
        """
        @lifetime >= 0.3.62
        
        Returns `True` if value is an union type
        """
        
        _all_ = (v,) + _
        _use_ = all if mode in ("and", _MODE_AND) else any
        
        return _use_([cls.isType(__.getOrigin(e), _UnionTypes) for e in _all_])
    
    @classmethod
    def isDeprecated(cls, v: _Any, /, *_: _Any, mode: _Mode = _MODE_AND):
        """
        @lifetime >= 0.3.56
        
        Determine if a definition is deprecated
        
        To return `True`, the `__deprecated__` attribute of the definition(s) must be string(s); preferably use the `@deprecated` decorator instead of setting it manually.
        
        `@deprecated` decorator is featured by `warnings` library since Python 3.13, and `typing_extensions` prior to it and since by importing from `warnings`
        """
        
        _all_ = (v,) + _
        _use_ = all if mode in ("and", _MODE_AND) else any
        
        return _use_([isinstance(getattr(e, "__deprecated__", None), str) for e in _all_])
    
    
    # OVERLOAD >= 0.3.34; < 0.3.39
    @classmethod
    def any(cls, i: __.AVT_Iterable[_T], /, condition: _cal[[_T], bool] = ...):
        """
        @lifetime >= 0.3.26rc2 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.any
        
        A little extension of inbuilt function `any()`.
        - 0.3.40: any iterable is now allowed, and replaced `None` with ellipsis
        - 0.3.34: `any()` now returns boolean rather than shallow copy of sequence
        """
        
        if not isinstance(i, __.Iterable):
            error = TypeError("expected an iterable")
            raise error
        
        if not cls.isEllipsis(condition) and not _is_bool_callback(condition):
            error = TypeError("expected a callable with parameter without default value or ellipsis in parameter 'condition'")
            raise error
        
        # 0.3.40
        if reckon(i) == 0:
            return False
        
        # 0.3.40; refer to constructor of 'bool'
        _cond = condition if not cls.isEllipsis(condition) else lambda x: bool(x)
            
        for e in list(i):
            
            # for better results consider using function/method that returns a boolean value
            if _cond(e):
                return True
            
        return False
    
    # OVERLOAD >= 0.3.34; < 0.3.40
    @classmethod
    def all(cls, i: __.AVT_Iterable[_T], /, condition: _cal[[_T], bool] = ...): # slash was after 'condition' parameter before (0.3.34)
        """
        @lifetime >= 0.3.26rc2 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.all
        
        Extension of inbuilt function `all()`
        - 0.3.40: any iterable is now allowed, removed change from 0.3.36. Replace `None` with ellipsis
        - 0.3.36: if condition was a callable, it must return boolean value, otherwise will always return `False`
        - 0.3.34: `all()` now returns boolean rather than shallow copy of sequence
        - 0.3.27a4: removed parameter `default`.
        """
        
        if not isinstance(i, __.Iterable):
            error = TypeError("expected an iterable")
            raise error
        
        if not cls.isEllipsis(condition) and not _is_bool_callback(condition):
            error = TypeError("expected a callable with parameter without default value or ellipsis in parameter 'condition'")
            raise error
        
        # 0.3.40
        if reckon(i) == 0:
            return False
        
        # 0.3.40; refer to constructor of 'bool'
        _cond = condition if not cls.isEllipsis(condition) else lambda x: bool(x)
        
        for e in list(i):
            
            # for better results consider using function/method that returns a boolean value
            if not _cond(e):
                return False
            
        return True
    
    @classmethod
    @__.overload
    def test(cls, target: str, pattern: _Pattern[str], flags: _FlagsType = 0) -> bool: ...
    
    @classmethod
    @__.overload # >= 0.3.62: 'bytearray' as pattern
    def test(cls, target: __.ReadableBuffer, pattern: __.Union[bytearray, _Pattern[bytes]], flags: _FlagsType = 0) -> bool: ...
    
    @classmethod
    def test(cls, target, pattern, flags = 0):
        """
        @lifetime >= 0.3.42 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.test
        
        Equivalent to `RegExp.test()` method from JavaScript and `re.match()` in Python;
        only difference between this class method and `re.match()` is that `Match` object is
        considered `True`, meaning it is the same as::
        
            return re.match(pattern, target, flags) is not None
        
        Target and pattern must be both either `str` or, respectively, `bytes` and buffer.
        Pattern can be also instance of `re.Pattern`.
        """
        
        if isinstance(pattern, bytearray): # >= 0.3.62
            _pattern = bytes(pattern)
        else:
            _pattern = pattern
        
        # Clarification concerning 're.Pattern' instances:
        # 're.Pattern' is actually a generic class that can take only one type argument, and it can be only 'str' or 'bytes'.
        # Before 0.3.62, technique with 'extensions.get_args(pattern) == (str|bytes,)' was used before discovery of the
        # 'pattern' property. Because 're.Pattern' is a generic class since Python 3.9, Python 3.8 will need to use the
        # currently used technique 'Tense.isString|isBytes(pattern.pattern)'.
        if (
            (cls.isString(target) and (cls.isString(_pattern) or (isinstance(_pattern, __.Pattern) and cls.isString(_pattern.pattern))) or
            (isinstance(target, __.ReadableBuffer) and (cls.isBytes(_pattern) or (isinstance(_pattern, __.Pattern) and cls.isBytes(_pattern.pattern))))) and
            isinstance(flags, (int, _re.RegexFlag))
        ):
            
            return _re.match(_pattern, target, flags) is not None
        
        else:
            
            error = TypeError("expected '{}' and '{}' to match one of following type patterns: 'str' + 'str', 'str' + 're.Pattern[str]', 'bytes' + 'collections.abc.Buffer', 'bytes' + 're.Pattern[bytes]', and expected '{}' to be an integer or 're.RegexFlag'".format(*tuple(_get_all_params(cls.test))))
            raise error
    
    @classmethod
    @__.overload
    def startsWith(cls, s: str, prefix: __.Union[str, __.AVT_Tuple[str, ...]], /, start: __.Optional[__.Indexable] = ..., end: __.Optional[__.Indexable] = ...) -> bool: ...
    
    @classmethod
    @__.overload
    def startsWith(cls, b: __.Union[bytes, bytearray], prefix: __.Union[__.ReadableBuffer, __.AVT_Tuple[__.ReadableBuffer, ...]], /, start: __.Optional[__.Indexable] = ..., end: __.Optional[__.Indexable] = ...) -> bool: ...
    
    @classmethod
    def startsWith(cls, target, prefix, /, start = ..., end = ...):
        """
        @lifetime >= 0.3.42 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.startsWith
        
        `[str|bytes|bytearray].startswith()`
        """
        
        if (isinstance(target, str) and isinstance(prefix, str)) or \
            (isinstance(target, (bytes, bytearray)) and isinstance(prefix, __.ReadableBuffer)):
                
            _start = 0 if start in (None, ...) else start
            _end = reckon(target) - 1 if end in (None, ...) else end
                
            return target.startswith(prefix, _start, _end)
        
        error = TypeError("expected 'str' + 'str' or 'bytes/bytearray' + 'bytes-like'")
        raise error
    
    
    @classmethod
    @__.overload
    def endsWith(cls, s: str, suffix: __.Union[str, __.AVT_Tuple[str, ...]], /, start: __.Optional[__.Indexable] = ..., end: __.Optional[__.Indexable] = ...) -> bool: ...
    
    @classmethod
    @__.overload
    def endsWith(cls, b: __.Union[bytes, bytearray], suffix: __.Union[__.ReadableBuffer, __.AVT_Tuple[__.ReadableBuffer, ...]], /, start: __.Optional[__.Indexable] = ..., end: __.Optional[__.Indexable] = ...) -> bool: ...
    
    @classmethod
    def endsWith(cls, v, suffix, /, start = ..., end = ...):
        """
        @lifetime >= 0.3.42 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.endsWith
        
        `[str|bytes|bytearray].endswith()`
        """
        
        if (isinstance(v, str) and isinstance(suffix, str)) or \
            (isinstance(v, (bytes, bytearray)) and isinstance(suffix, __.ReadableBuffer)):
                
            _start = 0 if start in (None, ...) else start
            _end = reckon(v) - 1 if end in (None, ...) else end
                
            return v.endswith(suffix, _start, _end)
        
        error = TypeError("expected 'str' + 'str' or 'bytes/bytearray' + 'bytes-like'")
        raise error
                        
    if _version.VERSION_INFO >= (0, 3, 78) and False: # >= 18.03.2025
        
        @classmethod
        def replace(self, target: _Target, pattern: _uni[_Pattern, __.AVT_Tuple[str, ...]], value: _uni[_Target, _cal[[_re.Match[_Target]], _Target], __.AVT_Tuple[str, ...]], count = -1, flags: _FlagsType = 0):
            
            if not self.isInteger(count):
                
                error = TypeError("expected 'count' to be an integer")
                raise error
            
            if type(flags) not in (int, _re.RegexFlag):
                
                error = TypeError("expected 'flags' to be an integer or enum member of 're.RegexFlag'")
                raise error
            
            if self.isString(target):
                
                # comply with re.sub()
                _count = 0 if count == -1 else count
                
                if flags in (0, _re.NOFLAG):
                    
                    _new = target
                    
                    if self.isString(pattern):
                        
                        if self.isString(value):
                        
                            return target.replace(pattern, value, count)
                        
                        elif self.isTuple(value, str):
                            
                            for s in value:
                                
                                _new = _new.replace(pattern, s, count)
                                
                            return _new
                    
                    elif self.isTuple(pattern, str):
                        
                        if self.isString(value):
                        
                            for s in pattern:
                                
                                _new = _new.replace(s, value, count)
                                
                            return _new
                        
                        elif self.isTuple(value, str):
                            
                            for s1 in pattern:
                                
                                for s2 in value:
                                    
                                    _new = _new.replace(s1, s2, count)
                                    
                            return _new
                
                if (
                    (self.isString(pattern) or (isinstance(pattern, __.Pattern) and __.get_args(pattern) == (str,))) and
                    (self.isString(value) or (callable(value) and reckon(_get_all_params(value)) == 1))
                ):
                    
                    # typing.Any is deduced
                    a = _re.sub(pattern, value, target, _count, flags)
                    return str(a)
    
    # >= 0.3.45: Annotation in parameter 'm'
    @classmethod
    def expect(cls, i: __.AVT_Iterable[_T], m: __.Union[str, range, _ab_mod.AbroadInitializer, __.AVT_Uniqual[int]] = ">= 1", /, condition: __.AVT_Callable[[_T], bool] = ...):
        """
        @lifetime >= 0.3.40 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.expect
        
        Returns `True` whether specific number of items in an iterable satisfied `condition`.
        If `m` is `">= 1"` or `"1 <="`, this method will behave the same as `Tense.any()`.
        
        `m` must be a valid string literal, like `"> 3"`, otherwise `TypeError` is thrown.
        To rebuild `Tense.any()`, use `">= 1"`. To rebuild `Tense.all()`, use `"== len"`.
        
        Since 0.3.45 it is allowed to pass a set of positive integers to parameter `m`. This thing
        was meant to be provided in version 0.3.48.
        
        See documentation for more details.
        """
        
        if not _is_iterable(i):
            error = TypeError("expected an iterable in first positional parameter")
            raise error
        
        if cls.versionInfo >= (0, 3, 45) or True:
            
            if not isinstance(m, (str, range, _ab_mod.AbroadInitializer, __.Uniqual)) or (isinstance(m, (range, _ab_mod.AbroadInitializer, __.Uniqual)) and not Math.isPositive(list(m))): # all must satisfy
                error = TypeError("expected a valid string literal, like \"> 3\", or a positive integer set, range or abroad object")
                raise error
            
        else:
        
            if not cls.isString(m) or (cls.isString(m) and not _re.match(r"^(\d+|len) ?(<=|>=|==|!=|<|>)$|^(<=|>=|!=|==|<|>) ?(\d+|len)$", m)):
                error = TypeError("expected a valid string literal, like \"> 3\"")
                raise error
        
        if not (cls.isEllipsis(condition) or _is_bool_callback(condition)):
            error = TypeError("expected a callable with parameter without default value or ellipsis in parameter 'condition'")
            raise error
        
        if m in (">= 1", "1 <="):
            return cls.any(i, condition)
        
        # just like Tense.any(), this method returns False, because 'for' loop is skipped for empty iterables
        # for empty iterable Python any() function would return True
        if reckon(i) == 0:
            return False
        
        # pre-inspection that a callback returns boolean, same behavior as in Tense.all()
        if not cls.isType(type(condition(i[0])), bool):
            error = TypeError("callable in parameter 'condition' must return a boolean value")
            raise error
        
        # gimmick of this part of the code is about creating callable variable
        # and it allows to shorten the code since more 'if' statements would be required
        # when invoked, with both versions it will return boolean
        _cond = condition if not cls.isEllipsis(condition) else lambda x: bool(x)
        
        if cls.isString(m): # <- 0.3.45
        
            _tmp = str(_re.findall(r"(\d+|len)", m)[0])
            
            if _re.match(r"len", _tmp):
                _tmp = str(reckon(i))
            
            # integer with leading zeros isn't allowed (Python error not everyone can expect)
            if _tmp.startswith("0"):
                error = TypeError("leading zeros in decimal integer literals are not permitted in parameter 'm'")
                raise error
            
            # it is obligatory for integer to be in range [1; len], for zero matches you can use "< 1"
            if not Math.isInRange(int(_tmp), 1, reckon(i)):
                error = TypeError("expected an integer in a string in parameter 'm' in range [1; iterable_length]; for zero matches use \"< 1\"")
                raise error
            
            if _re.match(r"^(\d+|len) ?<=$|^>= ?(\d+|len)$", m):
                return reckon([e for e in i if _cond(e)]) >= int(_tmp)
            
            elif _re.match(r"^(\d+|len) ?>=$|^<= ?(\d+|len)$", m):
                return reckon([e for e in i if _cond(e)]) <= int(_tmp)
            
            elif _re.match(r"^(\d+|len) ?<$|^> ?(\d+|len)$", m):
                return reckon([e for e in i if _cond(e)]) > int(_tmp)
            
            elif _re.match(r"^(\d+|len) ?>$|^< ?(\d+|len)$", m):
                return reckon([e for e in i if _cond(e)]) < int(_tmp)
            
            elif _re.match(r"^(\d+|len) ?!=$|^!= ?(\d+|len)$", m):
                return reckon([e for e in i if _cond(e)]) != int(_tmp)
            
            else:
                return reckon([e for e in i if _cond(e)]) == int(_tmp)
            
        else:
            
            # >= 0.3.45
            return reckon([e for e in i if _cond(e)]) in list(m)
    
    @classmethod
    def hasAttr(cls, o: object, attr: __.Union[str, __.AVT_Tuple[str, ...]], /) -> bool:
        """
        @lifetime >= 0.3.34 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.hasattr
        
        Extension to inbuilt function `hasattr()`, allowing to check multiple attributes at once
        
        Check update from 0.3.61 regarding removal of `mode` parameter and no multiple objects support
        """
        
        if cls.isString(attr):
            _seq = attr.strip().split(" ")
        elif cls.isTuple(attr, str):
            _seq = list(attr)
        else:
            error = TypeError("expected a string tuple or a string in parameter 'attr'")
            raise error
        
        _seq = list(filter(lambda x: reckon(x) > 0, _seq))
        
        for a in _seq:
            if hasattr(o, a):
                return True
            
        return False
    
    @classmethod
    def group(cls, *statements: _uni[__.AVT_Sequence[bool], __.AVT_Uniqual[bool]], mode = "and-or"):
        """
        @lifetime >= 0.3.34
        
        Returns one boolean value combining all statements into one boolean value.
        Parameter `mode` determines about used logical operators inside and outside
        provided sequences. Possible values (with `and`, `or`, `nand` = `and not`, `nor` = `or not`):
        
        - `"and-or"` = `(a1 and a2 and ... and aN) or (b1 and b2 and ... and bN) or ...`
        - `"or-and"` = `(a1 or a2 or ... or aN) and (b1 or b2 or ... or bN) and ...`
        - `"and-nor"` = `not (a1 and a2 and ... and aN) or not (b1 and b2 and ... and bN) or not ...`
        - `"nor-and"` = `(not a1 or not a2 or not ... or not aN) and (not b1 or not b2 or not ... or not bN) and ...`
        - `"nand-or"` = `(not a1 and not a2 and not ... and not aN) or (b1 and not b2 and not ... and not bN) or ...`
        - `"or-nand"` = `not (a1 or a2 or ... or aN) and not (b1 or b2 or ... or bN) and not ...`
        - `"nand-nor"` = `not (not a1 and not a2 and not ... and not aN) or not (b1 and not b2 and not ... and not bN) or not ...`
        - `"nor-nand"` = `not (not a1 or not a2 or not ... or not aN) and not (not b1 or not b2 or not ... or not bN) and not ...`
        
        On 0.3.40 added missing modes (and case is now insensitive):
        - `"and-nand"` = `not (a1 and a2 and ... and aN) and not (b1 and b2 and ... and bN) and not ...`
        - `"nand-and"` = `(not a1 and not a2 and not ... and not aN) and (not b1 and not b2 and not ... and not bN) and ...`
        - `"or-nor"` = `not (a1 or a2 or ... or aN) or not (b1 or b2 or ... or bN) or not ...`
        - `"nor-or"` = `(not a1 or not a2 or not ... or not aN) or (not b1 or not b2 or not ... or not bN) or ...`
        
        Note: using modes `"and-and"`, `"or-or"`, `"nand-nand"` and `"nor-nor"` is discouraged,
        but will be kept to save some time writing `and`, `or` and `not` operators
        """
        
        if not cls.isString(mode):
            
            error = TypeError("expected a string in parameter 'mode'")
            raise error
        
        _mode = mode.lower()
        _modes = ("and-or", "or-and", "and-nor", "nor-and", "nand-or", "or-nand", "nand-nor", "nor-nand", "and-and", "or-or", "nand-nand", "nor-nor", "and-nand", "nand-and", "or-nor", "nor-or")
        
        if _mode not in _modes:
            
            error = ValueError("expected a valid mode from following: {}".format(", ".join(_modes)))
            raise error
        
        for statement in statements:
            
            if not isinstance(statement, (__.Sequence, __.Uniqual)) or (isinstance(statement, (__.Sequence, __.Uniqual)) and not cls.isList(list(statement), bool)):
                
                error = ValueError("expected non-empty sequence(s) with single boolean values, like list, tuple, set or frozenset")
                raise error
            
            
        _result = _subresult = True
        
        for statement in statements:
            
            if _mode == "and-and":
                
                for s in statement:
                    _subresult = _subresult and s
                    
                _result = _result and _subresult
                
            elif _mode == "and-nor":
                
                for s in statement:
                    _subresult = _subresult or not s
                    
                _result = _result and _subresult
                
            elif _mode == "and-or":
                
                for s in statement:
                    _subresult = _subresult or s
                    
                _result = _result and _subresult
                
            elif _mode == "nand-nand":
                
                for s in statement:
                    _subresult = _subresult and not s
                    
                _result = _result and not _subresult
                
            elif _mode == "nand-nor":
                
                for s in statement:
                    _subresult = _subresult or not s
                    
                _result = _result and not _subresult
                
            elif _mode == "nand-or":
                
                for s in statement:
                    _subresult = _subresult or s
                    
                _result = _result and not _subresult
                
            elif _mode == "nor-and":
                
                for s in statement:
                    _subresult = _subresult and s
                    
                _result = _result or not _subresult
                
            elif _mode == "nor-nand":
                
                for s in statement:
                    _subresult = _subresult and not s
                    
                _result = _result or not _subresult
                
            elif _mode == "nor-nor":
                
                for s in statement:
                    _subresult = _subresult or not s
                    
                _result = _result or not _subresult
                
            elif _mode == "or-and":
                
                for s in statement:
                    _subresult = _subresult and s
                    
                _result = _result or _subresult
                
            elif _mode == "or-nand":
                
                for s in statement:
                    _subresult = _subresult and not s
                    
                _result = _result or _subresult
                
            elif _mode == "or-or":
                
                for s in statement:
                    _subresult = _subresult or s
                    
                _result = _result or _subresult
                
            elif _mode == "and-nand":
                
                for s in statement:
                    _subresult = _subresult and not s
                    
                _result = _result and _subresult
                
            elif _mode == "nand-and":
                
                for s in statement:
                    _subresult = _subresult and s
                    
                _result = _result and not _subresult
                
            elif _mode == "nor-or":
                
                for s in statement:
                    _subresult = _subresult or s
                    
                _result = _result or not _subresult
                
            else:
                
                for s in statement:
                    _subresult = _subresult or not s
                    
                _result = _result or _subresult
                
            _subresult = True
            
        return _result
    
    @classmethod
    def equal(cls, *v: _T):
        """
        @lifetime >= 0.3.41 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.equal
        
        Returns `True` if all values are equal to each other.
        
        Same as::

            v[0] == v[1] and v[1] == v[2] and v[2] == v[3] and ...
            v[0] == v[1] == v[2] == v[3] == ...
            
        For no values and no type accordance returned is `False`.
        """
        
        if reckon(v) == 0:
            return False
        
        _placeholder = True
        _type_all = type(v[0])
        
        for i in abroad(1, v):
            
            if type(v[i - 1]) is not _type_all:
                return False
            
            _placeholder = _placeholder and v[i - 1] == v[i]
            
        return _placeholder
    
    @classmethod
    def inequal(cls, *v: _T):
        """
        @lifetime >= 0.3.41 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.inequal
        
        Returns `True` if all values are inequal to each other.
        
        Same as::

            v[0] != v[1] and v[1] != v[2] and v[2] != v[3] and ...
            v[0] != v[1] != v[2] != v[3] != ...
            
        For no values and no type accordance returned is `False`.
        """
        
        if reckon(v) == 0:
            return False
        
        _placeholder = True
        _type_all = type(v[0])
        
        for i in abroad(1, v):
            
            if type(v[i - 1]) is not _type_all:
                return False
            
            _placeholder = _placeholder and v[i - 1] != v[i]
            
        return _placeholder
    
    @classmethod
    def abroadPositive(cls, value1: _AbroadValue1[_T1], /, value2: _AbroadValue2[_T2] = None, modifier: _AbroadModifier[_T3] = None):
        """
        @lifetime >= 0.3.24 \\
        @modified 0.3.25 (moved slash to between `value1` and `value2`), 0.3.29, 0.3.52
        
        Every negative integer is coerced to positive.
        """
        ab = abroad(value1, value2, modifier)
        return type(ab)([abs(e) for e in ab], abs(ab.params[0]), abs(ab.params[1]), ab.params[2])
    
    @classmethod
    def abroadNegative(cls, value1: _AbroadValue1[_T1], /, value2: _AbroadValue2[_T2] = None, modifier: _AbroadModifier[_T3] = None):
        """
        @lifetime >= 0.3.24 \\
        @modified 0.3.25 (moved slash to between `value1` and `value2`), 0.3.29, 0.3.52
        
        Every positive integer is coerced to negative.
        """
        ab = abroad(value1, value2, modifier)
        return type(ab)([-abs(e) for e in ab], -abs(ab.params[0]), -abs(ab.params[1]), ab.params[2])
    
    @classmethod
    def abroadPositiveFlip(cls, value1: _AbroadValue1[_T1], /, value2: _AbroadValue2[_T2] = None, modifier: _AbroadModifier[_T3] = None):
        """
        @lifetime >= 0.3.24 \\
        @modified 0.3.25 (moved slash to between `value1` and `value2`), 0.3.29, 0.3.52
        
        Every negative integer is coerced to positive, then sequence is reversed.
        """
        ab = abroad(value1, value2, modifier)
        return type(ab)([abs(e) for e in ab][::-1], abs(ab.params[1]) - 1, abs(ab.params[0]) - 1, ab.params[2])
    
    @classmethod
    def abroadNegativeFlip(cls, value1: _AbroadValue1[_T1], /, value2: _AbroadValue2[_T2] = None, modifier: _AbroadModifier[_T3] = None):
        """
        @lifetime >= 0.3.24 \\
        @modified 0.3.25 (moved slash to between `value1` and `value2`), 0.3.29, 0.3.52
        
        Every positive integer is coerced to negative, then sequence is reversed.
        """
        ab = abroad(value1, value2, modifier)
        return type(ab)([-abs(e) for e in ab][::-1], -abs(ab.params[1]) + 1, -abs(ab.params[0]) + 1, ab.params[2])
    
    @classmethod
    def abroadPack(cls, *values: _AbroadPackType[_T]):
        """
        @lifetime >= 0.3.25 \\
        @modified 0.3.29
        
        This variation of `abroad()` function bases on `zip()` Python function.
        """
        ab = abroad(reckonLeast(*values))
        return type(ab)([e for e in ab], ab.params[0], ab.params[1], ab.params[2])
    
    @classmethod
    def abroadExclude(cls, value1: _AbroadValue1[_T1], /, value2: _AbroadValue2[_T2] = None, modifier: _AbroadModifier[_T3] = None, *excludedIntegers: int):
        """
        @lifetime >= 0.3.25 \\
        @modified 0.3.29, 0.3.52
        
        This variation of `abroad()` function is the same as `abroad()` function,
        but it also allows to exclude specific integers from the returned list.
        If all are excluded, returned is empty integer list. If integers excluded
        do not exist in returned sequence normally, this issue is omitted, and a
        shallow copy of abroad object as a list is returned.
        """
        for e in excludedIntegers:
            
            if not cls.isInteger(e):
                error = TypeError("every item in parameter 'excludedIntegers' must be an integer")
                raise error
            
        return [e for e in abroad(value1, value2, modifier) if e not in excludedIntegers] # >= 0.3.52, return list
    
    @classmethod
    def abroadPrecede(cls, value1: _AbroadValue1[_T1], /, value2: _AbroadValue2[_T2] = None, modifier: _AbroadModifier[_T3] = None, prefix: _opt[str] = None):
        """
        @lifetime >= 0.3.25 \\
        @modified 0.3.29, 0.3.52
        
        This variation of `abroad()` function returns strings in a list. If `prefix` is `None`,
        returned are integers in strings, otherwise added is special string prefix before integers.
        """
        if prefix is not None and not isinstance(prefix, str):
            error = TypeError("expected parameter '{}' have string value".format(_get_all_params(cls.abroadPrecede)[-1]))
            raise error

        return [("" if prefix is None else prefix) + str(e) for e in abroad(value1, value2, modifier)] # >= 0.3.52; return list
            
    @classmethod
    def abroadSufcede(cls, value1: _AbroadValue1[_T1], /, value2: _AbroadValue2[_T2] = None, modifier: _AbroadModifier[_T3] = None, suffix: _opt[str] = None):
        """
        @lifetime >= 0.3.25 \\
        @modified 0.3.29, 0.3.52
        
        This variation of `abroad()` function returns strings in a list. If `suffix` is `None`,
        returned are integers in strings, otherwise added is special string suffix after integers.
        """
        if suffix is not None and not isinstance(suffix, str):
            error = TypeError("expected parameter '{}' have string value".format(_get_all_params(cls.abroadSufcede)[-1]))
            raise error

        return [str(e) + ("" if suffix is None else suffix) for e in abroad(value1, value2, modifier)] # >= 0.3.52; return list
    
    @classmethod
    def abroadInside(cls, value1: _AbroadValue1[_T1], /, value2: _AbroadValue2[_T2] = None, modifier: _AbroadModifier[_T3] = None, string: _opt[str] = None):
        """
        @lifetime >= 0.3.25 \\
        @modified 0.3.29, 0.3.52
        
        This variation of `abroad()` function returns strings in a list. If `string` is `None`,
        returned are integers in strings, otherwise integers are placed inside `{}` of the string.
        """
        if string is not None and not isinstance(string, str):
            error = TypeError("expected parameter '{}' have string value".format(_get_all_params(cls.abroadInside)[-1]))
            raise error

        ab = abroad(value1, value2, modifier)
        return [str(e) for e in ab] if string is None else [string.format(str(e)) for e in ab]
    
    @classmethod
    def abroadConvect(cls, *values: _AbroadConvectType[_Any]):
        """
        @lifetime >= 0.3.25
        
        Typical math sum operation before returned is list from `abroad()` function.
        If from values a value is:
        - an integer - added is this integer
        - a float - added is this number, without fraction
        - a complex - added are both real and imaginary parts
        - sizeable object - added is its length

        Note: it is possible to provide negative entities. If resulted number is negative,
        up to `abroad()` function, sequence will go in range `[values_sum, -1]`.
        Otherwise, it will take this form: `[0, values_sum - 1]`.
        """
        i = 0
        _params = _get_all_params(cls.abroadConvect)
        
        if reckon(values) == 0:
            error = exceptions.MissingValueError("expected at least one item in parameter '{}'".format(_params[-1]))
            raise error
        
        for e in values:
            
            if not isinstance(e, (_ReckonNGT, int, float, complex)):
                error = TypeError("from gamut of supported types, parameter '{}' has at least one unsupported type".format(_params[-1]))
                raise error
            
            elif isinstance(e, int):
                i += e
                
            elif isinstance(e, float):
                i += _math.trunc(e)
                
            elif isinstance(e, complex):
                i += _math.trunc(e.real) + _math.trunc(e.imag)
                
            else:
                i += reckon(e)
        return abroad(i)
    
    @classmethod
    def abroadFloaty(cls, value1: _AbroadValue1[_T1], /, value2: _AbroadValue2[_T2] = None, modifier: _AbroadModifier[_T3] = None, div: __.FloatOrInteger = 10):
        """
        @lifetime >= 0.3.25 \\
        @modified 0.3.29, 0.3.52
        
        Every item from `abroad()` function will be divided by parameter `div`. \\
        It's default value is `10`.
        """
        if not isinstance(div, (int, float)):
            error = TypeError(f"parameter 'div' is not an integer nor floating-point number. Ensure argument got value of type 'int' or 'float'. Received type: {type(div).__name__}")
            raise error
        
        elif isinstance(div, float) and div in (_math.nan, _math.inf):
            error = ValueError("parameter 'div' may not be infinity or not a number.")
            raise error
        
        elif (isinstance(div, int) and div == 0) or (isinstance(div, float) and div == .0):
            error = ZeroDivisionError("parameter 'div' may not be equal zero. This is attempt to divide by zero")
            raise error
        
        ab = abroad(value1, value2, modifier)
        return [e / div for e in ab]
    
    @classmethod
    def abroadSplit(cls, value1: _AbroadValue1[_T1], /, value2: _AbroadValue2[_T2] = None, modifier: _AbroadModifier[_T3] = None, limit = 2) -> _AbroadMultiInitializer:
        """
        @lifetime >= 0.3.25
        
        Reference to string slicing. Limit is amount of items, \\
        which can be in one sub-list. May not be equal or below 1.
        """
        lim = 0
        tmp, a = ([0], [[0]])
        cls.clear(a, tmp)
        
        if not isinstance(limit, int):
            error = TypeError(f"parameter 'limit' is not an integer. Ensure argument got integer value. Received type: {type(limit).__name__}")
            raise error
        
        elif limit < 1:
            error = ValueError("parameter 'limit' may not be negative, or have value 0 or 1. Start from 2.")
            raise error
        
        for i in abroad(value1, value2, modifier):
            
            if lim % limit == 0:
                a.append(tmp)
                tmp.clear()
                
            else:
                tmp.append(i)
                
            lim += 1
            
        return a
    
    @classmethod
    @__.overload
    def abroadEach(cls, value1: _AbroadValue1[_T1], /, value2: _AbroadValue2[_T2] = None, modifier: _AbroadModifier[_T3] = None, *, each: None = None) -> _AbroadEachInitializer[int]: ...
    
    @classmethod
    @__.overload
    def abroadEach(cls, value1: _AbroadValue1[_T1], /, value2: _AbroadValue2[_T2] = None, modifier: _AbroadModifier[_T3] = None, *, each: _cal[[int], _T]) -> _AbroadEachInitializer[_T]: ...
    
    @classmethod
    def abroadEach(cls, value1, /, value2 = None, modifier = None, *, each = None):
        """
        @lifetime >= 0.3.25 (experimental for 0.3.25 - 0.3.26b1)
        
        Invoked is `each` callback for every item in `abroad()` function.
        """
        
        if cls.versionInfo >= (0, 3, 44) or True:
            
            if not cls.isNone(each) and (not callable(each) or (callable(each) and reckon(_util.ParamVar(each).positional, _util.ParamVar(each).universal) != 1)):
                error = TypeError("expected 'None' or callable with one integer parameter not being keyword-only one")
                raise error
        
        else:
            
            if (not callable(each) and each is not None):
                error = TypeError("expected None or callable with one integer parameter")
                raise error
        
        # because TypeVars are objects themselves, we can pass an object list
        a = [0] if each is None else [object()]
        a.clear()
        
        for i in abroad(value1, value2, modifier):
            
            if each is None:
                a.append(i) # int
            
            else:
                a.append(each(i)) # object
        
        return a
    
    @classmethod
    def abroadHex(cls, value1: _AbroadValue1[_T1], /, value2: _AbroadValue2[_T2] = None, modifier: _AbroadModifier[_T3] = None, mode = ABROAD_HEX_INCLUDE):
        """
        @lifetime >= 0.3.25 (10.07.2024) \\
        @modified 0.3.52
        
        This variation of `abroad()` function returns hexadecimal representation of each integer.

        Modes (for 0.3.26rc2; to 0.3.27 support for integers):
        - `self.ABROAD_HEX_INCLUDE` - appends `0x` to each string. It faciliates casting to integer.
        - `self.ABROAD_HEX_INCLUDE_HASH` - appends `#` to each string. Reference from CSS.
        - `self.ABROAD_HEX_EXCLUDE` - nothing is appended.
        """
        a, ab = ([""], abroad(value1, value2, modifier))
        a.clear()
        
        for i in ab:
            
            if not isinstance(mode, _cl.AbroadHexMode):
                error = ValueError("expected a constant preceded with 'ABROAD_HEX_'")
                raise error
            
            elif mode == cls.ABROAD_HEX_INCLUDE:
                a.append(hex(i))
                
            elif mode == cls.ABROAD_HEX_HASH:
                a.append(_re.sub(r"^0x", "#", hex(i)))
                
            else:
                a.append(_re.sub(r"^0x", "", hex(i)))
        
        return a
    
    @classmethod
    def abroadBinary(cls, value1: _AbroadValue1[_T1], /, value2: _AbroadValue2[_T2] = None, modifier: _AbroadModifier[_T3] = None, include_0b = True):
        """
        @lifetime >= 0.3.25 \\
        @modified 0.3.52
        
        This variation of `abroad()` function returns binary representation of each integer.
        Parameter `include_0b` allows to append `0b` before binary notation, what allows
        to faciliate casting to integer. Defaults to `True`
        """
        a, ab = ([""], abroad(value1, value2, modifier))
        a.clear()
        
        for i in ab:
            
            if not isinstance(include_0b, bool):
                error = TypeError("expected parameter 'include_0b' to be of type 'bool'.")
                raise error
            
            elif include_0b:
                a.append(bin(i))
                
            else:
                a.append(_re.sub(r"^0b", "", bin(i)))
                
        return a
    
    @classmethod
    def abroadOctal(cls, value1: _AbroadValue1[_T1], /, value2: _AbroadValue2[_T2] = None, modifier: _AbroadModifier[_T3] = None):
        """
        @lifetime >= 0.3.25 \\
        @modified 0.3.52
        
        This variation of `abroad()` function returns octal representation of each integer.
        Every string will be preceded with `0o`
        """
        a, ab = ([""], abroad(value1, value2, modifier))
        a.clear()
        
        for i in ab:
            a.append(oct(i))
                
        return a
    
    @classmethod
    def architecture(cls, executable = _sys.executable, bits = "", linkage = ""):
        """
        @lifetime >= 0.3.26rc2 (0.3.27a5: added optional parameters)
        
        Returns system's architecture
        """
        return _architecture(executable, bits, linkage)
    
    @classmethod
    def disassemble(
        cls,
        x: __.Union[_HaveCodeType, str, bytes, bytearray, None] = None, # 0.3.62: missing type hint
        /,
        file: __.Optional[__.IO[str]] = None,
        depth: __.Optional[int] = None,
        showCaches = False,
        adaptive = False,
        showOffsets = False
    ):
        """
        @lifetime >= 0.3.26rc3
        
        Detach code of a class, type, function, methods and other compiled objects. \\
        If argument `x` is `None` (by default is `None`), disassembled is last traceback. \\
        See [`dis.dis()`](https://docs.python.org/3/library/dis.html#dis.dis) \\
        Modified 0.3.31: added missing parameter `showOffsets`
        """
        _dis.dis(x, file = file, depth = depth, show_caches = showCaches, adaptive = adaptive, show_offsets = showOffsets)
        return cls
    
    # changeover 0.3.42
    @classmethod
    def timeit(cls, statement: __.AVT_Callable[[], _Any], /):
        """
        @lifetime >= 0.3.26rc3 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.timeit
        
        A simplified version of [`timeit.timeit()`](https://docs.python.org/3/library/timeit.html#timeit.timeit).
        
        To invoke callable with arguments, use `lambda: <func-name>(...)`.
        """
        
        if not callable(statement) or util.ParamVar(statement).allCount != 0:
            
            error = TypeError("expected callable without any arguments")
            raise error
        
        c = _time.time()
        statement()
        return _time.time() - c
    
    if False: # < 0.3.55
        
        @classmethod
        def socket(cls, family: _uni[int, _socket.AddressFamily] = -1, type: _uni[int, _socket.SocketKind] = -1, proto = -1, fileno: _opt[int] = None):
            """
            @lifetime >= 0.3.27a2; < 0.3.55
            
            See [`socket.socket`](https://docs.python.org/3/library/socket.html#socket.socket)
            """
            return _socket.socket(family, type, proto, fileno)
    
    @classmethod
    def cast(cls, v: _Any, t: __.AVT_Type[_T], /) -> _T: 
        """
        @lifetime >= 0.3.36
        
        Casts a value to specific type, keeping its primal state after type casting.
        """
        
        return v
    
    @classmethod
    def generator(cls, i: __.Union[__.AVT_Iterable[_T], __.AVT_AsyncIterable[_T]], /, condition: __.AVT_Callable[[_T], bool] = ...):
        """
        @lifetime >= 0.3.50
        
        Creates a generator (before 0.3.53 with generator expression) using an iterable
        
        0.3.55: Asynchronous iterables are now allowed
        """
        
        if not isinstance(i, (__.Iterable, __.AsyncIterable)):
            error = TypeError("passed object isn't iterable")
            raise error
        
        if True: # >= 0.3.53
            
            if isinstance(i, __.AsyncIterable): # >= 0.3.55
                gen = _extract_from_async_iterable(i)
            
            else:
            
                def _gen_(iterable: __.AVT_Iterable[_T]):
                    
                    nonlocal condition
                    
                    if cls.isEllipsis(condition):
                        yield from iterable # see pep 380 (>=Py3.3)
                            
                    elif _is_bool_callback(condition):
                        yield from [e for e in iterable if condition(e)]
                                
                    else:
                        error = TypeError("expected ellipsis or callable object with one parameter only")
                        raise error
                    
                gen = _gen_(i)
                
            gen.__qualname__ = "<aveytense_generator>"
            return gen
            
        else:
            if cls.isEllipsis(condition):
                return (e for e in i)
            
            else:
                
                if _is_bool_callback(condition):
                    return (e for e in i if condition(e))
                
                else:
                    error = TypeError("expected one parameter only")
                    raise error
            
    @classmethod
    def asyncGenerator(cls, i: __.AVT_Iterable[_T], /, condition: __.AVT_Callable[[_T], bool] = ...):
        """
        @lifetime >= 0.3.53
        
        Creates an asynchronous generator using an iterable
        """
        
        if not isinstance(i, __.Iterable):
            error = TypeError("passed object isn't iterable")
            raise error
        
        async def _asyncgen_(iterable: __.AVT_Iterable[_T]):
            
            nonlocal condition
            
            if cls.isEllipsis(condition):
                for e in iterable: # pep 380 is not allowed in async functions
                    yield e
                    
            elif _is_bool_callback(condition):
                for e in iterable:
                    if condition(e):
                        yield e
                        
            else:
                error = TypeError("expected ellipsis or callable object with one parameter only")
                raise error
        
        asyncgen = _asyncgen_(i)
        asyncgen.__qualname__ = "<aveytense_async_generator>"
        return asyncgen
    
    # OVERLOAD 0.3.34
    
    if False: # utopic for now
        @classmethod
        @__.overload
        def shuffle(cls, v: __.IO[__.AnyStr]) -> __.IO[__.AnyStr]: ...
    
    @classmethod
    @__.overload
    def shuffle(cls, v: str) -> str: ...
    
    @classmethod
    @__.overload # >= 0.3.43
    def shuffle(cls, v: _util.MutableString) -> _util.MutableString: ...
    
    @classmethod
    @__.overload
    def shuffle(cls, v: _ab_mod.AbroadInitializer) -> __.AVT_List[int]: ...
    
    @classmethod
    @__.overload
    def shuffle(cls, v: __.TrueSequence[_T]) -> __.AVT_List[_T]: ...
    
    @classmethod
    @__.overload # >= 0.3.53
    def shuffle(cls, v: __.AVT_Generator[_T_yield_cov, _T_send_con, _T_return_cov]) -> __.AVT_Generator[_T_yield_cov, _T_send_con, _T_return_cov]: ...
    
    @classmethod
    @__.overload # >= 0.3.53
    def shuffle(cls, v: __.AVT_AsyncGenerator[_T_yield_cov, _T_send_con]) -> __.AVT_AsyncGenerator[_T_yield_cov, _T_send_con]: ...
    
    @classmethod
    @__.overload
    def shuffle(cls, v: __.AVT_Mapping[_KT, _VT]) -> __.AVT_Dict[_KT, _VT]: ...
    
    @classmethod
    def shuffle(cls, v):
        """
        @lifetime >= 0.3.26rc1 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.shuffle
        
        Shuffle a string, mapping or a sequence, and return shuffled iterable \\
        without changing passed iterable.
        """
        
        def _shuffle(x: __.AVT_Iterable[_T], /): # >= 0.3.42
            _placeholder = list(x)
            _random.shuffle(_placeholder)
            return _placeholder
            
        if cls.isString(v):
            _v = "".join(_shuffle(v))
            
        elif isinstance(v, _util.MutableString):
            _v = _util.MutableString("".join(_shuffle(v.value)))
            
        elif isinstance(v, _ab_mod.AbroadInitializer):
            _v = _shuffle(+v)
            
        # 0.3.53: Shuffle generators
        elif isinstance(v, __.Generator):
            _v = cls.generator(_shuffle(v))
            
        elif isinstance(v, __.AsyncGenerator):
            _v = cls.asyncGenerator(_shuffle(cls.generator(v)))
    
        elif isinstance(v, (__.Sequence, __.Uniqual)): # >= 0.3.55
            _v = _shuffle(v)
            
        elif isinstance(v, __.Mapping):
            _v = {k: v[k] for k in _shuffle([k for k in v])}
        
        else:
            error = TypeError("expected a string, mapping, sequence, set, generator, or result of abroad() function")
            raise error
            
        return _v
    
    # OVERLOAD 0.3.34
    
    if False:
        @classmethod
        @__.overload
        def reverse(cls, v: __.IO[__.AnyStr]) -> __.IO[__.AnyStr]: ...
    
    @classmethod
    @__.overload
    def reverse(cls, v: str) -> str: ...
    
    @classmethod
    @__.overload # >= 0.3.43
    def reverse(cls, v: _util.MutableString) -> _util.MutableString: ...
    
    @classmethod
    @__.overload
    def reverse(cls, v: _ab_mod.AbroadInitializer) -> __.AVT_List[int]: ...
    
    @classmethod
    @__.overload
    def reverse(cls, v: __.TrueSequence[_T]) -> __.AVT_List[_T]: ...
    
    @classmethod
    @__.overload # >= 0.3.53
    def reverse(cls, v: __.AVT_Generator[_T_yield_cov, _T_send_con, _T_return_cov]) -> __.AVT_Generator[_T_yield_cov, _T_send_con, _T_return_cov]: ...
    
    @classmethod
    @__.overload # >= 0.3.53
    def reverse(cls, v: __.AVT_AsyncGenerator[_T_yield_cov, _T_send_con]) -> __.AVT_AsyncGenerator[_T_yield_cov, _T_send_con]: ...
    
    @classmethod
    @__.overload
    def reverse(cls, v: __.AVT_Mapping[_KT, _VT]) -> __.AVT_Dict[_KT, _VT]: ...
    
    @classmethod
    @__.overload # >= 0.3.42
    def reverse(cls, v: __.AVT_Reversible[_T]) -> __.AVT_Iterator[_T]: ...
    
    @classmethod
    def reverse(cls, v):
        """
        @lifetime >= 0.3.26rc2 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.reverse
        
        Reverse a string, mapping or sequence, and return reversed iterable \\
        without changing passed iterable.
        """
        
        if cls.isString(v):
            _v = v[::-1]
            
        elif isinstance(v, _util.MutableString):
            
            # ~.util.MutableString.reverse() implemented on 0.3.45
            v.reverse()
            _v = _util.MutableString(v) # 0.3.45: allow instances of this class to the constructor
            v.reverse()
            
        elif isinstance(v, _ab_mod.AbroadInitializer):
            _v = (+v)[::-1]
            
        # 0.3.53: Reverse generators
        elif isinstance(v, __.Generator):
            _v = cls.generator(list(v)[::-1])
            
        elif isinstance(v, __.AsyncGenerator):
            _v = cls.asyncGenerator(list(cls.generator(v))[::-1])
        
        elif isinstance(v, __.Uniqual): # >= 0.3.42
           _v = list(v)[::-1]
        
        elif isinstance(v, __.Sequence):
            _v = list(v)[::-1]
        
        # 'dict' objects normally do not include the 'reverse' method
        elif isinstance(v, __.Mapping):
            _v = {k: v[k] for k in [k2 for k2 in v][::-1]}
        
        elif isinstance(v, __.Reversible): #>= 0.3.42
            return reversed(v)
            
        else:
            error = TypeError("expected a string, mapping, sequence, set, generator, or result of abroad() function")
            raise error
        
        return _v
    
    if False:
        @classmethod
        @__.overload
        def append(cls, i: __.IO[__.AnyStr], /, *items: str) -> __.IO[__.AnyStr]: ...
    
    @classmethod
    @__.overload # >= 0.3.46
    def append(cls, i: __.AVT_Mapping[_KT1, _VT1], /, *items: __.AVT_Tuple[_KT2, _VT2]) -> __.AVT_Dict[__.Union[_KT1, _KT2], __.Union[_VT1, _VT2]]: ...
    
    @classmethod
    @__.overload # >= 0.3.55a1
    def append(cls, i: __.AVT_Generator[_T_yield_cov, _T_send_con, _T_return_cov], /, *items: _T) -> __.AVT_Generator[__.Union[_T_yield_cov, _T], _T_send_con, _T_return_cov]: ...
    
    @classmethod
    @__.overload # >= 0.3.55a1
    def append(cls, i: __.AVT_AsyncGenerator[_T_yield_cov, _T_send_con], /, *items: _T) -> __.AVT_AsyncGenerator[__.Union[_T_yield_cov, _T], _T_send_con]: ...
    
    @classmethod
    @__.overload
    def append(cls, i: __.AVT_Iterable[_T1], /, *items: _T2) -> __.AVT_List[__.Union[_T1, _T2]]: ...
    
    @classmethod
    def append(cls, i, /, *items):
        """
        @lifetime >= 0.3.27a4 \\
        @standard-lifetime >= 0.3.39 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.append
        
        Same as `list.append()`, just variable amount of items can be passed. \\
        Input list remains non-modified, and returned is its modified copy.
        
        Since 0.3.34, because mutable sequences are normally coerced to list, allowed are also \\
        all other iterables
        
        Since 0.3.46 mappings are allowed; `items` may only contain 2-item tuples in this case
        
        Since 0.3.55a1 generators and asynchronous generators return themselves.
        """
        
        if isinstance(i, __.Mapping) and cls.all(items, lambda x: cls.isTuple(x) and reckon(x) == 2):
                
            return dict([(k, i[k]) for k in i] + list(items))
        
        elif isinstance(i, __.Generator):
            
            def _gen_(*iterables):
                
                nonlocal i
                
                yield from i
                yield from iterables
            
            gen = _gen_(*items)
            gen.__qualname__ = "<aveytense_generator>"
            return gen
        
        elif isinstance(i, __.AsyncGenerator):
            
            async def _asyncgen_(*iterables):
                
                nonlocal i
                
                async for e in i:
                    yield e
                for e in iterables:
                    yield e
                    
            asyncgen = _asyncgen_(*items)
            asyncgen.__qualname__ = "<aveytense_async_generator>"
            return asyncgen
        
        elif isinstance(i, __.Iterable):
            
            return list(i) + list(items)
        
        else:
            
            error = TypeError("expected a mapping + 2-item tuples or iterable objects")
            raise error
    
    if False:
        @classmethod
        @__.overload
        def extend(cls, i: __.IO[__.AnyStr], /, *iters: __.AVT_Iterable[str]) -> __.IO[__.AnyStr]: ...
    
    @classmethod
    @__.overload # >= 0.3.46
    def extend(cls, i: __.AVT_Mapping[_KT1, _VT1], /, *iters: __.AVT_Mapping[_KT2, _VT2]) -> __.AVT_Dict[_uni[_KT1, _KT2], _uni[_VT1, _VT2]]: ...
    
    @classmethod
    @__.overload # >= 0.3.55a2
    def extend(cls, i: __.AVT_Generator[_T_yield_cov, _T_send_con, _T_return_cov], /, *iters: __.Union[__.AVT_Iterable[_T], __.AVT_AsyncIterable[_T]]) -> __.AVT_Generator[_uni[_T_yield_cov, _T], _T_send_con, _T_return_cov]: ...
    
    @classmethod
    @__.overload # >= 0.3.55a2
    def extend(cls, i: __.AVT_AsyncGenerator[_T_yield_cov, _T_send_con], /, *iters: __.Union[__.AVT_Iterable[_T], __.AVT_AsyncIterable[_T]]) -> __.AVT_AsyncGenerator[_uni[_T_yield_cov, _T], _T_send_con]: ...
    
    @classmethod
    @__.overload
    def extend(cls, i: __.AVT_Iterable[_T1], /, *iters: __.AVT_Iterable[_T2]) -> __.AVT_List[_uni[_T1, _T2]]: ...
    
    @classmethod
    def extend(cls, i, /, *iters):
        """
        @lifetime >= 0.3.27a4 \\
        @standard-lifetime >= 0.3.39 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.extend
        
        Same as `list.extend()`, just variable amount of iterables can be passed. \\
        Input list remains non-modified, and returned is its modified copy.
        
        Since 0.3.34, because mutable sequences are normally coerced to list, allowed are also \\
        all other iterables
        
        Since 0.3.46 mappings are allowed; in this case all items in `iters` must be mappings too.
        
        Since 0.3.55a2 generator returns a generator, and so does its asynchronous equivalent.
        """
        
        if isinstance(i, __.Mapping) and cls.isTuple(iters, __.Mapping):
                
            return dict([(k, i[k]) for k in i] + [(k, e[k]) for e in iters for k in e])
        
        elif isinstance(i, __.Generator) and cls.isTuple(iters, (__.AsyncIterable, __.Iterable)):
            
            return cls.flatten([list(i)] + [cls.toList(e) for e in iters])
        
        elif isinstance(i, __.AsyncGenerator) and cls.isTuple(iters, (__.AsyncIterable, __.Iterable)):
            
            return cls.asyncGenerator(cls.flatten([list(i)] + [cls.toList(e) for e in iters]))
        
        elif isinstance(i, __.Iterable) and cls.isTuple(iters, __.Iterable):
            
            return list(i) + [e for iterable in iters for e in iterable]
        
        else:
            
            error = TypeError("expected mapping objects only, generator/async generator object + iterable/async iterable objects, or iterable objects only")
            raise error
    
    # OVERLOAD 0.3.34
    @classmethod
    @__.overload
    def occurrences(cls, v: str, *items: str, mode: _lit["case_sensitive"] = "case_sensitive") -> int: ...
    
    @classmethod
    @__.overload
    def occurrences(cls, v: str, *items: str, mode: _lit["case_insensitive"]) -> int: ...
    
    @classmethod
    @__.overload
    def occurrences(cls, v: _ab_mod.AbroadInitializer, *items: int, mode: _lit["normal"] = "normal") -> int: ...
    
    @classmethod
    @__.overload
    def occurrences(cls, v: _ab_mod.AbroadInitializer, *items: int, mode: _lit["absolute"]) -> int: ...
    
    @classmethod
    @__.overload
    def occurrences(cls, v: _uni[__.AVT_Sequence[_T], __.AVT_Uniqual[_T]], *items: _T) -> int: ...
    
    @classmethod
    @__.overload
    def occurrences(cls, v: __.AVT_Mapping[_KT, _VT], *items: _KT, mode: _lit["key"] = "key") -> int: ...
    
    @classmethod
    @__.overload
    def occurrences(cls, v: __.AVT_Mapping[_KT, _VT], *items: _VT, mode: _lit["value"]) -> int: ...
    
    @classmethod
    def occurrences(cls, v, *items, mode = "case_sensitive"):
        """
        @lifetime >= 0.3.32 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.occurrences
        
        Returns number of how many times specified item appears \\
        or items appear in a sequence
        """
        
        o = 0
        m = mode.lower()
        
        if not cls.isString(mode):
            
            error = TypeError("parameter 'mode' is not a string")
            raise error
        
        if m not in ("case_sensitive", "case_insensitive", "normal", "absolute", "key", "value"):
            
            error = ValueError("parameter 'mode' provides invalid mode")
            raise error
        
        if isinstance(v, (str, _ab_mod.AbroadInitializer, __.Sequence, __.Uniqual, __.Mapping)) and reckon(v) == 0:
            return 0
        
        if cls.isString(v):
            
            if m not in ("case_sensitive", "case_insensitive"):
                
                error = ValueError("for strings parameter 'mode' can take one of 2 modes: 'case_sensitive' and 'case_insensitive'")
                raise error
            
            
            _v = v.split()
            _s = list(items)
            
            if not cls.isList(_s, str):
                
                error = ValueError("parameter 'items' doesn't utterly consist of string items")
                raise error
            
            if m == "case_insensitive":
                _s = [cls.cast(s, str).lower() for s in items]
                
            for s in _v:
                
                if (s in _s and m == "case_sensitive") or (s.lower() in _s and m == "case_insensitive"):
                    o += 1
                    
            return o
                    
        elif isinstance(v, _ab_mod.AbroadInitializer):
            
            if m not in ("normal", "absolute"):
                
                error = ValueError("for instances of internal class being result of abroad() function ({} class objects), parameter 'mode' can take one of 2 modes: 'normal' and 'absolute'".format(_ab_mod.AbroadInitializer.__name__))
                raise error
            
            _i = list(items)
            
            if not cls.isList(_i, int):
                
                error = ValueError("parameter 'items' doesn't utterly consist of integer items")
                raise error
            
            if m == "absolute":
                _i = [abs(i) for i in items]
                
                
            for i in v:
                
                if (i in _i and m == "normal") or (abs(i) in _i and m == "absolute"):
                    o += 1
                    
            return o
                    
        elif isinstance(v, (__.Sequence, __.Uniqual)):
            
            _v = list(v)
            
            for e in _v:
                
                if e in items:
                    o += 1
                    
            return o
                    
        elif isinstance(v, __.Mapping):
            
            if m not in ("key", "value"):
                
                error = ValueError("for mappings parameter 'mode' can take one of 2 modes: 'key' and 'value'")
                raise error
            
            if m == "key":
                _v = list(v.keys())
                
            else:
                _v = list(v.values())
                
            for e in _v:
                
                if e in items:
                    o += 1
                    
            return o
            
        else:
            error = TypeError("expected a string, mapping, sequence or result of abroad() function")
            raise error
                    
    # OVERLOAD 0.3.34
    @classmethod
    @__.overload
    def difference(cls, v1: __.AVT_Type[_T1], v2: __.AVT_Type[_T2], /, invert: bool = False, value_check: bool = True) -> __.AVT_List[str]: ...
    
    @classmethod
    @__.overload
    def difference(cls, v1: __.AVT_Type[_T1], v2: __.AVT_Mapping[str, _T2], /, invert: bool = False, value_check: bool = True) -> __.AVT_List[str]: ...
    
    @classmethod
    @__.overload
    def difference(cls, v1: __.AVT_Mapping[str, _T1], v2: type[_T2], /, invert: bool = False, value_check: bool = True) -> __.AVT_List[str]: ...
    
    @classmethod
    @__.overload
    def difference(cls, v1: __.AVT_Mapping[_KT1, _VT1], v2: __.AVT_Mapping[_KT2, _VT2], /, invert: _lit[False] = False, value_check: bool = True) -> __.AVT_List[_KT1]: ...
    
    @classmethod
    @__.overload
    def difference(cls, v1: __.AVT_Mapping[_KT1, _VT1], v2: __.AVT_Mapping[_KT2, _VT2], /, invert: _lit[True], value_check: bool = True) -> __.AVT_List[_KT2]: ...
    
    @classmethod
    @__.overload
    def difference(cls, v1: __.AVT_Type[_T], v2: _uni[__.Sequence[str], __.Uniqual[str]], /, invert: bool = False, value_check: bool = True) -> __.AVT_List[str]: ...
    
    @classmethod
    @__.overload
    def difference(cls, v1: _uni[__.Sequence[str], __.Uniqual[str]], v2: __.AVT_Type[_T], /, invert: bool = False, value_check: bool = True) -> __.AVT_List[str]: ...
    
    @classmethod
    @__.overload
    def difference(cls, v1: _ab_mod.AbroadInitializer, v2: _uni[__.Sequence[int], __.Uniqual[int]], /, invert: bool = False) -> __.AVT_List[int]: ...
    
    @classmethod
    @__.overload
    def difference(cls, v1: _uni[__.Sequence[int], __.Uniqual[int]], v2: _ab_mod.AbroadInitializer, /, invert: bool = False) -> __.AVT_List[int]: ...
    
    @classmethod
    @__.overload
    def difference(cls, v1: _ab_mod.AbroadInitializer, v2: _ab_mod.AbroadInitializer, /, invert: bool = False) -> __.AVT_List[int]: ...
    
    @classmethod
    @__.overload
    def difference(cls, v1: _uni[__.Sequence[_T1], __.Uniqual[_T1]], v2: _uni[__.Sequence[_T2], __.Uniqual[_T2]], /, invert: _lit[False] = False) -> __.AVT_List[_T1]: ...
    
    @classmethod
    @__.overload
    def difference(cls, v1: _uni[__.Sequence[_T1], __.Uniqual[_T1]], v2: _uni[__.Sequence[_T2], __.Uniqual[_T2]], /, invert: _lit[True]) -> __.AVT_List[_T2]: ...
    
    @classmethod
    def difference(cls, v1, v2, /, invert = False, value_check = True):
        """
        @lifetime >= 0.3.32
        
        Find items, which belong to `v1`, but do not belong to `v2` (math difference `v1 \\ v2`). \\
        With `invert` being `True` it is vice versa (`v2 \\ v1`).
        
        When `value_check` is `True`, values from fields in classes or dictionairies will be also checked. \\
        In this case when values are different, then they are included in the returned list.
        
        For class fields with roundly underscored names, these fields aren't counted.
        """
        _v1, _v2 = [{} for _ in abroad(2)]
        
        if isinstance(v1, type):
            
            if isinstance(v2, type):
                
                _v1 = {k: v1.__annotations__[k] for k in v1.__annotations__ if k[:1] != "_"}
                _v2 = {k: v2.__annotations__[k] for k in v2.__annotations__ if k[:1] != "_"}
            
            elif isinstance(v2, __.Mapping):
                
                if not cls.isList([k for k in v2], str):
                    
                    error = ValueError("with comparison with a class expected a string-key-typed mapping")
                    raise error
                
                _v1 = {k: v1.__annotations__[k] for k in v1.__annotations__ if k[:1] != "_"}
                _v2 = {k: v2[k] for k in v2 if k[:1] != "_"}
            
            elif isinstance(v2, (__.Sequence, __.Uniqual)):
                
                if not cls.isList([k for k in v2], str):
                    
                    error = ValueError("with comparison with a class expected a string-typed sequence")
                    raise error
                
                _v1 = [k for k in v1.__annotations__]
                _v2 = list(v2)
                
            else:
                error = TypeError("with comparison with a class expected another class or string sequence, mapping with string keys")
                raise error
        
        elif isinstance(v1, __.Mapping):
            
            if isinstance(v2, type):
                
                if not cls.isList([k for k in v1], str):
                    
                    error = ValueError("with comparison with a class expected a string-key-typed mapping")
                    raise error
                
                _v1 = {k: v1[k] for k in v1 if k[:1] != "_"}
                _v2 = {k: v2.__annotations__[k] for k in v2.__annotations__ if k[:1] != "_"}
                
            elif isinstance(v2, __.Mapping):
                
                _v1 = {k: v1[k] for k in v1 if k[:1] != "_"}
                _v2 = {k: v2[k] for k in v2 if k[:1] != "_"}
                
            else:
                error = TypeError("with comparison with a mapping expected another mapping or a class")
                raise error
        
        elif isinstance(v1, _ab_mod.AbroadInitializer):
            
            if isinstance(v2, _ab_mod.AbroadInitializer):
                
                _v1 = +v1
                _v2 = +v2
                
                if invert:
                    return [e for e in _v1 if e not in _v2]
                
                else:
                    return [e for e in _v2 if e not in _v1]
                
            elif isinstance(v2, (__.Sequence, __.Uniqual)):
                
                if not cls.isList([e for e in v2], int):
                    
                    error = ValueError("with comparison with a result from abroad() function expected an integer sequence")
                    raise error
                
                _v1 = +v1
                _v2 = list(v2)
                
            else:
                error = TypeError("with comparison with a result from abroad() function expected another abroad() function result or integer sequence")
                raise error
            
        elif isinstance(v1, (__.Sequence, __.Uniqual)):
            
            if isinstance(v2, type):
                
                if not cls.isList([k for k in v1], str):
                    
                    error = ValueError("with comparison with a class expected a string-typed sequence")
                    raise error
                
                _v1 = list(v1)
                _v2 = [k for k in v2.__annotations__]
                
            elif isinstance(v2, _ab_mod.AbroadInitializer):
                
                if not cls.isList([e for e in v2], int):
                    
                    error = ValueError("with comparison with a result from abroad() function expected an integer sequence")
                    raise error
                
                _v1 = list(v1)
                _v2 = +v2
                
            elif isinstance(v2, (__.Sequence, __.Uniqual)):
                
                _v1 = list(v1)
                _v2 = list(v2)
                
        if invert:
            _v1, _v2 = _v2, _v1
            
        _res = [k for k in _v1 if k not in _v2]
        
        if value_check and isinstance(_v1, dict) and isinstance(_v2, dict):
            
            for k in _v1:
                
                if k in _v2 and _v1[k] != _v2[k]:
                    _res.append(k)
        
        _res.sort()
        return _res
    
    # OVERLOAD 0.3.34
    @classmethod
    @__.overload
    def intersection(cls, v: int, /, *_: int) -> int: ...
    
    @classmethod
    @__.overload
    def intersection(cls, v: bool, /, *_: bool) -> bool: ...
    
    @classmethod
    @__.overload
    def intersection(cls, v: __.AVT_Iterable[_T], /, *_: __.AVT_Iterable[_Any]) -> __.AVT_List[_T]: ...
                        
    @classmethod
    def intersection(cls, v, /, *_):
        """
        @lifetime >= 0.3.34
        
        Returns list of items, which appear in all sequences (math intersection `v1 \u2229 v2 \u2229 ... \u2229 vN`). \\
        In case of integers returned is bitwise AND (`&`) taken on all integers. \\
        In case of boolean values returned is logical AND (`and`) taken on all boolean values.
        """
        if isinstance(v, bool):
            
            if reckon(_) == 0:
                return v
            
            else:
                
                if not cls.isList([e for e in _], bool):
                    
                    error = ValueError("expected every value a boolean value")
                    raise error
                
                _v = v
                
                for e in _:
                    _v = _v and e
                    
                return _v
        
        elif isinstance(v, int):
            
            if reckon(_) == 0:
                return v
            
            else:
                
                if not cls.isList([e for e in _], int):
                    
                    error = ValueError("expected every value an integer")
                    raise error
                
                _v = v
                
                for e in _:
                    _v &= e
                    
                return _v
            
        elif isinstance(v, __.Iterable):
            
            if reckon(_) == 0:
                return list(v)
            
            else:
                
                _pre = list(_)
                
                if _sys.version_info >= (3, 9):
                    _checkery = bool(cls.isList(_pre, __.Iterable))
                    
                else:
                    _checkery = cls.all(_pre, lambda x: issubclass(type(x), __.Iterable))
                
                if not _checkery:
                    
                    error = ValueError("expected every value an iterable")
                    raise error
                
                return list(set(v).intersection(*_))
            
        else:
            error = TypeError("expected every value either integers, boolean values or iterable objects")
            raise error
    
    # OVERLOAD 0.3.34
    @classmethod
    @__.overload
    def union(cls, v: int, /, *_: int) -> int: ...
    
    @classmethod
    @__.overload
    def union(cls, v: bool, /, *_: bool) -> bool: ...
    
    @classmethod
    @__.overload
    def union(cls, v: __.AVT_Iterable[_T1], /, *_: __.AVT_Iterable[_T2]) -> __.AVT_List[_uni[_T1, _T2]]: ...
    
    @classmethod
    @__.overload # >= 0.3.61; type hint fixed in 0.3.62
    def union(cls, v: __.AVT_Type[_T], /, *_: __.AVT_Type[_T]) -> __.AVT_Type[_T]: ...
    
    @classmethod
    def union(cls, v, /, *_: _Any):
        """
        @lifetime >= 0.3.34
        
        Returns list of items, which appear in any sequences (math union `v1 \u222A v2 \u222A ... \u222A vN`). \\
        In case of integers returned is bitwise OR (`|`) taken on all integers. \\
        In case of boolean values returned is logical OR (`or`) taken on all boolean values.
        
        0.3.61: In case of types, returned is union type
        """
        
        if isinstance(v, (type, _GenericTypes, _UnionTypes, bool, int)) and reckon(_) == 0:
            return v
        
        if isinstance(v, (type, _GenericTypes, _UnionTypes)): # >= 0.3.61
            
            if not cls.all(_, lambda x: isinstance(x, (type, _GenericTypes, _UnionTypes))):
                error = TypeError("expected types only")
                raise error
            
            if _sys.version_info >= (3, 10): # extract from _prepare_union_() internal function from Tense.getGeneric()
                    
                _union_: __.UnionType = v
                for e in _: _union_ = _union_ | e
                return _union_
                
            else:
                
                # typing.Union[*v] throws SyntaxError before Python 3.10, use eval() instead
                return cls.cast(extensions.eval("__.Union[{}]".format(", ".join([t.__qualname__ for t in (v, *_)])), globals = globals()), __.TypingUnionType)
        
        if isinstance(v, bool):
                
            if not cls.isTuple(_, bool):
                
                error = ValueError("expected every value a boolean value")
                raise error
            
            _v = v
            
            for e in _:
                _v = _v or e
                
            return _v
        
        elif isinstance(v, int):
            
            if not cls.isList([e for e in _], int):
                
                error = ValueError("expected every value an integer")
                raise error
            
            _v = v
            
            for e in _:
                _v |= e
                
            return _v
            
        elif cls.isIterable(v):
            
            if reckon(_) == 0:
                return list(v)
            
            else:
                
                _pre = list(_)
                
                if _sys.version_info >= (3, 9):
                    _checkery = bool(cls.isList(_pre, __.Iterable))
                    
                else:
                    _checkery = cls.all(_pre, lambda x: issubclass(type(x), __.Iterable))
                
                if not _checkery:
                    
                    error = ValueError("expected every value an iterable")
                    raise error
                
                return list(set(v).union(*_))
            
        else:
            error = TypeError("expected every value either integers, boolean values or iterable objects")
            raise error
    
    @classmethod
    @__.overload
    def exclude(cls, i: __.AVT_Mapping[_KT, _VT], /, *items: _KT, filter: __.Literal["keys"] = "keys") -> __.AVT_Dict[_KT, _VT]: ...
        
    @classmethod
    @__.overload
    def exclude(cls, i: __.AVT_Mapping[_KT, _VT], /, *items: _VT, filter: __.Literal["values"]) -> __.AVT_Dict[_KT, _VT]: ...
    
    @classmethod
    @__.overload
    def exclude(cls, i: __.AVT_Iterable[_T], /, *items: _T) -> __.AVT_List[_T]: ...
    
    @classmethod
    def exclude(cls, i, /, *items, filter = "keys"):
        """
        @lifetime >= 0.3.34 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.exclude
        
        Return a new list from iterable without items specified.
        
        Since 0.3.46 mappings are allowed. Keyword-only parameter `filter` *only* take place for mappings, \\
        and can only contain case-sensitive string values: `"keys"` or `"values"`
        """
        
        # 0.3.46
        if isinstance(i, __.Mapping):
            
            if filter == "keys":
                return dict([(k, i[k]) for k in i if k not in items])
            
            elif filter == "values":
                return dict([(k, i[k]) for k in i if i[k] not in items])
            
            else:
                error = TypeError("invalid value for 'filter' parameter, expected either 'keys' or 'values' (case sensitive)")
                raise error
            
        elif cls.isIterable(i):
            
            return [e for e in i if e not in items]
        
        else:
            
            error = TypeError("expected a mapping or an iterable")
            raise error
            
    @classmethod
    @__.overload
    def extract(cls, i: __.AVT_Mapping[_KT, _VT], /, condition: __.AVT_Callable[[_KT], bool] = ...) -> __.AVT_Dict[_KT, _VT]: ...
        
    @classmethod
    @__.overload
    def extract(cls, i: __.AVT_Mapping[_KT, _VT], /, condition: __.AVT_Callable[[_KT, _VT], bool]) -> __.AVT_Dict[_KT, _VT]: ...
    
    @classmethod
    @__.overload
    def extract(cls, i: __.AVT_Iterable[_T], /, condition: __.AVT_Callable[[_T], bool] = ...) -> __.AVT_List[_T]: ...
        
    @classmethod
    def extract(cls, i, /, condition = ...):
        """
        @lifetime >= 0.3.52
        
        Extracts items from a mapping or iterable which satisfy given `condition`, and returns them in a dictionary or list.
        If no condition given, returns shallow copy of given iterable/mapping as a list/dictionary.
        
        This class method is almost the same as `aveytense.Tense.expect()`, just a new copy of an iterable/mapping is returned,
        and there is no quantity specifier `m`.
        """
        
        if isinstance(i, __.Mapping):
            
            if cls.isEllipsis(condition) or reckon(i) == 0:
                return dict(i)
            
            elif cls.isLambda(condition):
                p = util.ParamVar(condition)
                key, value = list(i.keys())[0], list(i.values())[0]
                
                if p.positionalCount + p.universalCount == p.allCount == 1:
                    
                    if not isinstance(condition(key), bool):
                        error = TypeError("callable object as the condition must return a boolean value")
                        raise error
                    
                    return dict([(k, i[k]) for k in i if condition(k)])
                
                elif p.positionalCount + p.universalCount == p.allCount == 2:
                    
                    if not isinstance(condition(key, value), bool):
                        error = TypeError("callable object as the condition must return a boolean value")
                        raise error
                    
                    return dict([(k, i[k]) for k in i if condition(k, i[k])])
                
                else:
                    error = TypeError("expected one or two parameter in a lambda expression")
                    raise error
                
            else:
                error = TypeError("expected a callable object")
                raise error
            
        elif cls.isIterable(i):
            
            if cls.isEllipsis(condition) or reckon(i) == 0:
                return list(i)
            
            elif cls.isLambda(condition):
                p = util.ParamVar(condition)
                e = list(i)[0]
                
                if isinstance(condition(e), bool) and p.positionalCount + p.universalCount == p.allCount == 1:
                    return list([elem for elem in i if condition(elem)])
                
                else:
                    error = TypeError("expected callable object as the condition with one parameter")
                    raise error
            
            else:
                error = TypeError("expected callable object")
                raise error
            
        else:
            error = TypeError("expected a mapping or iterable")
            raise error
    
    @classmethod
    def explode(cls, s: str, /, separator: _opt[str] = None, max = -1, noEmpty = False):
        """
        @lifetime >= 0.3.34
        
        Reference from PHP inbuilt function `explode()`. Split a string \\
        using specified separator into a string list.
        """
        _params = _get_all_params(cls.explode)
        
        # error message template
        _msgtmpl = "expected {} in parameter '{}'"
        
        _msg = ["" for _ in abroad(_params)]
        _msg[0] = _msgtmpl.format("a string", _params[0])
        _msg[1] = _msgtmpl.format("a string or None", _params[1])
        _msg[2] = _msgtmpl.format("an integer for -1 above (not being zero)", _params[2])
        
        if not cls.isString(s):
            error = TypeError(_msg[0])
            raise error
        
        if not cls.isString(separator) and not cls.isNone(separator):
            error = TypeError(_msg[1])
            raise error
        
        if not cls.isInteger(max) or (cls.isInteger(max) and max != -1 and max < 1):
            error = TypeError(_msg[2])
            raise error
        
        if noEmpty: 
            return [k for k in s.split(separator, max) if reckon(k) != 0]
        
        return s.split(separator, max)
    
    @classmethod
    @__.overload
    def removePrefix(cls, s: str, prefix: str, /) -> str: ...
    
    @classmethod
    @__.overload
    def removePrefix(cls, b: bytes, prefix: __.ReadableBuffer, /) -> bytes: ...
    
    @classmethod
    @__.overload
    def removePrefix(cls, b: bytearray, prefix: __.ReadableBuffer, /) -> bytearray: ...
    
    @classmethod
    def removePrefix(cls, v, prefix, /):
        """
        @lifetime >= 0.3.53
        
        Re-implement PEP 616 (implemented in Python 3.9)
        
        Return copy of string or bytes object if prefix was not found,
        otherwise return copy without specific prefix.
        
        Since 0.3.60 `bytearray` objects are supported.
        """
        
        if cls.isString(v) and cls.isString(prefix):
            return extensions.str_removeprefix(v, prefix)
        elif isinstance(v, (bytes, bytearray)) and isinstance(prefix, __.ReadableBuffer):
            return extensions.bt_removeprefix(v, prefix)
        else:
            error = TypeError("expected 'str' + 'str' or 'bytes/bytearray' + 'bytes-like'")
            raise error
        
    @classmethod
    @__.overload
    def removeSuffix(cls, s: str, suffix: str, /) -> str: ...
    
    @classmethod
    @__.overload
    def removeSuffix(cls, b: bytes, suffix: __.ReadableBuffer, /) -> bytes: ...
    
    @classmethod
    @__.overload
    def removeSuffix(cls, b: bytearray, suffix: __.ReadableBuffer, /) -> bytearray: ...
    
    @classmethod
    def removeSuffix(cls, v, suffix, /):
        """
        @lifetime >= 0.3.53
        
        Re-implement PEP 616 (implemented in Python 3.9)
        
        Return copy of string or bytes object if suffix was not found,
        otherwise return copy without specific suffix.
        
        Since 0.3.60 `bytearray` objects are supported.
        """
        
        if cls.isString(v) and cls.isString(suffix):
            return extensions.str_removesuffix(v, suffix)
        elif isinstance(v, (bytes, bytearray)) and isinstance(suffix, __.ReadableBuffer):
            return extensions.bt_removesuffix(v, suffix)
        else:
            error = TypeError("expected 'str' + 'str' or 'bytes/bytearray' + 'bytes-like'")
            raise error

    @classmethod # below: append 'typing.IO[Any]' when tests are done on 0.3.48
    def clear(cls, *v: _Clearable): # 0.3.27a4
        """
        @lifetime >= 0.3.27a4 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.clear
        
        Same as `[list/set/dict].clear()`, just variable amount of lists/sets/dictionaries can be passed. \\
        This type list includes strings and instances of `types.FrameType`.
        
        Supported types (since: + type):
        - originally - mutable sequences
        - 0.3.27b1 - strings
        - 0.3.36 - mutable sets
        - 0.3.37 - mutable dictionaries and instances of `~.Color`
        - 0.3.40 - instances of `types.FrameType` (and fixed strings)
        - 0.3.42 - any objects of classes implementing `clear()` with no arguments, \\
            and instances of `~.util.MutableString`
        - 0.3.50 - file objects
        """
        
        # This doesn't seem as a secure idea, but had to do it since strings are immutable
        # and on this method they are here to be cleared. Only way to clear the string
        # is getting the variable passed to the parameter, which is a string. Basically this
        # is a technique without 'varname' PyPi project.
        
        # Answer is from Stack Overflow https://stackoverflow.com/a/18425523, only revamped it
        # so it can apply to arbitrary amount of arguments. F-string won't work there, as it
        # would be f"{n=}".split("=")[0], referring to 'n', not to any passed variables.
        # 24.02.2025
        
        _frame = _inspect.currentframe().f_back.f_locals
        _getvars = {name: val for name, val in _frame.items() if val in v and cls.isString(val)}
            
        # We are assuming variables are defined and won't require pre-definition.
        # If it happened, then we would need to put another exec() invocation in
        # a loop, just as:
        #
        # for n, _v in _getvars.items():
        #     exec("{} = \"{}\"".format(n, _v), _frame)
        
        # If string was a literal, then deduced string will not be empty, original string value will
        # be kept (if we mention typing), but in reality string is cleared. Alternatively, you can do
        # something like this: a1, a2, a3 = ["" for _ in range(3)]
        # 10.03.2025
        
        for e in _getvars:
            exec("{} = \"\"".format(e), _frame)
        
        for _v in v:
            
            # Code below will work for literal strings only, but it is not advisable.
            # We can also omit string type checking (in case of literals nothing really
            # occurs, so in this case 'pass' may be used)
            
            if cls.isString(_v):
                
                if reckon(_v) > 0:
                    _v = ""
                
            else:
                
                # ~.Color (pre-defined; class overall)
                if isinstance(_v, Color):
                    _v.clear()
                
                # Lists, sets, dictionaries, ... Just with one invocation
                elif isinstance(_v, (
                    
                    __.MutableSequence,
                    __.MutableUniqual,
                    __.MutableMapping,
                    _util.MutableString,
                    __.FrameType
                    
                )):
                    
                    _v.clear()
                
                # 0.3.50
                elif isinstance(_v, __.IO): 
                    
                    _name_ = _v.name
                    
                    if not _v.closed:
                        _v.close()
                    
                    open(_name_, "w").close()
                
                # 0.3.42
                elif isinstance(_v, _ClearableAbc) or (hasattr(_v, "clear") and callable(_v.clear)):
                    
                    _clear = cls.cast(_v.clear, __.FunctionType)
                    p = util.ParamVar(_clear)
                    
                    if p.allCount == 0:
                        
                        _clear()
                    
                else:
                    error = ValueError("expected a mutable sequence, mutable mapping, instance of 'types.FrameType', 'aveytense.util.MutableString' or 'aveytense.Color', or a string")
                    raise error
                
    @classmethod
    def tryOrPass(cls, f: __.AVT_Callable[[], _Any], /, exc: __.Union[__.AVT_Type[Exception], __.AVT_Tuple[__.AVT_Type[Exception], ...]] = Exception):
        """
        @lifetime >= 0.3.58
        
        Roughly equivalent to::

            try:
                f()
            except exc:
                pass
        """
        
        if not _is_try_callback(f):
            error = TypeError("expected a function with no arguments")
            raise error
        
        if (not cls.isTuple(exc) and not issubclass(exc, Exception)) or (isinstance(exc, tuple) and not cls.all(exc, lambda x: issubclass(x, Exception))):
            error = TypeError("expected a tuple of subclasses of 'Exception' or 'Exception' class itself")
            raise error
        
        try:
            f()
        except exc:
            pass
        
    @classmethod
    def tryOrReturn(cls, f: __.AVT_Callable[[], _T1], r: _T2 = None, /, exc: __.Union[__.AVT_Type[Exception], __.AVT_Tuple[__.AVT_Type[Exception], ...]] = Exception, returnOnTry: bool = False):
        """
        @lifetime >= 0.3.58
        
        Roughly equivalent to::
        
            try:
                f()
            except exc:
                return r
        """
        
        if not _is_try_callback(f):
            error = TypeError("expected a function with no arguments")
            raise error
        
        if (not cls.isTuple(exc) and not issubclass(exc, Exception)) or (isinstance(exc, tuple) and not cls.all(exc, lambda x: issubclass(x, Exception))):
            error = TypeError("expected a tuple of subclasses of 'Exception' or 'Exception' class itself")
            raise error
        
        if returnOnTry:
            
            try:
                return f()
            except exc:
                return r
        
        else:
            
            cls.tryOrPass(f, exc)
            return r
                       
    @classmethod
    def copy(cls, x: _T):
        """
        @lifetime >= 0.3.34
        
        Same as `copy.copy()`.
        """
        return _copy.copy(x)
    
    @classmethod
    def deepcopy(cls, x: _T, memo: _opt[__.AVT_Dict[int, _Any]] = None, _nil: _Any = []):
        """
        @lifetime >= 0.3.34
        
        Same as `copy.deepcopy()`.
        """
        return _copy.deepcopy(x, memo, _nil)
    
    @classmethod
    def flatten(cls, i: __.AVT_Iterable[__.AVT_Iterable[_T]], /):
        """
        @lifetime >= 0.3.49
        
        Re-creation as `itertools.chain.from_iterable()`
        """
        
        if not isinstance(i, __.Iterable):
            error = TypeError("passed object isn't iterable")
            raise error
        
        l = cls.cast([], __.AVT_List[_T])
        
        _get_ = [([e] if isinstance(e, (str, bytes)) else e) for e in i]
        
        for e in _get_:
            l.extend(e)
        
        return cls.generator(l)
        
        # return list(_itertools.chain.from_iterable(i))
        
    @classmethod
    def getAttr(cls, o: object, names: __.Union[str, __.TrueSequence[str]], default: _T = None, /):
        """
        @lifetime >= 0.3.58
        
        Extension of `getattr()` that tries many attributes in a string sequence at once until one is defined and can be returned. If none of these exist, `default` is returned instead.
        
        0.3.59: If `names` is a string containing many names separated by space each, these are considered multiple attributes (inspired by `collections.namedtuple()`). Since the version, empty strings are excluded too
        """
        
        emitError = False
        
        if cls.isString(names):
            seq = names.strip().split(" ")
        
        elif isinstance(names, (__.Sequence, __.Uniqual)):
            seq = list(names)
            
            if not cls.isList(seq, str):
                emitError = True
        
        else:
            emitError = True
            
        if emitError:
            error = TypeError("expected a string or sequence/set of strings")
            raise error
        
        seq = list(filter(lambda x: reckon(x) > 0, seq)) # prevent empty string items
            
        for attr in seq:
            if hasattr(o, attr):
                return getattr(o, attr)
            
        return default    
            
    @classmethod
    def getAllItemsTypes(cls, i: __.AVT_Iterable[_T], /): # >= 0.3.51
        """
        @lifetime >= 0.3.51 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.getAllItemsTypes
        
        Returns all items' types in a set-like tuple, from an iterable
        """
        
        if not isinstance(i, __.Iterable):
            error = TypeError("passed object isn't iterable")
            raise error
        
        return _get_all_item_types(i)
    
    @classmethod # 0.3.53: tupleEllipsis
    def getGeneric(cls, v: _Any, /, tupleEllipsis: bool = False): # >= 0.3.52
        """
        @lifetime >= 0.3.52 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.getGeneric
        
        Returns generic alias as `<origin>[<args>, ...]` or `None` if it is not possible.
        Practically this class method tries to receive an IDE type hint, since normally it
        is *not* possible (when not using type hint syntax, aka PEP 484) or it is but deduced
        type is different. This speech reminds `typing.reveal_type()`, just is used to detect
        non-generic types.
        """
        
        # inspect union expressions (>=3.10)
        def _prepare_union_(*v: type, default: _T = _Any):
            
            if _sys.version_info >= (3, 10):
                
                if reckon(v) > 0:
                    
                    _union_: __.UnionType = v[0]
                
                    for e in v[1:]:
                        _union_ = _union_ | e
                        
                    return _union_

                else:
                    return default # replace with 'None' on 0.3.53
                
            else:
                
                if reckon(v) > 0:
                    return cls.cast(eval("__.Union[{}]".format(", ".join([t.__qualname__ for t in v])), globals()), __.TypingUnionType)
                
                else:
                    return default
        
        # use 'types.GenericAlias' if >=3.9 else 'typing._GenericAlias'
        if _sys.version_info >= (3, 9):
            _generic_ = __.GenericAlias
        else:
            _generic_ = _GenericTypes[0]
            
        # use 'types.UnionType' if >=3.10 else 'typing._UnionGenericAlias'; earlier: 'typing._SpecialForm'
        if _sys.version_info >= (3, 10):
            _union_ = __.UnionType
        else:
            _union_ = _UnionTypes[0]
            
        if isinstance(v, __.Iterable):
            
            # 0.3.53: mapping views
            if isinstance(v, (
                __.Mapping,
                __.KeysView,
                __.ValuesView,
                __.ItemsView
            )): 
                    
                if isinstance(v, (
                    __.KeysView,
                    __.ValuesView,
                    __.ItemsView
                )):
                    
                    # we will use their CamelCase equivalents, especially these classes are declared final
                    # in _collections_abc.pyi. Shouldn't make huge difference
                    if _hidden_collections_abc_def_check(v, "dict_items"):
                        _type_origin_ = __.DictItems
                        
                    elif _hidden_collections_abc_def_check(v, "dict_keys"):
                        _type_origin_ = __.DictKeys
                        
                    elif _hidden_collections_abc_def_check(v, "dict_values"):
                        _type_origin_ = __.DictValues
                        
                    else:
                        _type_origin_ = type(v)
                        
                    if not cls.isGeneric(_type_origin_):
                        return None
                    
                    # the 'mapping' property (since Python 3.10) is exclusive in 'dict_items', 'dict_keys' and 'dict_values'
                    # and should return 'types.MappingProxyType' instance
                    _mapping_ = cls.getAttr(v, "mapping _mapping")
                    
                    if _mapping_ is None:
                        
                        if isinstance(v, __.ItemsView):
                            
                            _mapping_ = dict(v.__iter__())
                            
                        elif isinstance(v, __.KeysView):
                            
                            return _generic_(_type_origin_, (_prepare_union_(*cls.getAllItemsTypes(list(v))), _Any))
                            
                        else:
                            
                            return _generic_(_type_origin_, (_Any, _prepare_union_(*cls.getAllItemsTypes(list(v)))))
                        
                    elif not isinstance(_mapping_, __.MappingProxyType):
                        return None
                    
                    # because 'types.MappingProxyType' inherits from 'collections.abc.Mapping', we can call all these 3 methods just
                    # as mere dict:
                    
                    return _generic_(_type_origin_, (
                        _prepare_union_(*cls.getAllItemsTypes(list(_mapping_.keys()))),
                        _prepare_union_(*cls.getAllItemsTypes(list(_mapping_.values())))
                    )) if reckon(list(_mapping_.items())) > 0 else None
                                
                else:
                    
                    if _hidden_collections_abc_def_check(v, "mappingproxy") or \
                       _hidden_collections_abc_def_check(v, "FrameLocalsProxy"):
                        _type_origin_ = __.MappingProxyType
                        
                    elif not cls.isGeneric(type(v)):
                        _type_origin_ = __.Mapping
                        
                    else:
                        _type_origin_ = type(v)
                    
                    return _generic_(_type_origin_, (
                        _prepare_union_(*cls.getAllItemsTypes(list(v.keys()))),
                        _prepare_union_(*cls.getAllItemsTypes(list(v.values())))
                    )) if reckon(list(v.items())) > 0 else None
                
            elif isinstance(v, __.Generator):
                
                if _hidden_collections_abc_def_check(v, "generator") or not cls.isGeneric(type(v)):
                    _type_origin_ = __.AVT_Generator
                else:
                    _type_origin_ = type(v)
                
                _yield_ = _prepare_union_(*cls.getAllItemsTypes(list(v)))
                # these both below have default value 'None', visible such as in generator expressions,
                # but generator doesn't have to be returned from generator expression and so these may
                # change and differ from 'None'. setting to 'typing.Any'
                _send_ = _Any
                _return_ = _Any
                
                return _generic_(_type_origin_, (
                    _yield_,
                    _send_,
                    _return_
                )) if reckon(list(v)) > 0 else None
            
            # 0.3.54: 'array.array' inherits from 'collections.abc.MutableSequence' since Python 3.10
            elif isinstance(v, (__.Sequence, __.Uniqual, __.array)): 
                
                _type_origin_ = type(v)
                
                # since 3.9 both these types are the same, but 'AVT_Tuple' changes to 'typing.Tuple' for 3.8
                # moreover, 'tuple == typing.Tuple' returns 'False'
                if _type_origin_ in (tuple, __.AVT_Tuple):
                    
                    if tupleEllipsis:
                        return _generic_(__.AVT_Tuple, (_prepare_union_(*cls.getAllItemsTypes(v)), ...)) if reckon(v) > 0 else None
                    else:
                        return _generic_(__.AVT_Tuple, _get_all_item_types(v, False)) if reckon(v) > 0 else None
                
                # 0.3.54: Revamp
                elif _type_origin_ is __.array:
                    
                    if not isinstance(v, __.array):
                        return None
                    
                    # type hint misses the 'w' type code
                    _typecode_ = v.typecode
                    
                    if _typecode_ in ('b', 'B', 'h', 'H', 'i', 'I', 'l', 'L', 'q', 'Q'):
                        return cls.cast(__.AVT_Array[int], _generic_)
                    
                    elif _typecode_ in ("f", "d"):
                        return cls.cast(__.AVT_Array[float], _generic_)
                    
                    elif _typecode_ in ("u", "w"): # "u" for backward compatibility
                        return cls.cast(__.AVT_Array[str], _generic_)
                    
                    else:
                        return _generic_(__.AVT_Array, (_prepare_union_(*cls.getAllItemsTypes(v.tolist())),)) if reckon(v.tolist()) > 0 else None
                
                # 0.3.54: Revamp
                elif _type_origin_ is memoryview:
                    
                    if not isinstance(v, memoryview):
                        return None
                    
                    _format_ = v.format
                    
                    if not cls.isString(_format_):
                        return None
                    
                    if _format_ in ("c", "@c"):
                        return cls.cast(__.AVT_MemoryView[bytes], _generic_)
                    
                    elif _format_ in ("f", "@f", "d", "@d"): # float, double
                        return cls.cast(__.AVT_MemoryView[float], _generic_)
                    
                    elif _format_ in ("?",):
                        return cls.cast(__.AVT_MemoryView[bool], _generic_)
                    
                    # extract from 'builtins._IntegerFormats'
                    elif _format_ in ('b', 'B', '@b', '@B', 'h', 'H', '@h', '@H', 'i', 'I', '@i', '@I', 'l', 'L', '@l', '@L', 'q', 'Q', '@q', '@Q', 'P', '@P'):
                        return cls.cast(__.AVT_MemoryView[int], _generic_)
                    
                    else:
                        return None

                return _generic_(_type_origin_, _prepare_union_(*cls.getAllItemsTypes(v))) if reckon(v) > 0 or not cls.isGeneric(_type_origin_) else None
            
            # 0.3.55a2
            elif isinstance(v, zip):
                
                if cls.isGeneric(type(v)):
                    _type_origin_ = type(v)
                else:
                    _type_origin_ = __.AVT_Zip
                    
                _zip_content = []
                
                while True:
                    
                    try:
                        _zip_content.append(next(v))
                        
                    except StopIteration:
                        break
                    
                _types = list(cls.flatten(_zip_content))
                    
                return _generic_(_type_origin_, _prepare_union_(*cls.getAllItemsTypes(_types))) if reckon(_types) > 0 or not cls.isGeneric(_type_origin_) else None
            
            # 0.3.55a2
            elif isinstance(v, enumerate):
                
                if cls.isGeneric(type(v)):
                    _type_origin_ = type(v)
                else:
                    _type_origin_ = __.AVT_Enumerate
                    
                _enumerate_convert = []
                
                for _, e in v:
                    _enumerate_convert.append(e)
                    
                return _generic_(_type_origin_, _prepare_union_(*cls.getAllItemsTypes(_enumerate_convert))) if reckon(_enumerate_convert) > 0 else None
            
            # 0.3.53: Revamp
            elif isinstance(v, __.Iterator): 
                
                if cls.isGeneric(type(v)):
                    _type_origin_ = type(v)
                else:
                    _type_origin_ = __.AVT_Iterator
                
                if _hidden_collections_abc_def_check(v, "bytearray_iterator"):
                    return _generic_(_type_origin_, (bytearray,))
                
                elif _hidden_collections_abc_def_check(v, "bytes_iterator"):
                    return _generic_(_type_origin_, (bytes,))
                
                elif _hidden_collections_abc_def_check(v, "dict_itemiterator"):
                    return _generic_(_type_origin_, (__.ItemsView,))
                
                elif _hidden_collections_abc_def_check(v, "dict_keyiterator"):
                    return _generic_(_type_origin_, (__.KeysView,))
                
                elif _hidden_collections_abc_def_check(v, "dict_valueiterator"):
                    return _generic_(_type_origin_, (__.ValuesView,))
                
                elif _hidden_collections_abc_def_check(v, "list_iterator"):
                    return _generic_(_type_origin_, (_generic_(__.AVT_List, (_prepare_union_(*cls.getAllItemsTypes(list(v))),)))) if reckon(list(v)) > 0 else None
                
                elif _hidden_collections_abc_def_check(v, "list_reverseiterator"):
                    return _generic_(_type_origin_, (_generic_(__.AVT_Iterator, (_prepare_union_(*cls.getAllItemsTypes(list(v))),)))) if reckon(list(v)) > 0 else None
                
                elif _hidden_collections_abc_def_check(v, "longrange_iterator") or \
                     _hidden_collections_abc_def_check(v, "range_iterator"):
                    return _generic_(_type_origin_, (range,))
                
                elif _hidden_collections_abc_def_check(v, "set_iterator"):
                    return _generic_(_type_origin_, (_generic_(__.AVT_Set, (_prepare_union_(*cls.getAllItemsTypes(list(v))),)))) if reckon(list(v)) > 0 else None
                
                elif _hidden_collections_abc_def_check(v, "str_iterator"):
                    return _generic_(_type_origin_, (str,))
                
                elif _hidden_collections_abc_def_check(v, "tuple_iterator"):
                    if tupleEllipsis:
                        return _generic_(_type_origin_, (_generic_(__.AVT_Tuple, (_prepare_union_(*cls.getAllItemsTypes(list(v))), ...)))) if reckon(list(v)) > 0 else None
                    else:
                        return _generic_(_type_origin_, (_generic_(__.AVT_Tuple, _get_all_item_types(list(v), False)))) if reckon(list(v)) > 0 else None
                
                elif _hidden_collections_abc_def_check(v, "zip_iterator"):
                    return _generic_(_type_origin_, (zip,))
                
        # 0.3.55b2
        elif isinstance(v, slice):
            
            _start_ = type(v.start) if v.start is not None else v.start
            _stop_ = type(v.stop) if v.stop is not None else v.stop
            _step_ = type(v.step) if v.step is not None else v.step
            
            return _generic_(__.AVT_Slice, (_start_, _stop_, _step_))
                
        elif isinstance(v, __.TypingCallableType):
            return cls.cast(v, _generic_)
            
        elif isinstance(v, __.Awaitable): # collections.abc.Awaitable also includes coroutines
            
            # receive generator without using the 'await' keyword
            _list_from_gen_ = list(v.__await__())
            
            # awaitable: one type parameter, coroutine: three
            if isinstance(v, __.Coroutine):
                
                if _hidden_collections_abc_def_check(v, "coroutine"):
                    _type_origin_ = __.AVT_Coroutine
                else:
                    _type_origin_ = type(v)
            
                return _generic_(_type_origin_, (
                    _prepare_union_(*cls.getAllItemsTypes(_list_from_gen_)), # 'yield'
                    _Any, # 'send'
                    _Any # 'return'
                )) if reckon(_list_from_gen_) > 0 else None
                
            else:
                
                return _generic_(_type_origin_, _Any)
            
        elif isinstance(v, __.AsyncIterable): # 0.3.53 // collections.abc.AsyncIterator (one type param) and AsyncGenerator (2 type params)
            
            _list_from_async_ = cls.toList(v)
            
            if isinstance(v, __.AsyncGenerator):
                
                if _hidden_collections_abc_def_check(v, "async_generator"):
                    _type_origin_ = __.AVT_AsyncGenerator
                else:
                    _type_origin_ = type(v)
                
                return _generic_(_type_origin_, (
                    _prepare_union_(*cls.getAllItemsTypes(_list_from_async_)), # 'yield'
                    _Any # 'return'
                )) if reckon(_list_from_async_) > 0 else None
                
            elif isinstance(v, __.AsyncIterator):
                
                if cls.isGeneric(type(v)):
                    _type_origin_ = type(v)
                else:
                    _type_origin_ = __.AVT_AsyncIterator
            
                return _generic_(_type_origin_, (*cls.getAllItemsTypes(_list_from_async_),))
            
            else:
                
                if cls.isGeneric(type(v)):
                    _type_origin_ = type(v)
                else:
                    _type_origin_ = __.AVT_AsyncIterable
                
                return _generic_(_type_origin_, (_Any,))
            
        elif isinstance(v, (_union_, __.TypingUnionType)):
            
            # both have the '__args__' attribute
            return cls.cast(_prepare_union_(*v.__args__), _generic_)
                
        elif isinstance(v, (_generic_, __.TypingGenericType)):
            return cls.cast(v, _generic_)
        
        elif isinstance(v, __.Pattern):
            return _generic_(type(v), (v.pattern,))
        
        elif isinstance(v, __.Match):
            return _generic_(type(v), (v.string,))
        
        elif isinstance(v, __.TypingCallableType):
            return cls.cast(v, _generic_)
        
        elif callable(v):
            
            p = _util.ParamVar(v)
            
            _annotations_ = dict(p.annotations)
            
            _completed_ = tuple([(_Any if k not in _annotations_ else _annotations_[k]) for k in (*p.all, "return")])
            
            # cannot deduce the 'return' type, unless it has type annotation too, this would be necessary
            # inspecting every 'return' statement within a function
            
            # 0.3.53: ellipsis for Callable once vararg and varkeywords are found
            if p.variableCount == 2:
                
                _completed_no_vars_ = tuple([(_Any if k not in _annotations_ else _annotations_[k]) for k in (*p.all, "return") if k not in dict(p.variable)])
                
                return cls.cast(__.AVT_Callable[[*_completed_no_vars_[:-1], ...], _completed_no_vars_[-1]], _generic_) # type: ignore
            
            return cls.cast(__.AVT_Callable[[*_completed_[:-1]], _completed_[-1]], _generic_) # type: ignore
                
        return None
    
    @classmethod
    def getFlags(cls, v: _Any, /):
        """
        @lifetime >= 0.3.53
        
        Returns flags of a type, buffer or callable object or -1 if it is not possible
        """
        
        if isinstance(v, type):
            
            return v.__flags__
        
        elif isinstance(v, memoryview):
            
            bufferFlags = 0
            
            if v.c_contiguous:
                bufferFlags |= _util.BufferFlags.contiguousC
                
            elif v.f_contiguous:
                bufferFlags |= _util.BufferFlags.contiguousF
                
            if v.readonly: # https://docs.python.org/3/c-api/buffer.html#c.Py_buffer.readonly
                bufferFlags |= _util.BufferFlags.writable
                
            return bufferFlags
        
        elif isinstance(v, __.CoroutineType):
            
            return v.cr_code.co_flags
        
        elif isinstance(v, __.TracebackType):
            
            return v.tb_frame.f_code.co_flags
        
        elif isinstance(v, __.FrameType):
            
            return v.f_code.co_flags
                
        elif callable(v):
            
            return v.__code__.co_flags
        
        else:
            
            return -1
        
    @classmethod
    def splitGeneric(cls, v: _Any, /):
        """
        @lifetime >= 0.3.55b1
        
        Splits generic alias into a tuple with type origin and type args in an internal tuple. Return `None` if value isn't a generic alias.
        """
        
        if not isinstance(v, _GenericTypes):
            return None
        
        return (cls.cast(v.__origin__, type), (*v.__args__,))
    
    @classmethod
    def print(cls, *values: object, separator: _opt[str] = " ", ending: _opt[str] = "\n", file: _uni[__.Writable[str], __.Flushable, None] = None, flush = False, reprFirst = False):
        """
        @lifetime >= 0.3.25
        
        Almost identical to `print()`.
        
        - 0.3.26a1: returns reference to `aveytense.Tense`
        - 0.3.27b1: setting `TenseOptions.insertionMessage` to override `invokeAs`
        - 0.3.41: Added `reprFirst` to invoke `repr()` before `str()`, and removed `invokedAs`
        """
        
        # a trick providing default value for 'x'
        _invoke_this = lambda x = object(): repr(x) if hasattr(x, "__repr__") else str(x)
        
        if reprFirst:
                
            print(*tuple([_invoke_this(e) for e in values]), sep = separator, end = ending, file = file, flush = flush)
            
        else:
                
            print(*values, sep = separator, end = ending, file = file, flush = flush)
            
        return cls
    
    @classmethod
    @__.overload
    def random(cls, x: _uni[__.TrueSequence[_T], __.AVT_Mapping[_Any, _T]], /) -> _T: ...
    
    @classmethod
    @__.overload
    def random(cls, x: int, /) -> int: ...
    
    @classmethod
    @__.overload
    def random(cls, x: int, y: int, /) -> int: ...
    
    @classmethod
    def random(cls, x, y = None, /):
        """
        @lifetime >= 0.3.24 \\
        @standard-lifetime >= 0.3.25 \\
        @modified 0.3.25, 0.3.26rc2 (support for `tkinter.IntVar`), 0.3.31 (cancelled support for `tkinter.IntVar`) \\
        0.3.34 (overloads)
        
        With one parameter, returns an item from a sequence or integer from range [0, x) \\
        With two parameters, returns an integer in specified range [x, y] or [y, x] if x > y.
        """
        if cls.isNone(y):
            
            if cls.isInteger(x):
                
                if x <= 1:
                    error = ValueError("expected a positive integer above 1")
                    raise error
                
                # lack of same overloads as in 'range' is less convincing, because 'x' is
                # theoretically considered value of 'start' parameter, not 'stop'
                return _random.randrange(x)
            
            elif isinstance(x, (__.Sequence, __.Uniqual, __.Mapping)): # 0.3.54: Mapping
                
                return cls.pick(x)
            
        a = [x, y]
        
        if cls.isList(a, int):
                
            _x, _y = a[0], a[1]
            
            if x > y:
                _x, _y = _y, _x
            
            return _random.randint(_x, _y)
            
        error = TypeError("no matching function signature")
        raise error
    
    if False:
        @classmethod
        def randomWithout(self, from_: int, to_: int, /, exclude: __.Union[range, _ab_mod.AbroadInitializer, None] = None):
            """
            @lifetime >= 0.3.52
            
            Equivalent to `~.Tense.pick(~.Tense.random(<from>, <oneBeforeStartPoint>), ~.Tense.random(<oneAfterEndpoint>, <to>))`.
            
            where `<oneBeforeStartPoint>` and `<oneAfterEndpoint>` are determined by `exclude` 2-item tuple
            """
            
            if not self.isInteger(from_, to_):
                error = TypeError("expected integers only in parameters '{}' and '{}'".format(*_get_all_params(self.randomWithout))[:2])
                raise error
            
            if not isinstance(exclude, (type(None), range, _ab_mod.AbroadInitializer)):
                error = TypeError("expected 'range' or 'abroad' object, or 'None' in parameter '{}'".format(_get_all_params(self.randomWithout))[2])
                raise error
            
            if isinstance(exclude, range):
                
                if exclude.start > exclude.stop:
                    error = ValueError("conflict with points. expected: 'from_' < 'exclude_start' < 'exclude_stop' < 'to_'")
                    raise error
                
                return self.pick((self.random(from_, exclude.start + 1), self.random(exclude.stop + 1, to_)))
                
    @classmethod
    def randomString(cls, lower = True, upper = True, digits = True, special = True, length = 10):
        """
        @lifetime >= 0.3.9; < 0.3.24; >= 0.3.25 \\
        to 0.3.34 known as `NennaiRandomize.randomizeStr()` \\
        to 0.3.60 known as `Tense.randstr()`
        
        - `lower` - determine, if you want to include all lowercased letters from english alphabet. Defaults to `True`
        - `upper` - determine, if you want to include all uppercased letters from english alphabet. Defaults to `True`
        - `digits` - determine, if you want to include all numbers. Defaults to `True`
        - `special` - determine, if you want to include all remaining chars accessible normally via English keyboard. Defaults to `True`
        - `length` - allows to specify the length of returned string. Defaults to `10`.
        """
        # code change 0.3.34
        conv = [""]
        conv.clear()
        ret = ""
        
        if lower:
            conv.extend([e for e in constants.STRING_LOWER])
                
        if upper:
            conv.extend([e for e in constants.STRING_UPPER])
                
        if digits:
            conv.extend([e for e in constants.STRING_DIGITS])
                
        if special:
            conv.extend([e for e in constants.STRING_SPECIAL])
        
        # there no matter if negative or positive
        for _ in abroad(length):
            ret += cls.pick(conv)
            
        return ret
    
    @classmethod
    def randomUuid(cls):
        """
        @lifetime >= 0.3.26a1
        
        Return a random UUID
        """
        
        import uuid
        return uuid.uuid4()
    
    @classmethod # before 0.3.46 this signature had no annotations
    def pick(cls, i: __.Union[__.SizeableItemGetter[_T], __.TrueSequence[_T], __.AVT_Mapping[_Any, _T]], /):
        """
        @lifetime >= 0.3.8 \\
        @standard-lifetime >= 0.3.24 \\
        @modified 0.3.25, 0.3.26rc2, 0.3.26rc3, 0.3.34 (overloads + mappings), 0.3.46 (no overloads) \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.pick
        
        Returns a random item from a sequence or value from a mapping
        """
        if isinstance(i, (__.SizeableItemGetter, __.Sequence, __.Uniqual, __.Mapping)):
            
            if reckon(i) == 0: 
                error = TypeError("expected at least one item in a sequence/set / one pair in a mapping/dictionary")
                raise error
            
            if isinstance(i, (__.Sequence, __.Uniqual)):
                _i = list(i) # Sequence and AbstractSet are both Iterable so these are convertible (0.3.46)
            elif isinstance(i, __.Mapping):
                _i = [i[k] for k in i]
            else:
                try:
                    _i = list(iter(i))
                except TypeError:
                    error = TypeError("expected a set, sequence, mapping or an object supporting item getting with integer indexes starting with 0")
                    raise error
            
            return _random.choice(_i)
        
        else:
            error = TypeError("expected a set, sequence, mapping or an object supporting item getting with integer indexes starting with 0")
            raise error
    
    @classmethod
    @__.overload
    def invert(cls, v: _uni[int, float], /) -> float: ...
    
    @classmethod
    @__.overload
    def invert(cls, v: _uni[__.TrueSequence[_uni[int, float]], _ab_mod.AbroadInitializer], /) -> __.AVT_List[float]: ...
    
    @classmethod
    @__.overload
    def invert(cls, v: __.AVT_Mapping[_KT, _VT], /) -> __.AVT_Dict[_VT, _KT]: ...
    
    @classmethod
    def invert(cls, v, /):
        """
        @lifetime >= 0.3.46
        
        Invert an integer or float (`1/v`) or a mapping (key becoming value and value becoming key).
        
        If you want to reverse order of a sequence, use `reverse()` method instead.
        """
        
        if cls.isInteger(v) or cls.isFloat(v):
            
            if v in (0, .0):
                error = ZeroDivisionError("division by zero")
                raise error
            
            return 1/v
        
        elif isinstance(v, (__.Sequence, __.Uniqual)) and cls.all(v, lambda x: cls.isInteger(x) or cls.isFloat(x)):
            
            _filter = cls.cast([1/e for e in v if e not in (0, .0)], __.AVT_List[float])
            
            if reckon(v) != reckon(_filter):
                error = ZeroDivisionError("division by zero")
                raise error
            
            return cls.cast([-e for e in v], __.AVT_List[float])
            
        elif isinstance(v, _ab_mod.AbroadInitializer):
            
            _filter = [1/e for e in v if e not in (0, .0)]
            
            if reckon(v) != reckon(_filter):
                error = ZeroDivisionError("division by zero")
                raise error
            
            return [1/e for e in v]
        
        elif isinstance(v, __.Mapping):
            
            return dict([(v[k], k) for k in v])
        
        else:
            
            error = TypeError("expected an integer, float, sequence/set of integers or floats or a mapping/dictionary")
            raise error
            
    # OVERLOAD 0.3.34
    @classmethod
    @__.overload
    def first(cls, i: __.TrueSequence[_T], /, condition: None = None, default: _S = None) -> _uni[_S, _T]: ...
    
    @classmethod
    @__.overload
    def first(cls, i: __.TrueSequence[_T], /, condition: _cal[[_T], bool], default: _S = None) -> _uni[_S, _T]: ...
            
    @classmethod
    def first(cls, i, /, condition = None, default = None):
        """
        @lifetime >= 0.3.26rc2 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.first
        
        Return first element in a `seq` (sequence) which satisfies `condition`. If none found, returned
        is default value defined via parameter `default`, which by default has value `None`. On 0.3.27a4
        removed this parameter, it has been restored on 0.3.34
        """
        
        if not _is_bool_callback(condition) and not cls.isNone(condition):
            error = TypeError("expected 'condition' parameter to be a callable or 'None'")
            raise error
        
        _seq = list(i)
        
        for _i in abroad(_seq):
            
            if condition is not None and condition(_seq[_i]):
                return _seq[_i]
            
            else:
                if _seq[_i]: return _seq[_i]
                
        return default
    
    # OVERLOAD 0.3.34
    @classmethod
    @__.overload
    def last(cls, i: __.TrueSequence[_T], /, condition: None = None, default: _S = None) -> _uni[_S, _T]: ...
    
    @classmethod
    @__.overload
    def last(cls, i: __.TrueSequence[_T], /, condition: _cal[[_T], bool], default: _S = None) -> _uni[_S, _T]: ...
    
    @classmethod
    def last(cls, i, /, condition = None, default = None):
        """
        @lifetime >= 0.3.26rc2 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.last
        
        Return last element in a `seq` (sequence) which satisfies `condition`. If none found, returned is default
        value defined via parameter `default`, which by default has value `None`. On 0.3.27a4 removed this parameter,
        it has been restored on 0.3.34
        """
        if not _is_bool_callback(condition) and not cls.isNone(condition):
            error = TypeError("expected 'condition' parameter to be a callable or 'None'")
            raise error
        
        _seq = list(i)
        
        for _i in cls.abroadNegative(1, _seq):
            
            if condition is not None and condition(_seq[_i]):
                return _seq[_i]
            
            else:
                if _seq[_i]: return _seq[_i]
                
        return default
    
    @classmethod
    def probability2(cls, x: _T1 = 1, y: _T2 = 0, frequency: int = 1, length: _ProbabilityLengthType = 10000):
        """
        @lifetime >= 0.3.8; < 0.3.24; >= 0.3.25 \\
        @standard-lifetime >= 0.3.9; < 0.3.24; >= 0.3.25 \\
        @modified 0.3.26a3, 0.3.26rc1, 0.3.31, 0.3.46 (utterly bypass `sys.maxsize`) \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.probability2
        
        Randomize a value using probability `frequency/length` applied on parameter `x`.
        Math interpretation: `P(x) = frequency/length` and `P(y) = 1 - P(x)`.
        Default values:
        - for `x`: 1
        - for `y`: 0
        - for `frequency`: 1
        - for `length`: 10000 (since 0.3.26a3 `length` can also have value `-1`)

        Default operation: return `x` with `1/10000` chance (0.01%) or `y` with `9999/10000` chance (99.99%).
        
        Value exceptions:
        - for `frequency` equal 0 or `x` equal `y`, returned is `y`
        - for `frequency` greater than (or since 0.3.25 equal) `length` returned is `x`
        """
        
        # due to swap from IntegerEnum to Enum in _ProbabilityLength class's subclass
        # it had to be replaced
        _length = 10000 if length in (-1, cls.PROBABILITY_COMPUTE) else length
        _frequency = frequency
        
        # 0.3.33: refraining from using string literals, since they will need to be manually changed
        # once parameter names are changed
        # note that 'return' keyword is reserved for return annotation with '->' operator
        _params = _get_all_params(cls.probability2) # 0.3.36: missing 2 after 'probability'
        # _options = [k for k in TenseOptions.__dict__ if k[:1] != "_"]
            
        if not cls.isInteger(_frequency):
            error = TypeError("expected an integer in parameter '{}'".format(_params[2]))
            raise error
        
        elif _frequency < 0:
            error = ValueError("expected a non-negative integer in parameter '{}'".format(_params[2]))
            raise error
        
        # types must match, otherwise you can meet an union-typed result, which is not useful during
        # type inspection, since you need to append appropriate 'if' statement!
        # exception: a function result being a union-typed one
        # for 0.3.46 it isn't necessary to both have the same type anyway, responsibility goes to user
        
        if cls.versionInfo < (0, 3, 46) and False:
            
            if not cls.isList([x, y], type(x)):
                error = TypeError("provided types in parameters '{}' and '{}' do not match".format(_params[0], _params[1]))
                raise error
        
        if not cls.isInteger(length) and length != cls.PROBABILITY_COMPUTE:
            error = TypeError("expected an integer or constant '{}' in parameter '{}'".format("PROBABILITY_" + cls.PROBABILITY_COMPUTE.name, _params[3]))
            raise error
        
        elif _length == 0:
            error = ZeroDivisionError("expected integer value from -1 or above in parameter '{}', but not equal zero".format(_params[3]))
            raise error
        
        elif _length < -1:
            error = ValueError("parameter '{}' may not have a negative integer value".format(_params[3]))
            raise error
        
        # these statements are according to probability math definition
        # once 'x' and 'y' are the same, there is no reason to activate loop at all
        
        try: # >= 0.3.51
            if x == y or _frequency == 0:
                return y
            
        except Exception:
            pass
        
        if _frequency >= _length:
            return x
        
        r = cls.random(1, _length)
        return x if Math.isInRange(r, 1, _frequency) else y
        
    @classmethod
    def probability3(cls, vf: __.AVT_Mapping[_T, __.Union[int, __.EllipsisType]], /):
        """
        @lifetime >= 0.3.46 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.probability3
        
        Abridged version of `~.probability()` without `length` parameter (length determined by mapping values),
        and `vf` parameter being positional-only non-variable parameter, which only accepts a mapping. Ellipsis
        equal 1.
        
        This class method is circa 3 times faster than `~.probability()` due to least amount of lines of code
        caused by least amount of statements, and only one, non-variable parameter to inspect
        """
        if _sys.version_info >= (3, 9):
            _check_if_mapping = isinstance(vf, __.Mapping)
            
        else:
            
            try:
                _check_if_mapping = isinstance(vf, __.Mapping)
                
            except Exception:
                _check_if_mapping = issubclass(type(vf), __.Mapping)
        
        if not _check_if_mapping:
            error = TypeError("expected a mapping/dictionary")
            raise error
        
        if reckon(vf) < 2:
            error = TypeError("expected at least 2 pairs in the mapping/dictionary")
            raise error
        
        elif reckon(vf) > _sys.maxsize:
            error = ValueError("too high amount of pairs in the mapping/dictionary, expected least or equal {}".format(_sys.maxsize))
            raise error
        
        else:
            
            _filter = dict([(k, vf[k]) for k in vf if cls.isEllipsis(vf[k]) or (cls.isInteger(vf[k]) and vf[k] > 0)])
            _keys, _values = [k for k in _filter], [_filter[k] for k in _filter]
            _values = [(1 if not cls.isInteger(e) else e) for e in _values]
            
            if reckon(vf) != reckon(_filter):
                error = TypeError("expected key values have positive integer or ellipsis")
                raise error
            
            if cls.all(_values, lambda x: x == 1):
                    
                return cls.pick(_keys)
            
            if reckon(vf) == 2:
                    
                return cls.probability2(_keys[0], _keys[1], _values[0], _values[0] + _values[1])
                
            else:
                    
                _value = 0
                _ranges = [(0, 0)]
                _ranges.clear()
                
                # amount of tuples in list is determined by amount of non-filtered pairs
                for e in _values:
                    
                    _ranges += [(_value + 1, _value + e)]
                    _value += e
                
                r = cls.random(1, _value)
                
                for i in abroad(_ranges):
                    
                    if Math.isInRange(r, _ranges[i][0], _ranges[i][1]):
                        return _keys[i]
                
                # not probable, but necessary if we don't want to use return annotation
                error = ValueError("couldn't return the value")
                raise error
                    
    @classmethod
    def probability(cls, *vf: _ProbabilityType[_T]):
        """
        @lifetime >= 0.3.8 \\
        @standard-lifetime >= 0.3.9 \\
        @modified 0.3.19, 0.3.24, 0.3.25, 0.3.26a3, 0.3.26b3, 0.3.26rc1, 0.3.26rc2, 0.3.31, 0.3.46 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.probability
        
        `vf` accepts 2-item sequences/sets, mappings and single values.
        """
        
        if reckon(vf) == 0:
            
            error = exceptions.MissingValueError("expected at least one value being mapping, or more values")
            raise error
        
        elif reckon(vf) == 1:
            
            e = vf[0]
            
            if not isinstance(e, __.Mapping):
                error = TypeError("expected a dictionary if there is only one value passed to parameter 'vf'")
                raise error
            
            if reckon(e) in (0, 1):
                error = TypeError("expected at least 2 pairs in a dictionary being the only value in parameter 'vf'")
                raise error
            
            elif reckon(e) > _sys.maxsize:
                error = ValueError("too high amount of pairs in a dictionary, expected least or equal {}".format(_sys.maxsize))
                raise error
            
            e: __.AVT_Mapping[_T, _uni[int, __.EllipsisType, None]] = e
            _filter = dict([(k, e[k]) for k in e if (cls.isEllipsis(e[k]) or cls.isNone(e[k])) or (cls.isInteger(e[k]) and e[k] > 0)])
            _keys, _values = [k for k in _filter], [_filter[k] for k in _filter]
            _values = [(1 if not cls.isInteger(e) else e) for e in _values]
            
            if reckon(e) != reckon(_filter):
                error = TypeError("expected key values have positive integer, ellipsis or None in a mapping")
                raise error
            
            _e = {_keys[i]: _values[i] for i in abroad(_keys)}
        
        else:
            
            _e: __.AVT_Dict[_T, int] = {}
            
            for e in vf:
                
                if isinstance(e, __.Mapping):
                    
                    if reckon(e) == 0:
                        error = TypeError("expected at least one pair in a mapping")
                        raise error
                    
                    e: __.AVT_Mapping[_T, _uni[int, __.EllipsisType, None]] = e
                    _filter = dict([(k, e[k]) for k in e if (cls.isEllipsis(e[k]) or cls.isNone(e[k])) or (cls.isInteger(e[k]) and e[k] > 0)])
                    _keys, _values = [k for k in _filter], [_filter[k] for k in _filter]
                    _values = [(1 if not cls.isInteger(e) else e) for e in _values]
                    
                    if reckon(e) != reckon(_filter):
                        error = TypeError("expected key values have positive integer, ellipsis or None in a mapping")
                        raise error
                    
                    _e = cls.extend(_e, {_keys[i]: _values[i] for i in abroad(_keys)})
                    
                elif isinstance(e, (__.Sequence, __.Uniqual)):
                    
                    _ie = list(e) # AbstractSet is not indexable
                    
                    if reckon(_ie) not in (1, 2):
                        error = TypeError("expected sequences and sets of size 1-2 only")
                        raise error
                    
                    elif reckon(_ie) == 1:
                        
                        _v1: _T = _ie[0]
                        _e = cls.extend(_e, {_v1: 1})
                        
                    else:
                        
                        _v2: __.AVT_Tuple[_T, int] = (_ie[0], 1 if not cls.isInteger(_ie[1]) else _ie[1])
                        _e = cls.extend(_e, {_v2[0]: _v2[1]})
                        
                else:
                    
                    _v3: _T = e
                    _e = cls.extend(_e, {_v3: 1})
                    
        return cls.probability3(_e)
    
    @classmethod
    def until(cls, desiredString: __.Union[str, __.AVT_Sequence[str]], /, message: _opt[str] = None, caseInsensitive: bool = True):
        """
        @lifetime >= 0.3.25 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.until
        
        Console-specific method, which will repeat the program *until* user won't
        write a correct string. Case is insensitive, may be configured via
        optional parameter `caseInsensitive`, which by default has
        value `True`. Returned is reference to this class.
        
        0.3.35 - Patch in first parameter `desiredString`
        """
        s = ""
        c = False
        
        if not isinstance(desiredString, (str, __.Sequence)) or (isinstance(desiredString, __.Sequence) and not cls.isString(desiredString) and not cls.isList(list(desiredString), str)):
            
            error = ValueError("expected a string or string sequence")
            raise error
        
        while c:
            
            s = input(message if message is not None and message != "" else "")
            c = s.lower() != desiredString.lower() if cls.isString(desiredString) else s.lower() not in (_s.lower() for _s in desiredString)
            
            if not caseInsensitive:
                c = s != desiredString if cls.isString(desiredString) else s not in desiredString
                
        return cls
    
    @classmethod
    def sleep(cls, seconds: float, /):
        """
        @lifetime >= 0.3.25 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.sleep
        
        Define an execution delay; equivalent to `time.sleep()`.
        """
        _time.sleep(seconds)
        return cls
    
    @classmethod
    def improvedBogoSort(cls, i: __.AVT_Iterable[_T], /, key: __.AVT_Callable[[_T], __.RichComparable] = ...):
        """
        @lifetime >= 0.3.42 \\
        https://aveyzan.xyz/aveytense#aveytense.Tense.improvedBogoSort
        
        Sort an iterable with improved bogo sort.
        
        Bogosort uses shuffling iterable's content to return sorted iterable. 'Improved' in the method name
        is its auxiliary appendix: this variant finds consecutive values from shuffled iterable, and places
        in a list, which will be returned, when list is sorted. This decreases amount of accesses, and shortens
        execution time.
        
        Returned is tuple with 2 items: accesses (integer) and sorted iterable as a list.
        """
        if isinstance(i, __.Iterable):
            
            l = list(i)
            
        else:
            
            error = TypeError("expected an iterable")
            raise error
        
        if cls.isEllipsis(key):
            
            _key = None
            
        elif callable(key) and reckon(util.ParamVar(key).positional, util.ParamVar(key).universal) == 1 and reckon(util.ParamVar(key).keyword) == 0:
            
            _key = key
            
        else:
            
            error = TypeError("expected an one-argument callable or ellipsis as a key")
            raise error
        
        if cls.hasAttr(l, ("__gt__", "__lt__"), mode = cls.constants.MODE_AND):
            pass
            
        else: # a subscripted type which is not comparable
            
            error = TypeError("expected an iterable which provides comparison operations")
            raise error
        
        _accesses = 0    
        
        for _i in abroad(1, l):
            
            while l[:_i] != sorted(l, key = _key)[:_i]:
                
                l[_i - 1:] = cls.shuffle(l[_i - 1:])
                _accesses += 1
            
        return _accesses, l
    
    __all__ = sorted([n for n in locals() if n[:1] != "_"])
    "@lifetime >= 0.3.26rc2"
    
    __dir__ = lambda self: __all__ # 0.3.42 fixed
    "@lifetime >= 0.3.26rc2"
    
aveytense = Tense()
AveyTense = Tense

class RGB(_util.Final):
    """
    @lifetime >= 0.3.28 \\
    https://aveyzan.xyz/aveytense#aveytense.RGB
    
    Auxiliary class for `Color` class. Represents red-green-blue color representation.
    """
    def __init__(self, red = 0, green = 0, blue = 0, /):
        
        _parameters = {
            "red": red,
            "green": green,
            "blue": blue
        }
        
        for key in _parameters:
            
            if not Tense.isInteger(_parameters[key]) or (Tense.isInteger(_parameters[key]) and _parameters[key] not in abroad(0x100)):
                error = TypeError("expected a non-negative integer in parameter '{}' in range 0-255".format(key))
                raise error
        
        _tmp = _inspect.currentframe().f_back.f_lineno
        self.__frame = _tmp if type(_tmp) is int else -1
        self.__rgb = (red, green, blue)
        
    def __str__(self):
        """
        @lifetime >= 0.3.28 \\
        https://aveyzan.xyz/aveytense#aveytense.RGB.?string_conversion
        """
        return "{}({})".format(type(self).__name__, ", ".join([str(e) for e in self.__rgb]))
        
    def __repr__(self):
        """
        @lifetime >= 0.3.28 \\
        [doc](https://aveyzan.xyz/aveytense#aveytense.RGB.__repr__)
        """
        return "<<'{}.{}' object :: {}> defined in line {}>".format(self.__module__, type(self).__name__, self.__str__(), self.__frame) # 0.3.41: Added line inspect
    
    def __hex__(self):
        """
        @lifetime >= 0.3.28 \\
        https://aveyzan.xyz/aveytense#aveytense.RGB.?hexadecimal_conversion
        
        Provides conversion to hexadecimal format
        """
        
        # 0.3.56: version with constant indexes is faster. I got to inspect different alternative in the meantime:
        ###
        # _rgb = [""]
        # _rgb.clear()
        # for i in abroad(self.__rgb):
        #   _rgb.append(hex(self.__rgb[i])[2:] if self.__rgb[i] >= 0x10 else "0" + hex(self.__rgb[i])[2:])
        # return "0x" + "".join(_rgb)
        ###
        
        _r = hex(self.__rgb[0])[2:] if self.__rgb[0] >= 0x10 else "0" + hex(self.__rgb[0])[2:]
        _g = hex(self.__rgb[1])[2:] if self.__rgb[1] >= 0x10 else "0" + hex(self.__rgb[1])[2:]
        _b = hex(self.__rgb[2])[2:] if self.__rgb[2] >= 0x10 else "0" + hex(self.__rgb[2])[2:]
        return "0x" + _r + _g + _b
    
    def __int__(self):
        """
        @lifetime >= 0.3.28 \\
        https://aveyzan.xyz/aveytense#aveytense.RGB.?integer_conversion
        
        Converts RGB tuple into its corresponding integer representation.
        
        Use it as `int(<RGB_OBJECT>)` instead of using other ways to retrieve the integer, since it may be bound with higher execution time.
        """
        
        # In 0.3.56 I looked at another version of getting the integer: 'int(eval(self.__hex__()))'
        # however, its execution time was longer than 'int(self.__hex__()[2:], base = 16)'. About
        # these, do not use these, rather use int(self) instead for faster performance.
        return int(self.__hex__()[2:], base = 16) 
    
    # little deviation from type hinting in methods below
    # read document strings to figure it out
    def __lt__(self, other): 
        """
        @lifetime >= 0.3.28 \\
        https://aveyzan.xyz/aveytense#aveytense.RGB.?comparison_operators
        
        To return true, following conditions must be satisfied:
        - `int(self) < int(other)`
        - `other` must be instance of `RGB` class
        """
        return self.__int__() < other.__int__() if type(other) is type(self) else False
    
    def __gt__(self, other):
        """
        @lifetime >= 0.3.28 \\
        https://aveyzan.xyz/aveytense#aveytense.RGB.?comparison_operators
        
        To return true, following conditions must be satisfied:
        - `int(self) > int(other)`
        - `other` must be instance of `RGB` class
        """
        return self.__int__() > other.__int__() if type(other) is type(self) else False
    
    def __eq__(self, other):
        """
        @lifetime >= 0.3.28 \\
        https://aveyzan.xyz/aveytense#aveytense.RGB.?comparison_operators
        
        To return true, following conditions must be satisfied:
        - `int(self) == int(other)`
        - `other` must be instance of `RGB` class
        """
        return self.__int__() == other.__int__() if type(other) is type(self) else False
    
    def __le__(self, other):
        """
        @lifetime >= 0.3.28 \\
        https://aveyzan.xyz/aveytense#aveytense.RGB.?comparison_operators
        
        To return true, following conditions must be satisfied:
        - `int(self) <= int(other)`
        - `other` must be instance of `RGB` class
        """
        return self.__int__() <= other.__int__() if type(other) is type(self) else False
    
    def __ge__(self, other):
        """
        @lifetime >= 0.3.28 \\
        https://aveyzan.xyz/aveytense#aveytense.RGB.?comparison_operators
        
        To return true, following conditions must be satisfied:
        - `int(self) >= int(other)`
        - `other` must be instance of `RGB` class
        """
        return self.__int__() >= other.__int__() if type(other) is type(self) else False
    
    def __ne__(self, other):
        """
        @lifetime >= 0.3.28 \\
        https://aveyzan.xyz/aveytense#aveytense.RGB.?comparison_operators
        
        To return true, following conditions must be satisfied:
        - `int(self) != int(other)`
        - `other` must be instance of `RGB` class
        """
        return self.__int__() != other.__int__() if type(other) is type(self) else False
    
    def __contains__(self, i):
        """
        @lifetime >= 0.3.56
        
        Determine if a number is in the RGB tuple.
        """
        
        return isinstance(i, int) and i in self.__rgb
    
    if False: # < 0.3.49
        
        @__.deprecated("deprecated since 0.3.41, will be removed 0.3.49. use `tuple` final property instead")
        def __pos__(self):
            """
            @lifetime >= 0.3.28 \\
            @deprecated >= 0.3.47 (up for removal in 0.3.48) \\
            https://aveyzan.xyz/aveytense#aveytense.RGB.tuple
            
            Returns a RGB tuple
            """
            return self.__rgb
        
        @__.deprecated("deprecated since 0.3.41, will be removed 0.3.49. use `tuple` final property instead")
        def __neg__(self):
            """
            @lifetime >= 0.3.28 \\
            @deprecated >= 0.3.47 (up for removal in 0.3.48) \\
            https://aveyzan.xyz/aveytense#aveytense.RGB.tuple
            
            Returns a RGB tuple
            """
            return self.__rgb
        
        @__.deprecated("deprecated since 0.3.41, will be removed 0.3.49. use `tuple` final property instead")
        def __invert__(self):
            """
            @lifetime >= 0.3.28 \\
            @deprecated >= 0.3.47 (up for removal in 0.3.48) \\
            https://aveyzan.xyz/aveytense#aveytense.RGB.tuple
            
            Returns a RGB tuple
            """
            return self.__rgb 
    
    def __bytes__(self):
        """
        @lifetime >= 0.3.41 \\
        https://aveyzan.xyz/aveytense#aveytense.RGB.?bytes_conversion
        
        Return a new `bytes` instance formed from the RGB tuple's integer values.
        """
        return bytes(self.__rgb) # integer-only tuple so it is convertible
    
    def __hash__(self):
        """
        @lifetime >= 0.3.41 \\
        [doc](https://aveyzan.xyz/aveytense#aveytense.RGB.__hash__)
        
        Returns RGB tuple as a hash.
        """
        return hash(self.__rgb) # hashable; tuple is hashable
    
    def __bool__(self):
        """
        @lifetime >= 0.3.41 \\
        [doc](https://aveyzan.xyz/aveytense#aveytense.RGB.__bool__)
        
        Converts RGB tuple to a boolean value. Always returns `True`
        """
        return True
    
    def __bin__(self):
        """
        @lifetime >= 0.3.41 \\
        https://aveyzan.xyz/aveytense#aveytense.RGB.?binary_conversion
        
        Converts RGB tuple into its corresponding binary value.
        """
        return bin(self.__int__())
    
    def __oct__(self):
        """
        @lifetime >= 0.3.41 \\
        https://aveyzan.xyz/aveytense#aveytense.RGB.?octal_conversion
        
        Converts RGB tuple into its corresponding octal value.
        """
        return oct(self.__int__())
    
    @_util.finalproperty
    def hex(self):
        """
        @lifetime >= 0.3.38 \\
        https://aveyzan.xyz/aveytense#aveytense.RGB.?hexadecimal_conversion
        
        Provides conversion to hexadecimal format
        """
        return self.__hex__()
    
    @_util.finalproperty
    def cssHex(self):
        """
        @lifetime >= 0.3.49 \\
        https://aveyzan.xyz/aveytense#aveytense.RGB.?hexadecimal_conversion
        
        Provides conversion to hexadecimal format, just with different prefix: \\
        `#` instead of `0x`, to be used in CSS
        """
        return "#" + self.hex[2:]
    
    @_util.finalproperty
    def cssRgb(self):
        """
        @lifetime >= 0.3.49 \\
        https://aveyzan.xyz/aveytense#aveytense.RGB.?string_conversion
        
        Returns string with format `rgb(r, g, b)`, to be used in CSS. \\
        Equivalent to `str(self).lower()`
        """
        return self.__str__().lower()
    
    @_util.finalproperty
    def oct(self):
        """
        @lifetime >= 0.3.44 \\
        https://aveyzan.xyz/aveytense#aveytense.RGB.?octal_conversion
        
        Converts RGB tuple into its corresponding octal value.
        """
        return self.__oct__()
    
    @_util.finalproperty
    def bin(self):
        """
        @lifetime >= 0.3.44 \\
        https://aveyzan.xyz/aveytense#aveytense.RGB.?binary_conversion
        
        Converts RGB tuple into its corresponding binary value.
        """
        return self.__bin__()
    
    @_util.finalproperty
    def tuple(self):
        """
        @lifetime >= 0.3.38 \\
        https://aveyzan.xyz/aveytense#aveytense.RGB.tuple
        
        Returns a RGB tuple
        """
        return self.__rgb
    
    @_util.finalproperty
    def r(self):
        """
        @lifetime >= 0.3.45 \\
        https://aveyzan.xyz/aveytense#aveytense.RGB.?values
        
        Returns R (red) value from RGB tuple.
        """
        return self.tuple[0]
    
    @_util.finalproperty
    def g(self):
        """
        @lifetime >= 0.3.45 \\
        https://aveyzan.xyz/aveytense#aveytense.RGB.?values
        
        Returns G (green) value from RGB tuple.
        """
        return self.tuple[1]
    
    @_util.finalproperty
    def b(self):
        """
        @lifetime >= 0.3.45 \\
        https://aveyzan.xyz/aveytense#aveytense.RGB.?values
        
        Returns B (blue) value from RGB tuple.
        """
        return self.tuple[2]
    
    @staticmethod
    def fromValue(n: _uni[int, str, _util.MutableString], /):
        """
        @lifetime >= 0.3.36 \\
        https://aveyzan.xyz/aveytense#aveytense.RGB.fromValue
        
        Returns a new `RGB` class object using specific integer or string value. \\
        If string was provided, it must contain a valid number in either hexadecimal, \\
        decimal, octal or binary notation.
        
        Updated 0.3.37, 0.3.38, 0.3.39, 0.3.42, 0.3.45
        """
        
        _n = n.value if isinstance(n, _util.MutableString) else n # 0.3.45
        
        if (Tense.isInteger(_n) and Math.isInRange(_n, 0, constants.RGB_MAX)) or (
            Tense.isString(_n) and ((_is_hexadecimal(_n) or _is_decimal(_n) or _is_octal(_n) or _is_binary(_n)) and Math.isInRange(_int_conversion(_n), 0, constants.RGB_MAX))
        ):
        
            # General notice: using hex(...)[2:] allows to exclude '0x' prefix from the comparison, and we would need to do that anyway, so we can implicitly
            # convert a string into a RGB tuple.
            # 25.03.2025
            
            if Tense.isInteger(_n):
                
                # >= 0.3.42
                if reckon(hex(_n)[2:]) < 6:

                    _hex = "0" * (6 - reckon(hex(_n)[2:])) + hex(_n)[2:]
                    
                else:
                    
                    _hex = hex(_n)[2:]
                
            else:
                
                # >= 0.3.42
                if _is_hexadecimal(_n):
                    _interpret_base = 16
                    
                elif _is_octal(_n):
                    _interpret_base = 8
                    
                elif _is_binary(_n):
                    _interpret_base = 2
                    
                else:
                    _interpret_base = 0
                
                # >= 0.3.42
                if reckon(_n) < 6:
                    
                    # >= 0.3.45
                    if reckon(_n) == 3:
                        
                        _hex = "".join([c * 2 for c in hex(int(_n, _interpret_base))[2:]])
                        
                    else:
                        
                        _hex = "0" * (6 - reckon(hex(int(_n, _interpret_base))[2:])) + hex(int(_n, _interpret_base))[2:]
                        
                else:    
                
                    _hex = hex(int(_n, _interpret_base))[2:]
                    
            return RGB(int(_hex[: 2], 16), int(_hex[2 : 4], 16), int(_hex[4 :], 16)) # 0.3.42
        
        else:
            
            error = ValueError("expected a number in range 0-16777215")
            raise error
        
class RGBA(_util.Final):
    """
    @lifetime >= 0.3.37
    
    Represents red-green-blue-alpha color representation.
    """
    
    def __init__(self, red = 0, green = 0, blue = 0, alpha = 1.0):
        
        _parameters = {
            "red": red,
            "green": green,
            "blue": blue,
        }
        
        for key in _parameters:
            
            if not Tense.isInteger(_parameters[key]) or (Tense.isInteger(_parameters[key]) and _parameters[key] not in abroad(0x100)):
                
                error = TypeError("expected a non-negative integer in parameter '{}' in range 0-255".format(key))
                raise error
            
        if not Tense.isFloat(alpha) or (Tense.isFloat(alpha) and not Math.isInRange(alpha, 0, 1)):
            
            error = TypeError("expected a non-negative float in parameter '{}' in range 0-1".format("alpha"))
            raise error
        
        _tmp = _inspect.currentframe().f_back.f_lineno
        self.__frame = _tmp if type(_tmp) is int else -1
        self.__rgba = (red, green, blue, round(alpha, 2))
        
    def __str__(self):
        """
        @lifetime >= 0.3.37
        """
        return "{}({}, {})".format(type(self).__name__, ", ".join([str(e) for e in self.__rgba][:-1]), self.__rgba[-1])
    
    def __repr__(self):
        """
        @lifetime >= 0.3.37
        """
        return "<<{}.{} object: {}> defined in line {}>".format(self.__module__, type(self).__name__, self.__str__(), self.__frame)
    
    def __hex__(self):
        """
        @lifetime >= 0.3.38
        
        Provides conversion to hexadecimal format. \\
        Does not occur with alpha value - use `float()` instead.
        """
        _r = hex(self.__rgba[0])[2:] if self.__rgba[0] >= 0x10 else "0" + hex(self.__rgba[0])[2:]
        _g = hex(self.__rgba[1])[2:] if self.__rgba[1] >= 0x10 else "0" + hex(self.__rgba[1])[2:]
        _b = hex(self.__rgba[2])[2:] if self.__rgba[2] >= 0x10 else "0" + hex(self.__rgba[2])[2:]
        return "0x" + _r + _g + _b
    
    def __int__(self):
        """
        @lifetime >= 0.3.38
        
        Converts RGBA tuple into its corresponding integer representation. \\
        Does not occur with alpha value - use `float()` instead.
        """
        return int(self.__hex__()[2:], base = 16)
    
    def __float__(self):
        """
        @lifetime >= 0.3.38
        
        Returns alpha value
        """
        return self.__rgba[-1]
    
    # little deviation from type hinting in methods below
    # read document strings to figure it out
    def __lt__(self, other):
        """
        @lifetime >= 0.3.38
        
        To return true, following conditions must be satisfied:
        - `int(self) + float(self) < int(other) + float(other)`
        - `other` must be instance of `RGBA` class
        """
        return self.__int__() + self.__float__() < float(int(other)) + float(other) if type(other) is type(self) else False
    
    def __gt__(self, other):
        """
        @lifetime >= 0.3.38
        
        To return true, following conditions must be satisfied:
        - `int(self) + float(self) > int(other) + float(other)`
        - `other` must be instance of `RGBA` class
        """
        return self.__int__() + self.__float__() > float(int(other)) + float(other) if type(other) is type(self) else False
    
    def __eq__(self, other):
        """
        @lifetime >= 0.3.38
        
        To return true, following conditions must be satisfied:
        - `int(self) + float(self) == int(other) + float(other)`
        - `other` must be instance of `RGBA` class
        """
        return self.__int__() + self.__float__() == float(int(other)) + float(other) if type(other) is type(self) else False
    
    def __le__(self, other):
        """
        @lifetime >= 0.3.38
        
        To return true, following conditions must be satisfied:
        - `int(self) + float(self) <= int(other) + float(other)`
        - `other` must be instance of `RGBA` class
        """
        return self.__int__() + self.__float__() <= float(int(other)) + float(other) if type(other) is type(self) else False
    
    def __ge__(self, other):
        """
        @lifetime >= 0.3.38
        
        To return true, following conditions must be satisfied:
        - `int(self) + float(self) >= int(other) + float(other)`
        - `other` must be instance of `RGBA` class
        """
        return self.__int__() + self.__float__() >= float(int(other)) + float(other) if type(other) is type(self) else False
    
    def __ne__(self, other):
        """
        @lifetime >= 0.3.38
        
        To return true, following conditions must be satisfied:
        - `int(self) + float(self) != int(other) + float(other)`
        - `other` must be instance of `RGBA` class
        """
        return self.__int__() + self.__float__() != float(int(other)) + float(other) if type(other) is type(self) else False
    
    if False: # < 0.3.56
    
        @__.deprecated("Deprecated since 0.3.47, will be removed in 0.3.48. Use str(self) instead")
        def __pos__(self):
            """
            @lifetime >= 0.3.38
            
            Returns a RGBA tuple
            """
            return self.__rgba
        
        @__.deprecated("Deprecated since 0.3.47, will be removed in 0.3.48. Use str(self) instead")
        def __neg__(self):
            """
            @lifetime >= 0.3.38
            
            Returns a RGBA tuple
            """
            return self.__rgba
        
        @__.deprecated("Deprecated since 0.3.47, will be removed in 0.3.48. Use str(self) instead")
        def __invert__(self):
            """
            @lifetime >= 0.3.38
            
            Returns a RGBA tuple
            """
            return self.__rgba
    
    @staticmethod
    def fromValue(n: _uni[int, str, _util.MutableString], opacity: float, /):
        """
        @lifetime >= 0.3.38
        
        Returns a new `RGBA` class object using specific integer or string value, and opacity. \\
        If string was provided on first parameter, it must contain a valid number in either hexadecimal, \\
        decimal, octal or binary notation.
        """
        
        _rgb = RGB.fromValue(n).tuple
        
        if not Tense.isFloat(opacity) or (Tense.isFloat(opacity) and not Math.isInRange(opacity, 0, 1)):
            
            error = TypeError("expected a non-negative float in parameter '{}' in range 0-1".format("alpha"))
            raise error
        
        return RGBA(_rgb[0], _rgb[1], _rgb[2], opacity)
    
    
class CMYK(_util.Final):
    """
    @lifetime >= 0.3.28
    
    Auxiliary class for `Color` class. Represents cyan-magenta-yellow color representation. \\
    Once instantiated, returns `RGB` class instance, only with inverted color values, that is: \\
    255 is 0, 254 is 1, 253 is 2 and so on, up to 0 being 255.
    """
    
    def __new__(self, cyan = 0, magenta = 0, yellow = 0, /):
        
        _parameters = {
            "cyan": cyan,
            "magenta": magenta,
            "yellow": yellow
        }
        
        for key in _parameters:
            
            if not isinstance(_parameters[key], int) or (isinstance(_parameters[key], int) and _parameters[key] not in abroad(0x100)):
                error = TypeError("expected a non-negative integer in parameter '" + key + "' in range 0-255")
                raise error
            
        return RGB(
            0xff - cyan,
            0xff - magenta,
            0xff - yellow
        )

# class _ChangeVarState(tc.IntegerFlag): # to 0.3.28
class _ChangeVarState(__.Enum):
    "@lifetime >= 0.3.26rc1. Internal class for `ChangeVar.setState()` method"
    I = 1
    D = 2

# _ChangeVarStateSelection = _lit[_ChangeVarState.D, _ChangeVarState.I] # unnecessary since 0.3.27b2

class ChangeVar(__.UnaryOperable, __.Comparable, __.AdditionReassignable, __.SubtractionReassignable):
    """
    @lifetime >= 0.3.26rc1 \\
    https://aveyzan.xyz/aveytense#aveytense.ChangeVar
    
    Auxiliary class for creating sentinel inside `while` loop.

    Use `~instance` to receive integer value. \\
    Use `+instance` to increment by 1. \\
    Use `-instance` to decrement by 1. \\
    Use `instance += any_int` to increment by `any_int`. \\
    Use `instance -= any_int` to decrement by `any_int`.
    """
    D = _ChangeVarState.D
    I = _ChangeVarState.I
    __v = 0
    __m = 1
    __default = 0

    def __init__(self, initialValue = 0):
        
        if not Tense.isInteger(initialValue):
            error = TypeError("expected an integer value")
            raise error
        
        self.__v = initialValue
        self.__default = initialValue

    def __pos__(self):
        self.__v += self.__m

    def __neg__(self):
        self.__v -= self.__m

    def __invert__(self):
        return self.__v
    
    def __eq__(self, other: int):
        return self.__v == other if Tense.isInteger(other) else False
    
    def __contains__(self, value: int):
        return self.__v == value if Tense.isInteger(value) else False
    
    def __ne__(self, other: int):
        return self.__v != other if Tense.isInteger(other) else False
    
    def __ge__(self, other: int):
        return self.__v >= other if Tense.isInteger(other) else False
    
    def __gt__(self, other: int):
        return self.__v > other if Tense.isInteger(other) else False
    
    def __le__(self, other: int):
        return self.__v <= other if Tense.isInteger(other) else False
    
    def __lt__(self, other: int):
        return self.__v < other if Tense.isInteger(other) else False
    
    def __iadd__(self, other: int):
        
        if not Tense.isInteger(other):
            error = TypeError("expected an integer as a right operand") # error replaced 0.3.34; earlier was NotInitializedError
            raise error
        
        _tmp = self.__v
        _tmp += other
        self.__v = _tmp
        return _tmp
    
    def __isub__(self, other: int):
        
        if not Tense.isInteger(other):
            error = TypeError("expected an integer as a right operand") # error replaced 0.3.34; earlier was NotInitializedError
            raise error
        
        _tmp = self.__v
        _tmp -= other
        self.__v = _tmp
        return _tmp
    
    def reset(self):
        """
        @lifetime >= 0.3.26rc1

        Reset the counter to value passed to the constructor, or - \\
        if `setDefault()` was invoked before - to value passed \\
        to that method.
        """
        self.__v = self.__default

    def setDefault(self, value):
        """
        @lifetime >= 0.3.26rc1

        Set a new default value. This overwrites current default value. \\
        Whether `reset()` method is used after, internal variable \\
        will have the default value, which was passed to this method. \\
        Otherwise it will refer to value passed to constructor
        """
        if not Tense.isInteger(value):
            error = TypeError("expected an integer value")
            raise error
        
        self.__default = abs(value)

    def setState(self, s: _ChangeVarState = I, m = 1):
        """
        @lifetime >= 0.3.26rc1

        Alternative for `+` and `-` unary operators.

        If `D` for `s` parameter is passed, sentinel will be decremented \\
        by 1, otherwise incremented by 1 (option `I`). Additionally, you \\
        can set a different step via `m` parameter.
        """
        _m = m
        
        if not Tense.isInteger(_m):
            error = TypeError("expected integer value for 'm' parameter")
            raise error
        
        elif abs(_m) == 0:
            _m = 1
            
        if s == self.D:
            self.__v -= abs(_m)
            
        elif s == self.I:
            self.__v += abs(_m)
            
        else:
            error = TypeError("expected 'ChangeVar.I' or 'ChangeVar.D' for 's' parameter")
            raise error
        
    def setModifier(self, m):
        """
        @lifetime >= 0.3.26rc1

        Changes behavior for `+` and `-` unary operators. \\
        If passed integer value was negative, code will \\
        retrieve absolute value of it. If 0 passed, used will be 1
        """
        _params = _get_all_params(self.setModifier)
        
        if not Tense.isInteger(m):
            error = TypeError("expected integer value in parameter '{}'".format(_params[0]))
            raise error
        
        elif abs(m) == 0:
            self.__m == 1
            
        self.__m = abs(m)

class Colors(_util.AbstractFinal):
    """
    @lifetime >= 0.3.41
    
    Provides colors accessible via names. \\
    All of them are instances of class `~.RGB`.
    
    To test them, use `~.Color("<text>", 24, ~.[Colors/Color.select].<var name>)`
    """
    
    # source: https://htmlcolorcodes.com/color-names/
    
    ### BELOW: 0.3.41
    indianRed = RGB(205, 92, 92)
    lightCoral = RGB(240, 128, 128)
    salmon = RGB(250, 128, 114)
    darkSalmon = RGB(233, 150, 122)
    lightSalmon = RGB(233, 160, 122)
    crimson = RGB(220, 20, 60)
    red = RGB(255, 0, 0)
    fireBrick = RGB(178, 34, 34)
    darkRed = RGB(139, 0, 0)
    
    pink = RGB(255, 192, 203)
    lightPink = RGB(255, 182, 193)
    hotPink = RGB(255, 105, 180)
    deepPink = RGB(255, 20, 147)
    mediumVioletRed = RGB(199, 21, 133)
    
    coral = RGB(255, 127, 80)
    tomato = RGB(255, 99, 71)
    orangeRed = RGB(255, 69, 0)
    darkOrange = RGB(255, 140, 0)
    orange = RGB(255, 165, 0)
    
    gold = RGB(255, 215, 0)
    yellow = RGB(255, 255, 0)
    lightYellow = RGB(255, 255, 224)
    lemonChiffon = RGB(255, 250, 205)
    lightGoldenrodYellow = RGB(250, 250, 210)
    papayaWhip = RGB(255, 239, 213)
    moccasin = RGB(255, 228, 181)
    peachPuff = RGB(255, 218, 185)
    paleGoldenrod = RGB(238, 232, 170)
    khaki = RGB(240, 230, 140)
    darkKhaki = RGB(189, 183, 107)
    
    lavender = RGB(230, 230, 250)
    thistle = RGB(216, 191, 216)
    plum = RGB(221, 160, 221)
    violet = RGB(238, 130, 238)
    orchid = RGB(218, 112, 214)
    fuchsia = magenta = RGB(255, 0, 255)
    mediumOrchid = RGB(186, 85, 211)
    mediumPurple = RGB(147, 112, 219)
    rebeccaPurple = RGB(102, 51, 153)
    blueViolet = RGB(138, 43, 226)
    darkViolet = RGB(148, 0, 211)
    darkOrchid = RGB(153, 50, 204)
    darkMagenta = RGB(139, 0, 139)
    purple = RGB(128, 0, 128)
    indigo = RGB(75, 0, 130)
    slateBlue = RGB(106, 90, 205)
    darkSlateBlue = RGB(72, 61, 139)
    mediumSlateBlue = RGB(123, 104, 238)
    
    greenYellow = RGB(173, 255, 47)
    chartreuse = RGB(127, 255, 0)
    lawnGreen = RGB(124, 252, 0)
    lime = RGB(0, 255, 0)
    limeGreen = RGB(50, 250, 50)
    paleGreen = RGB(152, 251, 152)
    lightGreen = RGB(144, 238, 144)
    mediumSpringGreen = RGB(0, 250, 154)
    springGreen = RGB(0, 255, 127)
    mediumSeaGreen = RGB(60, 179, 113)
    seaGreen = RGB(46, 139, 87)
    forestGreen = RGB(34, 139, 34)
    green = RGB(0, 128, 0)
    darkGreen = RGB(0, 100, 0)
    yellowGreen = RGB(154, 205, 50)
    oliveDrab = RGB(107, 142, 35)
    olive = RGB(128, 128, 0)
    darkOliveGreen = RGB(85, 107, 47)
    mediumAquamarine = RGB(102, 205, 170)
    darkSeaGreen = RGB(143, 188, 139)
    lightSeaGreen = RGB(32, 178, 170)
    darkCyan = RGB(0, 139, 139)
    teal = RGB(0, 128, 128)
    
    aqua = cyan = RGB(0, 255, 255)
    lightCyan = RGB(224, 255, 255)
    paleTurquoise = RGB(175, 238, 238)
    aquamarine = RGB(127, 255, 212)
    turquoise = RGB(64, 224, 208)
    mediumTurquoise = RGB(72, 209, 204)
    darkTurquoise = RGB(0, 206, 209)
    cadetBlue = RGB(95, 158, 160)
    steelBlue = RGB(70, 130, 180)
    lightSteelBlue = RGB(176, 196, 222)
    powderBlue = RGB(176, 224, 230)
    lightBlue = RGB(173, 216, 230)
    skyBlue = RGB(135, 206, 235)
    lightSkyBlue = RGB(135, 206, 250)
    deepSkyBlue = RGB(0, 191, 255)
    dodgerBlue = RGB(30, 144, 255)
    cornflowerBlue = RGB(100, 149, 237)
    royalBlue = RGB(65, 105, 225)
    blue = RGB(0, 0, 255)
    mediumBlue = RGB(0, 0, 205)
    darkBlue = RGB(0, 0, 139)
    navy = RGB(0, 0, 128)
    midnightBlue = RGB(25, 25, 112)
    
    cornsilk = RGB(255, 248, 220)
    blanchedDiamond = RGB(255, 235, 205)
    bisque = RGB(255, 228, 196)
    navajoWhite = RGB(255, 222, 173)
    wheat = RGB(245, 222, 179)
    burlyWood = RGB(222, 184, 135)
    tan = RGB(210, 180, 140)
    rosyBrown = RGB(188, 143, 143)
    sandyBrown = RGB(244, 164, 96)
    goldenrod = RGB(218, 165, 32)
    darkGoldenrod = RGB(184, 134, 11)
    peru = RGB(205, 133, 63)
    chocolate = RGB(210, 105, 63)
    saddleBrown = RGB(139, 69, 19)
    sienna = RGB(160, 82, 45)
    brown = RGB(165, 42, 42)
    maroon = RGB(128, 0, 0)
    
    white = RGB(255, 255, 255)
    snow = RGB(255, 250, 250)
    honeyDew = RGB(240, 255, 240)
    mintCream = RGB(244, 255, 250)
    azure = RGB(240, 255, 255)
    aliceBlue = RGB(240, 248, 255)
    ghostWhite = RGB(248, 248, 255)
    whiteSmoke = RGB(245, 245, 245)
    seaShell = RGB(255, 245, 238)
    beige = RGB(245, 245, 220)
    oldLace = RGB(253, 245, 230)
    floralWhite = RGB(255, 250, 240)
    ivory = RGB(255, 255, 240)
    antiqueWhite = RGB(250, 235, 215)
    linen = RGB(250, 240, 230)
    lavenderBlush = RGB(255, 240, 245)
    mistyRose = RGB(255, 228, 225)
    
    gainsboro = RGB(220, 220, 220)
    lightGray = RGB(211, 211, 211)
    silver = RGB(192, 192, 192)
    gray = RGB(128, 128, 128)
    dimGray = RGB(105, 105, 105)
    lightSlateGray = RGB(119, 136, 153)
    slateGray = RGB(112, 128, 144)
    darkSlateGray = RGB(47, 79, 79)
    black = RGB(0, 0, 0)
    
    # source: https://en.wikipedia.org/wiki/ANSI_escape_code#8-bit
    
    ### BELOW: 0.3.41
    mode256_0 = mode256_16 = black
    mode256_1 = RGB.fromValue(0x800000)
    mode256_2 = RGB.fromValue(0x008000)
    mode256_3 = RGB.fromValue(0x808000)
    mode256_4 = RGB.fromValue(0x000080)
    mode256_5 = RGB.fromValue(0x800080)
    mode256_6 = RGB.fromValue(0x008080)
    mode256_7 = RGB.fromValue(0xc0c0c0)
    mode256_8 = RGB.fromValue(0x808080)
    mode256_9 = mode256_196 = red
    mode256_10 = mode256_46 = lime
    mode256_11 = mode256_226 = yellow
    mode256_12 = mode256_21 = blue
    mode256_13 = mode256_201 = fuchsia
    mode256_14 = mode256_51 = aqua
    mode256_15 = mode256_231 = white
    ### BELOW: 0.3.48
    mode256_17 = RGB.fromValue(0x00005f)
    mode256_18 = RGB.fromValue(0x000087)
    mode256_19 = RGB.fromValue(0x0000af)
    mode256_20 = RGB.fromValue(0x0000d7)
    # 21 = html blue
    mode256_22 = RGB.fromValue(0x005f00)
    mode256_23 = RGB.fromValue(0x005f5f)
    mode256_24 = RGB.fromValue(0x005f87)
    mode256_25 = RGB.fromValue(0x005faf)
    mode256_26 = RGB.fromValue(0x005fd7)
    mode256_27 = RGB.fromValue(0x005fff)
    mode256_28 = RGB.fromValue(0x008700)
    mode256_29 = RGB.fromValue(0x00875f)
    mode256_30 = RGB.fromValue(0x008787)
    mode256_31 = RGB.fromValue(0x0087af)
    mode256_32 = RGB.fromValue(0x0087d7)
    mode256_33 = RGB.fromValue(0x0087ff)
    mode256_34 = RGB.fromValue(0x00af00)
    mode256_35 = RGB.fromValue(0x00af5f)
    mode256_36 = RGB.fromValue(0x00af87)
    mode256_37 = RGB.fromValue(0x00afaf)
    mode256_38 = RGB.fromValue(0x00afd7)
    mode256_39 = RGB.fromValue(0x00afff)
    mode256_40 = RGB.fromValue(0x00d700)
    mode256_41 = RGB.fromValue(0x00d75f)
    mode256_42 = RGB.fromValue(0x00d787)
    mode256_43 = RGB.fromValue(0x00d7af)
    mode256_44 = RGB.fromValue(0x00d7d7)
    mode256_45 = RGB.fromValue(0x00d7ff)
    # 46 = html lime
    mode256_47 = RGB.fromValue(0x00ff5f)
    mode256_48 = RGB.fromValue(0x00ff87)
    mode256_49 = RGB.fromValue(0x00ffaf)
    mode256_50 = RGB.fromValue(0x00ffd7)
    # 51 = html cyan/aqua
    ### BELOW: 0.3.58
    mode256_52 = RGB.fromValue(0x5f0000)
    mode256_53 = RGB.fromValue(0x5f005f)
    mode256_54 = RGB.fromValue(0x5f0087)
    mode256_55 = RGB.fromValue(0x5f00af)
    mode256_56 = RGB.fromValue(0x5f00d7)
    mode256_57 = RGB.fromValue(0x5f00ff)
    mode256_58 = RGB.fromValue(0x5f5f00)
    mode256_59 = RGB.fromValue(0x5f5f5f)
    mode256_60 = RGB.fromValue(0x5f5f87)
    mode256_61 = RGB.fromValue(0x5f5faf)
    mode256_62 = RGB.fromValue(0x5f5fd7)
    mode256_63 = RGB.fromValue(0x5f5fff)
    mode256_64 = RGB.fromValue(0x5f8700)
    mode256_65 = RGB.fromValue(0x5f875f)
    mode256_66 = RGB.fromValue(0x5f8787)
    mode256_67 = RGB.fromValue(0x5f87af)
    mode256_68 = RGB.fromValue(0x5f87d7)
    mode256_69 = RGB.fromValue(0x5f87ff)
    mode256_70 = RGB.fromValue(0x5faf00)
    mode256_71 = RGB.fromValue(0x5faf5f)
    mode256_72 = RGB.fromValue(0x5faf87)
    mode256_73 = RGB.fromValue(0x5fafaf)
    mode256_74 = RGB.fromValue(0x5fafd7)
    mode256_75 = RGB.fromValue(0x5fafff)
    mode256_76 = RGB.fromValue(0x5fd700)
    mode256_77 = RGB.fromValue(0x5fd75f)
    mode256_78 = RGB.fromValue(0x5fd787)
    mode256_79 = RGB.fromValue(0x5fd7af)
    mode256_80 = RGB.fromValue(0x5fd7d7)
    mode256_81 = RGB.fromValue(0x5fd7ff)
    mode256_82 = RGB.fromValue(0x5fff00)
    mode256_83 = RGB.fromValue(0x5fff5f)
    mode256_84 = RGB.fromValue(0x5fff87)
    mode256_85 = RGB.fromValue(0x5fffaf)
    mode256_86 = RGB.fromValue(0x5fffd7)
    mode256_87 = RGB.fromValue(0x5fffff)
    mode256_88 = RGB.fromValue(0x870000)
    mode256_89 = RGB.fromValue(0x87005f)
    mode256_90 = RGB.fromValue(0x870087)
    mode256_91 = RGB.fromValue(0x8700af)
    mode256_92 = RGB.fromValue(0x8700d7)
    mode256_93 = RGB.fromValue(0x8700ff)
    mode256_94 = RGB.fromValue(0x875f00)
    mode256_95 = RGB.fromValue(0x875f5f)
    mode256_96 = RGB.fromValue(0x875f87)
    mode256_97 = RGB.fromValue(0x875faf)
    mode256_98 = RGB.fromValue(0x875fd7)
    mode256_99 = RGB.fromValue(0x875fff)
    mode256_100 = RGB.fromValue(0x878700)
    mode256_101 = RGB.fromValue(0x87875f)
    mode256_102 = RGB.fromValue(0x878787)
    mode256_103 = RGB.fromValue(0x8787af)
    mode256_104 = RGB.fromValue(0x8787d7)
    mode256_105 = RGB.fromValue(0x8787ff)
    mode256_106 = RGB.fromValue(0x87af00)
    mode256_107 = RGB.fromValue(0x87af5f)
    mode256_108 = RGB.fromValue(0x87af87)
    mode256_109 = RGB.fromValue(0x87afaf)
    mode256_110 = RGB.fromValue(0x87afd7)
    mode256_111 = RGB.fromValue(0x87afff)
    mode256_112 = RGB.fromValue(0x87d700)
    mode256_113 = RGB.fromValue(0x87d75f)
    mode256_114 = RGB.fromValue(0x87d787)
    mode256_115 = RGB.fromValue(0x87d7af)
    mode256_116 = RGB.fromValue(0x87d7d7)
    mode256_117 = RGB.fromValue(0x87d7ff)
    mode256_118 = RGB.fromValue(0x87ff00)
    mode256_119 = RGB.fromValue(0x87ff5f)
    mode256_120 = RGB.fromValue(0x87ff87)
    mode256_121 = RGB.fromValue(0x87ffaf)
    mode256_122 = RGB.fromValue(0x87ffd7)
    mode256_123 = RGB.fromValue(0x87ffff)
    mode256_124 = RGB.fromValue(0xaf0000)
    mode256_125 = RGB.fromValue(0xaf005f)
    mode256_126 = RGB.fromValue(0xaf0087)
    mode256_127 = RGB.fromValue(0xaf00af)
    mode256_128 = RGB.fromValue(0xaf00d7)
    mode256_129 = RGB.fromValue(0xaf00ff)
    mode256_130 = RGB.fromValue(0xaf5f00)
    mode256_131 = RGB.fromValue(0xaf5f5f)
    mode256_132 = RGB.fromValue(0xaf5f87)
    mode256_133 = RGB.fromValue(0xaf5faf)
    mode256_134 = RGB.fromValue(0xaf5fd7)
    mode256_135 = RGB.fromValue(0xaf5fff)
    mode256_136 = RGB.fromValue(0xaf8700)
    mode256_137 = RGB.fromValue(0xaf875f)
    mode256_138 = RGB.fromValue(0xaf8787)
    mode256_139 = RGB.fromValue(0xaf87af)
    mode256_140 = RGB.fromValue(0xaf87d7)
    mode256_141 = RGB.fromValue(0xaf87ff)
    mode256_142 = RGB.fromValue(0xafaf00)
    mode256_143 = RGB.fromValue(0xafaf5f)
    mode256_144 = RGB.fromValue(0xafaf87)
    mode256_145 = RGB.fromValue(0xafafaf)
    mode256_146 = RGB.fromValue(0xafafd7)
    mode256_147 = RGB.fromValue(0xafafff)
    mode256_148 = RGB.fromValue(0xafd700)
    mode256_149 = RGB.fromValue(0xafd75f)
    mode256_150 = RGB.fromValue(0xafd787)
    mode256_151 = RGB.fromValue(0xafd7af)
    mode256_152 = RGB.fromValue(0xafd7d7)
    mode256_153 = RGB.fromValue(0xafd7ff)
    mode256_154 = RGB.fromValue(0xafff00)
    mode256_155 = RGB.fromValue(0xafff5f)
    mode256_156 = RGB.fromValue(0xafff87)
    mode256_157 = RGB.fromValue(0xafffaf)
    mode256_158 = RGB.fromValue(0xafffd7)
    mode256_159 = RGB.fromValue(0xafffff)
    mode256_160 = RGB.fromValue(0xd70000)
    mode256_161 = RGB.fromValue(0xd7005f)
    mode256_162 = RGB.fromValue(0xd70087)
    mode256_163 = RGB.fromValue(0xd700af)
    mode256_164 = RGB.fromValue(0xd700d7)
    mode256_165 = RGB.fromValue(0xd700ff)
    mode256_166 = RGB.fromValue(0xd75f00)
    mode256_167 = RGB.fromValue(0xd75f5f)
    mode256_168 = RGB.fromValue(0xd75f87)
    mode256_169 = RGB.fromValue(0xd75faf)
    mode256_170 = RGB.fromValue(0xd75fd7)
    mode256_171 = RGB.fromValue(0xd75fff)
    mode256_172 = RGB.fromValue(0xd78700)
    mode256_173 = RGB.fromValue(0xd7875f)
    mode256_174 = RGB.fromValue(0xd78787)
    mode256_175 = RGB.fromValue(0xd787af)
    mode256_176 = RGB.fromValue(0xd787d7)
    mode256_177 = RGB.fromValue(0xd787ff)
    mode256_178 = RGB.fromValue(0xd7af00)
    mode256_179 = RGB.fromValue(0xd7af5f)
    mode256_180 = RGB.fromValue(0xd7af87)
    mode256_181 = RGB.fromValue(0xd7afaf)
    mode256_182 = RGB.fromValue(0xd7afd7)
    mode256_183 = RGB.fromValue(0xd7afff)
    mode256_184 = RGB.fromValue(0xd7d700)
    mode256_185 = RGB.fromValue(0xd7d75f)
    mode256_186 = RGB.fromValue(0xd7d787)
    mode256_187 = RGB.fromValue(0xd7d7af)
    mode256_188 = RGB.fromValue(0xd7d7d7)
    mode256_189 = RGB.fromValue(0xd7d7ff)
    mode256_190 = RGB.fromValue(0xd7ff00)
    mode256_191 = RGB.fromValue(0xd7ff5f)
    mode256_192 = RGB.fromValue(0xd7ff87)
    mode256_193 = RGB.fromValue(0xd7ffaf)
    mode256_194 = RGB.fromValue(0xd7ffd7)
    mode256_195 = RGB.fromValue(0xd7ffff)
    # 196 = html red
    mode256_197 = RGB.fromValue(0xff005f)
    mode256_198 = RGB.fromValue(0xff0087)
    mode256_199 = RGB.fromValue(0xff00af)
    mode256_200 = RGB.fromValue(0xff00d7)
    # 201 = html fuchsia
    mode256_202 = RGB.fromValue(0xff5f00)
    mode256_203 = RGB.fromValue(0xff5f5f)
    mode256_204 = RGB.fromValue(0xff5f87)
    mode256_205 = RGB.fromValue(0xff5faf)
    mode256_206 = RGB.fromValue(0xff5fd7)
    mode256_207 = RGB.fromValue(0xff5fff)
    mode256_208 = RGB.fromValue(0xff8700)
    mode256_209 = RGB.fromValue(0xff875f)
    mode256_210 = RGB.fromValue(0xff8787)
    mode256_211 = RGB.fromValue(0xff87af)
    mode256_212 = RGB.fromValue(0xff87d7)
    mode256_213 = RGB.fromValue(0xff87ff)
    mode256_214 = RGB.fromValue(0xffaf00)
    mode256_215 = RGB.fromValue(0xffaf5f)
    mode256_216 = RGB.fromValue(0xffaf87)
    mode256_217 = RGB.fromValue(0xffafaf)
    mode256_218 = RGB.fromValue(0xffafd7)
    mode256_219 = RGB.fromValue(0xffafff)
    mode256_220 = RGB.fromValue(0xffd700)
    mode256_221 = RGB.fromValue(0xffd75f)
    mode256_222 = RGB.fromValue(0xffd787)
    mode256_223 = RGB.fromValue(0xffd7af)
    mode256_224 = RGB.fromValue(0xffd7d7)
    mode256_225 = RGB.fromValue(0xffd7ff)
    # 226 = html yellow
    mode256_227 = RGB.fromValue(0xffff5f)
    mode256_228 = RGB.fromValue(0xffff87)
    mode256_229 = RGB.fromValue(0xffffaf)
    mode256_230 = RGB.fromValue(0xffffd7)
    # 231 = html white
    ### BELOW: 0.3.41
    mode256_232 = RGB.fromValue(0x080808)
    mode256_233 = RGB.fromValue(0x121212)
    mode256_234 = RGB.fromValue(0x1c1c1c)
    mode256_235 = RGB.fromValue(0x262626)
    mode256_236 = RGB.fromValue(0x303030)
    mode256_237 = RGB.fromValue(0x3a3a3a)
    mode256_238 = RGB.fromValue(0x444444)
    mode256_239 = RGB.fromValue(0x4e4e4e)
    mode256_240 = RGB.fromValue(0x585858)
    mode256_241 = RGB.fromValue(0x626262)
    mode256_242 = RGB.fromValue(0x6c6c6c)
    mode256_243 = RGB.fromValue(0x767676)
    mode256_244 = mode256_8 # same color (0x808080)
    mode256_245 = RGB.fromValue(0x8a8a8a)
    mode256_246 = RGB.fromValue(0x949494)
    mode256_247 = RGB.fromValue(0x9e9e9e)
    mode256_248 = RGB.fromValue(0xa8a8a8)
    mode256_249 = RGB.fromValue(0xb2b2b2)
    mode256_250 = RGB.fromValue(0xbcbcbc)
    mode256_251 = RGB.fromValue(0xc6c6c6)
    mode256_252 = RGB.fromValue(0xd0d0d0)
    mode256_253 = RGB.fromValue(0xdadada)
    mode256_254 = RGB.fromValue(0xe4e4e4)
    mode256_255 = RGB.fromValue(0xeeeeee)
    
    __all__ = [k for k in locals() if not k.startswith("_")] # >= 0.3.41

Colours = Colors

class Color:
    """
    @lifetime >= 0.3.26rc1 \\
    https://aveyzan.xyz/aveytense#aveytense.Color
    
    Deputy of experimental class `aveytense.extensions.ANSIColor` (>= 0.3.24; < 0.3.26rc1).
    
    This class uses ANSI escape code for color purposes.

    Use `str()` to return colored string.
    
    Modulo operator (`%`) allows to change the font style. The right operand must be \\
    an appropriate constant or lowercased string literal (for single font styles).
    Examples::
    
        Color("Tense") % Color.BOLD
        Color("Countryside!", 8, 0o105) % Color.ITALIC # italic, blue text
        Color("Creativity!", 24, 0xc0ffee) % Color.BOLD # bold, c0ffee hex code text
        Color("Illusive!", 24, 0, 0xc0ffee) % Color.BOLD # bold, c0ffee hex code background, black text
    

    Since 0.3.26rc2 you can use constants, which grant more than one font style simultaneously, like::
    
        Color("Lines!", 8, 93) % Color.UOLINE # lines above and below text

    **Warning**: 24-bit colors load longer than colors from lower bit shelves. In this case it is \\
    recommended to stick to 8-bit colors, but if there isn't a satisfying color, 24-bit color support \\
    will be kept. It is also somewhat a reason of `RGB` and `CMYK` colors existence.
    """
    __fg = None
    __bg = None
    if False: # 0.3.27
        __un = None
    __text = ""
    __bits = 8 # 24 to 0.3.34
    
    select = Colors
    """@lifetime >= 0.3.41. Alias to `~.Colors`"""

    NORMAL = _ColorStyling.NORMAL
    "@lifetime >= 0.3.26rc1. Mere text"
    
    BOLD = _ColorStyling.BOLD
    "@lifetime >= 0.3.26rc1. Text becomes bold"
    
    FAINT = _ColorStyling.FAINT
    "@lifetime >= 0.3.26rc1. Also works as 'decreased intensity' or 'dim'"
    
    ITALIC = _ColorStyling.ITALIC
    "@lifetime >= 0.3.26rc1. Text becomes oblique. Not widely supported"
    
    UNDERLINE = _ColorStyling.UNDERLINE
    "@lifetime >= 0.3.26rc1. Text becomes underlined. Marked *experimental* as experimenting with underline colors, but normally it is OK to use"
    
    SLOW_BLINK = _ColorStyling.SLOW_BLINK
    "@lifetime >= 0.3.26rc1. Text will blink for less than 150 times per minute"
    
    RAPID_BLINK = _ColorStyling.RAPID_BLINK
    "@lifetime >= 0.3.26rc1. Text will blink for more than 150 times per minute. Not widely supported"
    
    REVERSE = _ColorStyling.REVERSE
    "@lifetime >= 0.3.26rc2. Swap text and background colors"
    
    HIDE = _ColorStyling.HIDE
    "@lifetime >= 0.3.26rc1. Text becomes transparent"
    
    STRIKE = _ColorStyling.STRIKE
    "@lifetime >= 0.3.26rc1. Text becomes crossed out"
    
    DOUBLE_UNDERLINE = _ColorStyling.DOUBLE_UNDERLINE
    "@lifetime >= 0.3.26rc2. Text becomes doubly underlined"
    
    # PROPORTIONAL = _ColorStyling.PROPORTIONAL
    # "@lifetime >= 0.3.26rc1; < 0.3.26rc2. Proportional spacing. *Experimental*"
    
    FRAME = _ColorStyling.FRAME
    "@lifetime >= 0.3.26rc1. Implemented in mintty as 'emoji variation selector'"
    
    ENCIRCLE = _ColorStyling.ENCIRCLE
    "@lifetime >= 0.3.26rc1. Implemented in mintty as 'emoji variation selector'"
    
    OVERLINE = _ColorStyling.OVERLINE
    "@lifetime >= 0.3.26rc1. Text becomes overlined"
    
    SUPERSCRIPT = _ColorStyling.SUPERSCRIPT
    "@lifetime >= 0.3.26rc2. Text becomes superscripted (implemented in mintty only)"
    
    SUBSCRIPT = _ColorStyling.SUBSCRIPT
    "@lifetime >= 0.3.26rc2. Text becomes subscripted (implemented in mintty only)"
    
    # 2x
    BOLD_ITALIC = _ColorAdvancedStyling.BOLD_ITALIC
    "@lifetime >= 0.3.26rc2. Text becomes bold and oblique"
    
    BOLD_UNDERLINE = _ColorAdvancedStyling.BOLD_UNDERLINE
    "@lifetime >= 0.3.26rc2. Text becomes bold and underlined"
    
    BOLD_STRIKE = _ColorAdvancedStyling.BOLD_STRIKE
    "@lifetime >= 0.3.26rc2. Text becomes bold and crossed out"
    
    BOLD_OVERLINE = _ColorAdvancedStyling.BOLD_OVERLINE
    "@lifetime >= 0.3.26rc2. Text becomes bold and overlined"
    
    ITALIC_UNDERLINE = _ColorAdvancedStyling.ITALIC_UNDERLINE
    "@lifetime >= 0.3.26rc2. Text becomes oblique and underlined"
    
    ITALIC_STRIKE = _ColorAdvancedStyling.ITALIC_STRIKE
    "@lifetime >= 0.3.26rc2. Text becomes oblique and crossed out"
    
    ITALIC_OVERLINE = _ColorAdvancedStyling.ITALIC_OVERLINE
    "@lifetime >= 0.3.26rc2. Text becomes oblique and overlined"
    
    UNDERLINE_STRIKE = _ColorAdvancedStyling.UNDERLINE_STRIKE
    "@lifetime >= 0.3.26rc2. Text becomes underlined and crossed out"
    
    UOLINE = _ColorAdvancedStyling.UOLINE
    "@lifetime >= 0.3.26rc2. Alias to underline-overline. Text gets lines above and below"
    
    STRIKE_OVERLINE = _ColorAdvancedStyling.STRIKE_OVERLINE
    "@lifetime >= 0.3.26rc2. Text becomes crossed out and overlined"
    
    # 3x
    BOLD_ITALIC_UNDERLINE = _ColorAdvancedStyling.BOLD_ITALIC_UNDERLINE
    "@lifetime >= 0.3.26rc2. Text becomes bold, oblique and underlined"
    
    BOLD_ITALIC_STRIKE = _ColorAdvancedStyling.BOLD_ITALIC_STRIKE
    "@lifetime >= 0.3.26rc2"
    
    BOLD_ITALIC_OVERLINE = _ColorAdvancedStyling.BOLD_ITALIC_OVERLINE
    "@lifetime >= 0.3.26rc2"
    
    BOLD_UNDERLINE_STRIKE = _ColorAdvancedStyling.BOLD_UNDERLINE_STRIKE
    "@lifetime >= 0.3.26rc2"
    
    BOLD_UOLINE = _ColorAdvancedStyling.BOLD_UOLINE
    "@lifetime >= 0.3.26rc2"
    
    ITALIC_UNDERLINE_STRIKE = _ColorAdvancedStyling.ITALIC_UNDERLINE_STRIKE
    "@lifetime >= 0.3.26rc2"
    
    ITALIC_UOLINE = _ColorAdvancedStyling.ITALIC_UOLINE
    "@lifetime >= 0.3.26rc2"
    
    ITALIC_STRIKE_OVERLINE = _ColorAdvancedStyling.ITALIC_STRIKE_OVERLINE
    "@lifetime >= 0.3.26rc2"
    
    STRIKE_UOLINE = _ColorAdvancedStyling.STRIKE_UOLINE
    "@lifetime >= 0.3.26rc2"
        
    def __prepare_return(self):
        
        return _colorize(self.__text, self.__bits, self.__fg, self.__bg, self.__itu)
        
    def __init__(self, text: __.Union[str, _util.MutableString], /, bits: _Bits = 8, foregroundColor: _Color = None, backgroundColor: _Color = None, ituFormat: bool = False): # slash since 0.3.26rc2
        """
        @lifetime >= 0.3.26rc1
        
        ## Parameters
        - `text` - string to be colored. Required parameter
        - `bits` - number of bits, possible values: 3, 4, 8, 24. Defaults to 24 (since 0.3.26rc2 - 8)
        - `foregroundColor` - color of the foreground (text). String/integer/`None`. Defaults to `None`
        - `backgroundColor` - color of the background. String/integer/`None`. Defaults to `None`
        - `ituFormat` (since 0.3.58) - Format for ITU T.416 Information technology. Defaults to `False`
        """
        _os.system("color")
        
        _params = _get_all_params(self.__init__)
        
        # 0.3.41: Prevent ANSI escape code to be passed to the text (27.02.2025)
        # 0.3.45: Add support for ~.util.MutableString
        if not isinstance(text, (str, _util.MutableString)) or ((Tense.isString(text) and Tense.test(text, r"\033\[\d(;\d)*m")) or (isinstance(text, _util.MutableString) and Tense.test(text.value, r"\033\[\d(;\d)*m"))):
            error = TypeError("expected string value for '{}' parameter".format(_params[0]))
            raise error
        
        if not Tense.isInteger(bits) or (Tense.isInteger(bits) and bits not in (3, 4, 8, 24)):
            error = TypeError("expected integer value: 3, 4, 8 or 24, for '{}' parameter".format(_params[1]))
            raise error
        
        for e in (foregroundColor, backgroundColor):
            
            # Issue caught and fixed on 0.3.37 (GeckoGM)
            # 0.3.38: Fixed for RGB instances
            # Unfortunately, support for 'types.UnionType' is provided on 3.10, and the project's minimal version is 3.9,
            # so we need to change it (0.3.41); it was an issue with ~.Tense.isNone(). (0.3.41)
            
            if not isinstance(e, (int, str, RGB, __.NoneType)):
                error = TypeError("expected integer, string or 'None' value for both foreground and background color parameters")
                raise error
            
            elif Tense.isString(e) and (
                # changing this order may cause easier error
                not Tense.isHexadecimal(e) and
                not Tense.isNumeric(e) and
                not Tense.isOctal(e) and
                not Tense.isBinary(e)
            ):
                error = TypeError("malformed string in either foreground or background color parameters, expected clean binary, decimal, hexademical or octal string")
                raise error
            
            elif bits == 24 and not Tense.isNone(e) and (
                Tense.isInteger(e) and e not in abroad(0x1000000) or
                Tense.isString(e) and _int_conversion(e) not in abroad(0x1000000) or
                isinstance(e, RGB) and int(e) not in abroad(0x1000000)
            ):
                error = ValueError("for 24-bit colors, expected \"RGB\" class instance of integer value, integer or string value in range 0-16777215")
                raise error
            
            elif bits == 8 and not Tense.isNone(e) and (
                Tense.isInteger(e) and e not in abroad(0x100) or
                Tense.isString(e) and _int_conversion(e) not in abroad(0x100) or isinstance(e, RGB)
            ):
                error = ValueError("for 8-bit colors, expected integer or string value in range 0-255. Cannot be used with \"RGB\" class instance")
                raise error
            
            elif bits == 4 and not Tense.isNone(e) and (
                Tense.isInteger(e) and e not in abroad(0x10) or
                Tense.isString(e) and _int_conversion(e) not in abroad(0x10) or isinstance(e, RGB)
            ):
                error = ValueError("for 4-bit colors, expected integer or string value in range 0-15. Cannot be used with \"RGB\" class instance")
                raise error
            
            elif bits == 3 and not Tense.isNone(e) and (
                Tense.isInteger(e) and e not in abroad(0x8) or
                Tense.isString(e) and _int_conversion(e) not in abroad(0x8) or isinstance(e, RGB)
            ):
                error = ValueError("for 3-bit colors, expected integer or string value in range 0-7. Cannot be used with \"RGB\" class instance")
                raise error
        
        _tmp = _inspect.currentframe().f_back.f_lineno
        self.__frame = _tmp if type(_tmp) is int else -1
        self.__text = text if Tense.isString(text) else text.value # 0.3.45
        self.__bits = bits
        self.__fg = foregroundColor if Tense.isInteger(foregroundColor) else _int_conversion(foregroundColor) if Tense.isString(foregroundColor) else int(foregroundColor) if isinstance(foregroundColor, RGB) else None
        self.__bg = backgroundColor if Tense.isInteger(backgroundColor) else _int_conversion(backgroundColor) if Tense.isString(backgroundColor) else int(backgroundColor) if isinstance(backgroundColor, RGB) else None
        self.__itu = ituFormat
    
    def clear(self):
        """
        @lifetime >= 0.3.26rc1
        
        Clear every color for foreground, background and underline. Should \\
        be used before `setBits()` method invocation to avoid conflicts. \\
        By default bits value is reset to 24. Since 0.3.27b1 - 8.
        """
        self.__fg = None
        self.__bg = None
        if False: # 0.3.27
            self.__un = None
        self.__bits = 8
        return self
    
    def setBits(self, bits: _Bits = 8, /):
        """
        @lifetime >= 0.3.26rc1

        Possible values: 3, 4, 8, 24. Default is 24. \\
        Since 0.3.26rc2 default value is 8.
        """
        
        if not Tense.isInteger(bits) or (Tense.isInteger(bits) and bits not in (3, 4, 8, 24)):
            error = TypeError("expected integer value: 3, 4, 8 or 24, for 'bits' parameter")
            raise error
        
        # for e in (self.__fg, self.__bg, self.__un): ### removed 0.3.27
        for e in (self.__fg, self.__bg):
            
            if e is not None:
                
                if bits == 24 and e not in abroad(0x1000000):
                    error = ValueError("internal conflict caught while setting 'bits' value to 24. One of foreground or background values is beyond range 0-16777215. To prevent this conflict, use method 'Color.clear()'.")
                    raise error
                
                elif bits == 8 and e not in abroad(0x100):
                    error = ValueError("internal conflict caught while setting 'bits' value to 8. One of foreground or background values is beyond range 0-255. To prevent this conflict, use method 'Color.clear()'.")
                    raise error
                
                elif bits == 4 and e not in abroad(0x10):
                    error = ValueError("internal conflict caught while setting 'bits' value to 4. One of foreground or background values is beyond range 0-15. To prevent this conflict, use method 'Color.clear()'.")
                    raise error
                
                elif bits == 3 and e not in abroad(0x8):
                    error = ValueError("internal conflict caught while setting 'bits' value to 3. One of foreground or background values is beyond range 0-7. To prevent this conflict, use method 'Color.clear()'.")
                    raise error
                
        self.__bits = bits
    
    def setForegroundColor(self, color: _Color = None, /):
        """
        @lifetime >= 0.3.26rc1
        
        Set foreground color manually.
        """
        _c = color if Tense.isInteger(color) or color is None else _int_conversion(color) if Tense.isString(color) else int(color) if isinstance(color, RGB) else None
        
        if _c is not None:
            
            if self.__bits == 3 and _c not in abroad(0x8):
                error = ValueError(f"for 3-bit colors, expected integer or string value in range 0-7")
                raise error
            
            elif self.__bits == 4 and _c not in abroad(0x10):
                error = ValueError(f"for 4-bit colors, expected integer or string value in range 0-15")
                raise error
            
            elif self.__bits == 8 and _c not in abroad(0x100):
                error = ValueError(f"for 8-bit colors, expected integer or string value in range 0-255")
                raise error
            
            elif self.__bits == 24 and _c not in abroad(0x1000000):
                error = ValueError(f"for 24-bit colors, expected integer, string or RGB/CMYK tuple value in range 0-16777215")
                raise error
            
            else:
                error = ValueError(f"internal 'bits' variable value is not one from following: 3, 4, 8, 24")
                raise error
            
        self.__fg = _c
        return self
    
    def setBackgroundColor(self, color: _Color = None, /):
        """
        @lifetime >= 0.3.26rc1
        
        Set background color manually.
        """
        _c = color if Tense.isInteger(color) or color is None else _int_conversion(color) if Tense.isString(color) else int(color) if isinstance(color, RGB) else None
        
        if _c is not None:
            
            if self.__bits == 3 and _c not in abroad(0x8):
                error = ValueError(f"for 3-bit colors, expected integer or string value in range 0-7")
                raise error
            
            elif self.__bits == 4 and _c not in abroad(0x10):
                error = ValueError(f"for 4-bit colors, expected integer or string value in range 0-15")
                raise error
            
            elif self.__bits == 8 and _c not in abroad(0x100):
                error = ValueError(f"for 8-bit colors, expected integer or string value in range 0-255")
                raise error
            
            elif self.__bits == 24 and _c not in abroad(0x1000000):
                error = ValueError(f"for 24-bit colors, expected integer, string or RGB/CMYK tuple value in range 0-16777215")
                raise error
            
            else:
                error = ValueError(f"internal 'bits' variable value is not one from following: 3, 4, 8, 24")
                raise error
            
        self.__bg = _c
        return self
    
    def __str__(self):
        """@lifetime >= 0.3.34. Receive colored string"""
        return self.__prepare_return()
    
    def __repr__(self):
        """@lifetime >= 0.3.35"""
        return "<<'{}.{}' object :: {}(\"{}\")> defined in line {}>".format(
            self.__module__,
            type(self).__name__,
            type(self).__name__,
            self.__text,
            self.__frame
        )
    
    def __mod__(self, other: _ColorStylingType):
        """
        @lifetime >= 0.3.26rc1
        
        Further styling. Use constant that is in `__constants__` attribute.
        """
        # below: since 0.3.26rc1
        if other in (self.NORMAL,):
            return self.__prepare_return()
        
        elif other in (self.BOLD,):
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[1;", self.__itu), self.__prepare_return())
        
        elif other in (self.FAINT,):
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[2;", self.__itu), self.__prepare_return())
        
        elif other in (self.ITALIC,):
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[3;", self.__itu), self.__prepare_return())
        
        elif other in (self.UNDERLINE,):
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[4;", self.__itu), self.__prepare_return())
        
        elif other in (self.SLOW_BLINK,):
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[5;", self.__itu), self.__prepare_return())
        
        elif other in (self.RAPID_BLINK,):
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[6;", self.__itu), self.__prepare_return())
        
        # below: since 0.3.26rc2
        elif other in (self.REVERSE,):
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[7;", self.__itu), self.__prepare_return())
        
        # below: since 0.3.26rc1
        elif other in (self.HIDE,):
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[8;", self.__itu), self.__prepare_return())
        
        elif other in (self.STRIKE,):
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[9;", self.__itu), self.__prepare_return())
        
        elif other in (self.DOUBLE_UNDERLINE,):
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[21;", self.__itu), self.__prepare_return())
        
        elif other in (self.FRAME,):
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[51;", self.__itu), self.__prepare_return())
        
        elif other in (self.ENCIRCLE,):
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[52;", self.__itu), self.__prepare_return())
        
        elif other in (self.OVERLINE,):
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[53;", self.__itu), self.__prepare_return())
        
        # below: since 0.3.26rc2
        elif other in (self.SUPERSCRIPT,):
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[73;", self.__itu), self.__prepare_return())
        
        elif other in (self.SUBSCRIPT,):
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[74;", self.__itu), self.__prepare_return())
        # 2x; since 0.3.26rc2
        elif other == self.BOLD_ITALIC:
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[1;3;", self.__itu), self.__prepare_return())
        
        elif other == self.BOLD_UNDERLINE:
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[1;4;", self.__itu), self.__prepare_return())
        
        elif other == self.BOLD_STRIKE:
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[1;9;", self.__itu), self.__prepare_return())
        
        elif other == self.BOLD_OVERLINE:
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[1;53;", self.__itu), self.__prepare_return())
        
        elif other == self.ITALIC_UNDERLINE:
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[3;4;", self.__itu), self.__prepare_return())
        
        elif other == self.ITALIC_STRIKE:
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[3;9;", self.__itu), self.__prepare_return())
        
        elif other == self.ITALIC_OVERLINE:
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[3;53;", self.__itu), self.__prepare_return())
        
        elif other == self.UNDERLINE_STRIKE:
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[4;9;", self.__itu), self.__prepare_return())
        
        elif other == self.UOLINE:
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[4;53;", self.__itu), self.__prepare_return())
        
        elif other == self.STRIKE_OVERLINE:
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[9;53;", self.__itu), self.__prepare_return())
        
        # 3x; since 0.3.26rc2
        elif other == self.BOLD_ITALIC_UNDERLINE:
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[1;3;4;", self.__itu), self.__prepare_return())
        
        elif other == self.BOLD_ITALIC_STRIKE:
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[1;3;9;", self.__itu), self.__prepare_return())
        
        elif other == self.BOLD_ITALIC_OVERLINE:
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[1;3;53;", self.__itu), self.__prepare_return())
        
        elif other == self.BOLD_UNDERLINE_STRIKE:
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[1;4;9;", self.__itu), self.__prepare_return())
        
        elif other == self.BOLD_UOLINE:
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[1;4;53;", self.__itu), self.__prepare_return())
        
        elif other == self.ITALIC_UNDERLINE_STRIKE:
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[3;4;9;", self.__itu), self.__prepare_return())
        
        elif other == self.ITALIC_UOLINE:
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[3;4;53;", self.__itu), self.__prepare_return())
        
        elif other == self.ITALIC_STRIKE_OVERLINE:
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[3;9;53;", self.__itu), self.__prepare_return())
        
        elif other == self.STRIKE_UOLINE:
            return _re.sub(r"^\x1b\[", _itu_perform("\x1b[4;9;53;", self.__itu), self.__prepare_return())
        
        else:
            
            if True: # >= 0.3.27
                error = TypeError("expected one from following constant values as a right operand: " + repr(self.__constants__) + " or a specific lowercased string literal when single font style was meant to be applied")
                
            else: # < 0.3.27
                error = TypeError(
                    "Expected any from constant values: " + repr(self.__constants__) + ". You are discouraged to do common operations on these constants, like union as in case of regular expression flags, to satisfy this requirement, because it "
                    "won't warrant that returned string will be styled as thought"
                )
                
            raise error
        
    @staticmethod
    def mix(text: str, /, bits: _Bits, colorIds: __.AVT_Iterable[__.Union[int, RGB]], style: __.Optional[_ColorStylingType] = None, ituFormat: bool = False, reverse: bool = True):
        """
        @lifetime >= 0.3.58
        
        ```
        Color.mix("Gradient?", 8, (51, 87, 123, 159, 195, 231), style)
        Color.mix("Gradient?", 8, (51, 87, 123, 159, 195, 231, 195, 159, 123), style)
        ```
        
        are the same as
        
        ```
        str(Color("G", 8, 51) % style) + \\
        str(Color("r", 8, 87) % style) + \\
        str(Color("a", 8, 123) % style) + ... + \\
        str(Color("?", 8, 123))
        ```
        """
        
        if not Tense.isString(text):
            error = TypeError("expected a string")
            raise error
        
        if bits not in (3, 4, 8, 24):
            error = TypeError("parameter 'bits' can only hold value from following: 3, 4, 8, 24")
            raise error
        
        if not Tense.isIterable(colorIds) or (Tense.isIterable(colorIds) and not Tense.isList(list(colorIds), (int, RGB))):
            error = TypeError("expected an iterable object with positive integers")
            raise error
        
        if reckon(colorIds) in (0, 1):
            error = ValueError("expected a non-empty iterable object with at least 2 integers")
            raise error
        
        if not isinstance(style, (_ColorStyling, _ColorAdvancedStyling)) and style is not None:
            error = TypeError("expected a proper style from 'Color', or 'None'")
            raise error
        
        foregroundColorIds = [(e if Tense.isInteger(e) else int(e)) for e in colorIds]
        result = ""
        space = ["\x20"][0] # prevent 'typing.LiteralString'; U+0020 is keyword space character
        whitespacesCount = 0
        whitespaces = constants.STRING_WHITESPACE + space + "\xa0"
        
        for c in whitespaces:
            whitespacesCount += text.count(c)
        
        if reckon(text) > reckon(foregroundColorIds):
            
            _foreground = [0]
            _foreground.clear()
            _foreground_tmp = 1
            
            while _foreground_tmp < reckon(text) - whitespacesCount:
                
                if reverse:
                
                    if _foreground_tmp % 2 == 0:
                        _foreground.extend(Tense.reverse(foregroundColorIds)[1:-1])
                        
                    else:
                        _foreground.extend(foregroundColorIds)
                        
                else:
                    _foreground.extend(foregroundColorIds)
                
                _foreground_tmp += 1
            
            _foreground = _foreground[: reckon(text) - whitespacesCount]
            
        else:
            _foreground = foregroundColorIds[: reckon(text) - whitespacesCount]
            
        nextI = 0
        
        for i in abroad(text):
            
            if text[i] not in whitespaces:
                result += Tense.removeSuffix(Color(text[i], bits, _foreground[nextI], None, ituFormat) % (style if style is not None else Color.NORMAL), "\x1b[0m")
                nextI += 1
                
            else:
                result += space[0]

        return result + "\x1b[0m"
        
    __all__ = [k for k in locals() if not k.startswith("_")]
    "@lifetime >= 0.3.26rc2. Returns list of all non-underscore-preceded members of class `~.Color`"
        
    __dir__ = lambda self: __all__
    "@lifetime >= 0.3.26rc2"
    
    __constants__ = [n for n in __all__ if n.isupper()]
    """
    @lifetime >= 0.3.26rc2

    Returns list of constants. These can be used as right operand for `%` operator. \\
    They are sorted as in ANSI escape code table, in ascending order
    """
    
Colour: extensions.TypeAlias = Color
"""
@lifetime >= 0.3.37: type alias `aveytense.Colour`
"""

__all__ = sorted([n for n in globals() if n[:1] != "_"])
__all_deprecated__ = sorted([n for n in globals() if hasattr(globals()[n], "__deprecated__")])
"""
@since 0.3.41

Returns all deprecated declarations within this module.
"""

def __dir__():
    return __all__

if __name__ == "__main__":
    error = RuntimeError("Import-only module")
    raise error