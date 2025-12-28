#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date          : 2025-09-02
# Author        : Lancelot PINCET
# GitHub        : https://github.com/LancelotPincet
# Library       : coreLP
# Module        : Path

"""
This file allows to test Path

Path : This function is a wrapper around the pathlib.Path and returns a compatible Path with a windows path copied inside Linux (for WSL)
"""



# %% Libraries
from corelp import print, debug
import pytest
from corelp import Path
debug_folder = debug(__file__)



# %% Function test
def test_function() :
    '''
    Test Path function
    '''
    print('Hello world!')



# %% Test function run
if __name__ == "__main__":
    from corelp import test
    test(__file__)