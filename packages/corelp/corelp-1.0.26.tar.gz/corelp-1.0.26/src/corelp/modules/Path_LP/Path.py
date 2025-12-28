#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date          : 2025-09-02
# Author        : Lancelot PINCET
# GitHub        : https://github.com/LancelotPincet
# Library       : coreLP
# Module        : Path

"""
This function is a wrapper around the pathlib.Path and returns a compatible Path with a windows path copied inside Linux (for WSL)
"""



# %% Libraries
from pathlib import Path as PathlibPath
import os



# %% Detect if running inside WSL
def _is_wsl() -> bool:
    """True if WSL."""
    if os.name != "posix":
        return False
    try:
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    except FileNotFoundError:
        return False


IS_WSL = _is_wsl()


# %% Function
def Path(path, *args, **kwargs) :
    '''
    This function is a wrapper around the pathlib.Path and returns a compatible Path with a windows path copied inside Linux (for WSL)
    
    Parameters
    ----------
    path : str of pathlib.Path
        path string to convert to Path.

    Returns
    -------
    path : pathlib.Path
        compatible Path.

    Examples
    --------
    >>> Path("C:\\Users\\Name\\Documents")
    PosixPath('/mnt/c/Users/Name/Documents')   # under WSL
    >>> Path("/home/user/project")
    PosixPath('/home/user/project')            # under Linux
    >>> Path("C:\\Users\\Name\\Documents")
    WindowsPath('C:/Users/Name/Documents')     # under Windows
    '''

    # Windows case → no conversion
    if os.name == "nt":
        return PathlibPath(path, *args, **kwargs)

    # Conversion in string
    pathstring = str(path).replace("\\", "/")

    # If not in WSL → no touching
    if not IS_WSL:
        return PathlibPath(pathstring, *args, **kwargs)

    # Detection of UNC Windows paths (\\server\share)
    if pathstring.startswith("//"):
        unc_path = pathstring.lstrip("/")
        pathstring = f"/mnt/unc/{unc_path}"
        return PathlibPath(pathstring, *args, **kwargs)

    # Conversion of paths Windows with disk (C:/Users/...)
    if ":" in pathstring:
        drive, rest = pathstring.split(":", 1)
        pathstring = f"/mnt/{drive.lower()}{rest}"
        return PathlibPath(pathstring, *args, **kwargs)

    # Else → already a native/relative Linux path
    return PathlibPath(pathstring, *args, **kwargs)
    


# %% Test function run
if __name__ == "__main__":
    from corelp import test
    test(__file__)