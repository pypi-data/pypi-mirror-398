#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date          : 2025-11-30
# Author        : Lancelot PINCET
# GitHub        : https://github.com/LancelotPincet
# Library       : coreLP
# Module        : user_inputs

"""
Gets last user inputs dictionnary from global variables.
"""



# %% Libraries
import inspect
from IPython import get_ipython



# %% Function
_user_inputs = {} # User inputs cache

def user_inputs() :
    r"""
    Return a dictionary of variables defined by the user in the interactive
    environment.

    This function is intended for use inside other functions via
    ``function(**user_inputs())``.  
    **It should not be used to store its return value**, e.g. **do not do**::

        variable = user_inputs()

    Instead, call it directly when needed.

    Returns
    -------
    dict
        A dictionary containing the user's currently defined variables.

    Examples
    --------
    >>> from corelp import user_inputs
    >>> user_inputs()       # First call (initializes and clears import-related variables)
    {}
    >>> a = 1               # User defines a variable
    >>> user_inputs()       # Now returns: {'a': 1}
    {'a': 1}
    """

    # ---- Detect execution environment ----
    ipy = get_ipython()

    if ipy is not None:
        # Running in IPython or Jupyter
        ns = ipy.user_ns
    else:
        # Running in normal Python script
        frame = inspect.currentframe().f_back
        ns = {**frame.f_globals, **frame.f_locals}

    # ---- Filter user variables (ignore internals starting with "_") ----
    ns = {k: v for k, v in ns.items() if not k.startswith("_")}

    # ---- Return only new or updated variables ----
    updated = {
        k: v
        for k, v in ns.items()
        if k not in _user_inputs or _user_inputs[k] is not v
    }

    _user_inputs.update(updated)
    return updated



# %% Test function run
if __name__ == "__main__":
    from corelp import test
    test(__file__)