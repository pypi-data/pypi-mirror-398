#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date          : 2025-11-30
# Author        : Lancelot PINCET
# GitHub        : https://github.com/LancelotPincet
# Library       : coreLP
# Module        : user_inputs

"""
This file allows to test user_inputs

user_inputs : Gets last user inputs dictionnary from global variables.
"""



# %% Libraries
from corelp import print, debug
import pytest
from corelp import user_inputs
debug_folder = debug(__file__)



# %% Function test
def test_user_inputs() :
    '''
    Test user_inputs function
    '''
    user_inputs() #init
    a = 1
    inputs = user_inputs()
    if inputs != {'a': 1} :
        raise ValueError(f'{inputs} should be dict(a=1)')
    user_inputs() #init
    b = 2
    if user_inputs() != {'b': 2} :
        raise ValueError(f'{inputs} should be dict(b=2)')



# %% Test function run
if __name__ == "__main__":
    from corelp import test
    test(__file__)