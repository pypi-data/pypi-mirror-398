#!/usr/bin/env python

'''
test_mrstoolbar.py - Tests methods of MRSToolBar class in controls.py

Authors: Vasilis Karlaftis    <vasilis.karlaftis@ndcn.ox.ac.uk>

Elements taken from fsleyes/fsleyes/tests/controls/test_controls.py by Paul McCarthy <pauldmccarthy@gmail.com>

Copyright (C) 2025 University of Oxford
'''

import os.path as op
from pathlib import Path
import fsl.data.image as fslimage
from tests import run_with_viewpanel, realYield

from fsleyes_plugin_mrs.controls    import MRSToolBar
from fsleyes_plugin_mrs.views       import MRSView

datadir = Path(__file__).parent / 'testdata' / 'svs'

# Test #1: check if the title matches the expected value
def test_title():
    assert isinstance(MRSToolBar.title(), str)
    assert MRSToolBar.title() == "MRS toolbar"

# Test #2: check if supportedViews include the MRSView
def test_supportedViews():
    assert isinstance(MRSToolBar.supportedViews(), list)
    assert MRSView in MRSToolBar.supportedViews()

# Test #3: check MRSToolBar basic functionality on a single metabolite file
def test_toggle():
    run_with_viewpanel(_test_toggle, MRSView)

def _test_toggle(view, overlayList, displayCtx):

    img = fslimage.Image(op.join(datadir, 'metab'))
    overlayList.append(img)
    realYield(25)

    # toggle the panel off and on
    view.togglePanel(MRSToolBar)
    realYield(25)

    view.togglePanel(MRSToolBar)
    realYield(25)
