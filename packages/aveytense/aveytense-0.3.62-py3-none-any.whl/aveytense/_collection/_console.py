"""
@lifetime >= 0.3.54 \\
© 2024-Present Aveyzan Mammoth // License: MIT

This internal module contains functions to be used for commands prefixed with `aveytense-`

Not in use in public scope.
"""

import sys as _sys
from . import _version

# >= 0.3.54
def upgrade(): # pyright: ignore[reportUnusedFunction]
    """
    @lifetime >= 0.3.54
    
    Used for command `aveytense-upgrade` - alias for `pip install --upgrade aveytense`
    """
    import subprocess
    
    # Unix and MacOS use 'python3', Windows - 'py'
    if _sys.platform == "win32":
        _py = "py"
    else:
        _py = "python3"
    
    subprocess.run([_sys.executable, _py, "-m", "pip", "install", "--upgrade", "aveytense"])
    
# >= 0.3.54
def version(): # pyright: ignore[reportUnusedFunction]
    """
    @lifetime >= 0.3.54
    
    Used for command `aveytense-version`
    """
    
    print(_version.VERSION_INFO)