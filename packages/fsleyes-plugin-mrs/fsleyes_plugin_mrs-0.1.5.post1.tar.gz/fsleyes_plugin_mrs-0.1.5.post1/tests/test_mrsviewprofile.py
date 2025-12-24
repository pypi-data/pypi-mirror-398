#!/usr/bin/env python

'''
test_mrsviewprofile.py - Tests methods of MRSViewProfile class in profiles.py

Authors: Vasilis Karlaftis    <vasilis.karlaftis@ndcn.ox.ac.uk>

Elements taken from fsleyes/fsleyes/tests/controls/test_orthoviewprofile.py by Paul McCarthy <pauldmccarthy@gmail.com>
         
Copyright (C) 2025 University of Oxford
'''

import os.path as op
from pathlib import Path
import fsl.data.image as fslimage
from tests import run_with_viewpanel, realYield, mockMouseEvent

from fsleyes_plugin_mrs.profiles    import MRSViewProfile
from fsleyes_plugin_mrs.views       import MRSView

datadir = Path(__file__).parent / 'testdata' / 'svs'

# Test #1: check if supportedView returns an MRSView
def test_supportedView():
    assert MRSViewProfile.supportedView() == MRSView

# Test #2: check if tempModes returns the right format
def test_tempModes():
    assert isinstance(MRSViewProfile.tempModes(), dict)

# Test #3: check MRSViewProfile basic functionality on a single metabolite file
def test_phasingMode():
    run_with_viewpanel(_test_phasingMode, MRSView)

def _test_phasingMode(view, overlayList, displayCtx):

    img = fslimage.Image(op.join(datadir, 'metab'))
    overlayList.append(img)

    realYield()

    opts     = view.displayCtx.getOpts(img)
    profile  = view.currentProfile
    # zcanvas  = view.getGLCanvases()[2]
    # z        = int(opts.transformCoords([displayCtx.location],
    #                                     'display',
    #                                     'voxel',
    #                                     vround=True)[0, 2])

    # vstart = [ 3,  3,  z]
    # vend   = [ 10, 10, z]
    # dstart = opts.transformCoords(vstart, 'voxel', 'display')
    # dend   = opts.transformCoords(vend,   'voxel', 'display')

    profile.mode = 'phasing'

    # mockMouseEvent(profile, zcanvas, 'LeftMouseDown', dstart)
    # mockMouseEvent(profile, zcanvas, 'LeftMouseDrag', dstart)
    # mockMouseEvent(profile, zcanvas, 'LeftMouseUp',   dend)

    # realYield()

    # sx, sy, sz = vstart
    # ex, ey, ez = vend

    # data = img.data[sx:ex + 1, sy:ey + 1, sz:ez + 1]
    # dmin = data.min()
    # dmax = data.max()

    # assert opts.displayRange == (dmin, dmax)
