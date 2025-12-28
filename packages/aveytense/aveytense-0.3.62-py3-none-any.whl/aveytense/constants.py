"""
**AveyTense Constants** \n
@lifetime >= 0.3.26rc3 \\
© 2024-Present Aveyzan // License: MIT \\
https://aveyzan.xyz/aveytense#aveytense.constants

Constants wrapper for AveyTense. Extracted from former `tense.tcs` module
"""
from __future__ import annotations
from decimal import Decimal

from ._collection._constants import (
    AbroadHexMode as _AbroadHexMode,
    ProbabilityLength as _ProbabilityLength,
    ModeSelection as _ModeSelection
)

_ModeSelection

#################################### ENUM CONSTANTS ####################################

ABROAD_HEX_INCLUDE = _AbroadHexMode.INCLUDE # 0.3.35
ABROAD_HEX_HASH = _AbroadHexMode.HASH # 0.3.35
ABROAD_HEX_EXCLUDE = _AbroadHexMode.EXCLUDE # 0.3.35

STRING_LOWER = "abcdefghijklmnopqrstuvwxyz" # 0.3.36
STRING_UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" # 0.3.36
STRING_LETTERS = STRING_LOWER + STRING_UPPER # 0.3.36
STRING_HEXADECIMAL = "0123456789abcdefABCDEF" # 0.3.36
STRING_DIGITS = "0123456789" # 0.3.36
STRING_OCTAL = "01234567" # 0.3.36
STRING_BINARY = "01" # 0.3.36
STRING_SPECIAL = r"""`~!@#$%^&*()-_=+[]{};:'"\|,.<>/?""" # 0.3.36
STRING_WHITESPACE = "\n\t\r\v\f" # 0.3.57

RGB_MIN = 0 # 0.3.37
RGB_MAX = (1 << 24) - 1 # 0.3.37

#################################### NUMBER CONSTANTS ####################################

# JavaScript
# >= 0.3.26b3; < 0.3.53; >= 0.3.57
# NOTE: 'JS_MIN_VALUE' constant value won't be displayed exactly as-is as a float object, it
# will comply with JavaScript's approximate value 5e-324 (from formula 2 ** -1074), so using
# 'decimal.Decimal' in this case.
JS_MIN_SAFE_INTEGER = -((1 << 53) - 1) 
JS_MAX_SAFE_INTEGER = ((1 << 53) - 1)
JS_MIN_VALUE = Decimal(2 ** -1074)
JS_MAX_VALUE = (1 << 1024) - (1 << 971)

# Borrowed from C/C++ (8-128 bits). 128-bit integer is compiler specific.
# Going above 14287 bits ('(1 << N) - 1' where N > 14287) will require
# exceeding the 4300 digit display limit with 'sys.set_int_max_str_digits'.
# This is set to 0 by default in AveyTense (see __init__.py file) whether
# this function is defined, but may not work on older versions of Python
# preceding 3.11. In this case hasattr() is used.
UINT8_MIN = UINT16_MIN = UINT32_MIN = UINT64_MIN = UINT128_MIN = UINT256_MIN = \
UINT512_MIN = UINT1024_MIN = UINT2048_MIN = UINT4096_MIN = UINT8192_MIN = 0 # 0.3.57 (all)
UINT8_MAX = (1 << (1 << 3)) - 1 # 0.3.57
UINT16_MAX = (1 << (1 << 4)) - 1 # 0.3.57
UINT32_MAX = (1 << (1 << 5)) - 1 # 0.3.57
UINT64_MAX = (1 << (1 << 6)) - 1 # 0.3.57
UINT128_MAX = (1 << (1 << 7)) - 1 # 0.3.57
UINT256_MAX = (1 << (1 << 8)) - 1 # 0.3.57
UINT512_MAX = (1 << (1 << 9)) - 1 # 0.3.57
UINT1024_MAX = (1 << (1 << 10)) - 1 # 0.3.57
UINT2048_MAX = (1 << (1 << 11)) - 1 # 0.3.57
UINT4096_MAX = (1 << (1 << 12)) - 1 # 0.3.57
UINT8192_MAX = (1 << (1 << 13)) - 1 # 0.3.57

INT8_MIN = -(1 << ((1 << 3) - 1)) # 0.3.57
INT8_MAX = (1 << ((1 << 3) - 1)) - 1 # 0.3.57
INT16_MIN = -(1 << ((1 << 4) - 1)) # 0.3.57
INT16_MAX = (1 << ((1 << 4) - 1)) - 1 # 0.3.57
INT32_MIN = -(1 << ((1 << 5) - 1)) # 0.3.57
INT32_MAX = (1 << ((1 << 5) - 1)) - 1 # 0.3.57
INT64_MIN = -(1 << ((1 << 6) - 1)) # 0.3.57
INT64_MAX = (1 << ((1 << 6) - 1)) - 1 # 0.3.57
INT128_MIN = -(1 << ((1 << 7) - 1)) # 0.3.57
INT128_MAX = (1 << ((1 << 7) - 1)) - 1 # 0.3.57
INT256_MIN = -(1 << ((1 << 8) - 1)) # 0.3.57
INT256_MAX = (1 << ((1 << 8) - 1)) - 1 # 0.3.57
INT512_MIN = -(1 << ((1 << 9) - 1)) # 0.3.57
INT512_MAX = (1 << ((1 << 9) - 1)) - 1 # 0.3.57
INT1024_MIN = -(1 << ((1 << 10) - 1)) # 0.3.57
INT1024_MAX = (1 << ((1 << 10) - 1)) - 1 # 0.3.57
INT2048_MIN = -(1 << ((1 << 11) - 1)) # 0.3.57
INT2048_MAX = (1 << ((1 << 11) - 1)) - 1 # 0.3.57
INT4096_MIN = -(1 << ((1 << 12) - 1)) # 0.3.57
INT4096_MAX = (1 << ((1 << 12) - 1)) - 1 # 0.3.57
INT8192_MIN = -(1 << ((1 << 13) - 1)) # 0.3.57
INT8192_MAX = (1 << ((1 << 13) - 1)) - 1 # 0.3.57

SIZE_MAX = (_ProbabilityLength.MAX.value + 1) * 2 - 1 # 0.3.57
SSIZE_MAX = _ProbabilityLength.MAX.value # 0.3.57; sys.maxsize

del Decimal # not for export

__all__ = [k for k in globals() if not k.startswith("_")]
"""
@lifetime >= 0.3.41
"""
__all_deprecated__ = sorted([n for n in globals() if hasattr(globals()[n], "__deprecated__")])
"""
@lifetime >= 0.3.41

Returns all deprecated declarations within this module.
"""

if __name__ == "__main__":
    error = RuntimeError("Import-only module")
    raise error