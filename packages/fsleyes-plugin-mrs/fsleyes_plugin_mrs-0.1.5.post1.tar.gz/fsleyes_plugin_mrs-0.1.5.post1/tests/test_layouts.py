#!/usr/bin/env python

'''
test_layouts.py - Tests methods of layouts.py

Authors: Vasilis Karlaftis    <vasilis.karlaftis@ndcn.ox.ac.uk>

Elements taken from fsleyes/fsleyes/tests/test_layouts.py by Paul McCarthy <pauldmccarthy@gmail.com>

Copyright (C) 2025 University of Oxford
'''

import os.path as op
from pathlib import Path
import fsl.data.image as fslimage
from tests import run_with_fsleyes, realYield

import fsleyes.layouts as layouts
from fsleyes_plugin_mrs.layouts import parseVersion

datadir = Path(__file__).parent / 'testdata' / 'svs'

# Test 1: check if parseVersion can handle standard format
def test_parseVersion_standard():
    assert parseVersion("1.15.0") == (1, 15, 0)

# Test 2: check if parseVersion can handle dev format
def test_parseVersion_dev():
    assert parseVersion("2.0.1.dev0") == (2, 0, 1)

# Test 3: check if parseVersion can handle non-numerical format
def test_parseVersion_nonnumeric():
    assert parseVersion("1.7.alpha") == (1, 7)

# Test #4: check MRSlayout basic functionality on a single metabolite file
def test_mrslayout():
    run_with_fsleyes(_test_layout, 'mrs')

def _test_layout(frame, overlayList, displayCtx, layout):
    img = fslimage.Image(op.join(datadir, 'metab'))
    overlayList.append(img)

    layouts.loadLayout(frame, layout)

    realYield(100)
