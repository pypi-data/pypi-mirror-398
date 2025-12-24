#!/usr/bin/env python

'''
test_mrscontrolpanel.py - Tests methods of MRSControlPanel class in controls.py

Authors: Vasilis Karlaftis    <vasilis.karlaftis@ndcn.ox.ac.uk>

Elements taken from fsleyes/fsleyes/tests/controls/test_controls.py and
    test_plotlistpanel.py by Paul McCarthy <pauldmccarthy@gmail.com>

Copyright (C) 2025 University of Oxford
'''

import os.path as op
from pathlib import Path
import fsl.data.image as fslimage
from tests import run_with_viewpanel, realYield

from fsleyes_plugin_mrs.controls    import MRSControlPanel
from fsleyes_plugin_mrs.views       import MRSView

datadir = Path(__file__).parent / 'testdata' / 'svs'

# Test #1: check if the title matches the expected value
def test_title():
    assert isinstance(MRSControlPanel.title(), str)
    assert MRSControlPanel.title() == "MRS control panel"

# Test #2: check if supportedViews include the MRSView
def test_supportedViews():
    assert isinstance(MRSControlPanel.supportedViews(), list)
    assert MRSView in MRSControlPanel.supportedViews()

# Test #3: check MRSControlPanel basic functionality on a single metabolite file
def test_toggle():
    run_with_viewpanel(_test_toggle, MRSView)

def _test_toggle(view, overlayList, displayCtx):

    img = fslimage.Image(op.join(datadir, 'metab'))
    overlayList.append(img)
    realYield(25)

    # toggle the panel off and on
    view.togglePanel(MRSControlPanel)
    realYield(25)

    view.togglePanel(MRSControlPanel)
    realYield(25)

# Test #4: check MRSControlPanel 'customPlotSettings' widgets
def test_customPlotSettings():
    run_with_viewpanel(_test_customPlotSettings, MRSView)

def _test_customPlotSettings(view, overlayList, displayCtx):
    img = fslimage.Image(op.join(datadir, 'metab'))
    overlayList.append(img)
    realYield(25)

    # toggle the panel on
    if not view.isPanelOpen(MRSControlPanel):
        view.togglePanel(MRSControlPanel)
    panel = view.getPanel(MRSControlPanel)
    realYield(25)
    
    groupName = 'customPlotSettings'
    widgetList = panel.getWidgetList()
    assert groupName in widgetList.GetGroups()
    # check that the following widgets are present
    disp_names = ['Link 0th and 1st order phase',
                  'Link apodization',
                  'Plot real', 'Plot imaginary',
                  'Plot magnitude', 'Plot phase']
    my_widgets = widgetList._WidgetList__groups[groupName].widgets
    for name in disp_names:
        assert any(w.displayName == name for w in my_widgets.values()), \
            f"No widget found with displayName == '{name}'"
    # check that the widgetList is expanded
    assert widgetList.IsExpanded(groupName) == True

# Test #5: check MRSControlPanel 'plotSettings' widgets
def test_plotSettings():
    run_with_viewpanel(_test_plotSettings, MRSView)

def _test_plotSettings(view, overlayList, displayCtx):
    img = fslimage.Image(op.join(datadir, 'metab'))
    overlayList.append(img)
    realYield(25)

    # toggle the panel on
    if not view.isPanelOpen(MRSControlPanel):
        view.togglePanel(MRSControlPanel)
    panel = view.getPanel(MRSControlPanel)
    realYield(25)
    
    groupName = 'plotSettings'
    widgetList = panel.getWidgetList()
    assert groupName in widgetList.GetGroups()
    # check that the 'Smooth' widget is deleted
    my_widgets = widgetList._WidgetList__groups[groupName].widgets
    assert all(w.displayName != "Smooth" for w in my_widgets.values())
    # check that the widgetList is collapsed
    assert widgetList.IsExpanded(groupName) == False

# Test #6: check MRSControlPanel 'currentDSSettings' widgets
def test_currentDSSettings():
    run_with_viewpanel(_test_currentDSSettings, MRSView)

def _test_currentDSSettings(view, overlayList, displayCtx):
    img = fslimage.Image(op.join(datadir, 'metab'))
    overlayList.append(img)
    realYield(25)

    # toggle the panel on
    if not view.isPanelOpen(MRSControlPanel):
        view.togglePanel(MRSControlPanel)
    panel = view.getPanel(MRSControlPanel)
    realYield(25)
    
    groupName = 'currentDSSettings'
    widgetList = panel.getWidgetList()
    assert groupName in widgetList.GetGroups()
    # check that the widgetList is collapsed
    assert widgetList.IsExpanded(groupName) == False

# Test #7: check MRSControlPanel 'customDSSettings' widgets
def test_customDSSettings():
    run_with_viewpanel(_test_customDSSettings, MRSView)

def _test_customDSSettings(view, overlayList, displayCtx):
    img = fslimage.Image(op.join(datadir, 'metab'))
    overlayList.append(img)
    realYield(25)

    # toggle the panel on
    if not view.isPanelOpen(MRSControlPanel):
        view.togglePanel(MRSControlPanel)
    panel = view.getPanel(MRSControlPanel)
    realYield(25)
    
    groupName = 'customDSSettings'
    widgetList = panel.getWidgetList()
    assert groupName in widgetList.GetGroups()
    # check that the following widgets are present
    disp_names = ['Apodize (in Hz)',
                  'Zero order phase correction (degrees)',
                  'First order phase correction (milliseconds)']
    my_widgets = widgetList._WidgetList__groups[groupName].widgets
    for name in disp_names:
        assert any(w.displayName == name for w in my_widgets.values()), \
            f"No widget found with displayName == '{name}'"
    # check that the widgetList is expanded
    assert widgetList.IsExpanded(groupName) == True
