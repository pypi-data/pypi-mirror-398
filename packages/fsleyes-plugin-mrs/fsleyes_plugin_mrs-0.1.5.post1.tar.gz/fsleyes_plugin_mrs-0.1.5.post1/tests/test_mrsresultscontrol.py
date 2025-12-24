#!/usr/bin/env python

'''
test_mrsresultscontrol.py - Tests methods of MRSResultsControl class in tools.py

Authors: Vasilis Karlaftis    <vasilis.karlaftis@ndcn.ox.ac.uk>

Elements taken from fsleyes/fsleyes/tests/controls/test_controls.py by Paul McCarthy <pauldmccarthy@gmail.com>

Copyright (C) 2025 University of Oxford
'''

import os.path as op
from pathlib import Path
import numpy as np
from unittest.mock import patch, MagicMock
import fsl.data.image as fslimage
from tests import run_with_viewpanel, realYield, capture_logs

from fsleyes_plugin_mrs.tools       import MRSResultsControl
from fsleyes.views.orthopanel       import OrthoPanel

datadir = Path(__file__).parent / 'testdata' / 'mrsi'

# Mock FileTree
def mock_tree(filename):
    tree = MagicMock()
    tree.metab_ph = 'metab'
    tree.update.return_value.get.return_value = filename
    return tree

# Mock colourscheme
def mock_colourscheme():
    colourscheme = {
        "partially_invalid": {
            "Cmap": "cool",
            "displayRange" : ["0.0", "min + std"],
        },
        "full-valid": {
            "cmap": "cool",
            "displayRange" : ["0.0", "median + 3 * std"],
            "clippingRange": ["min", "max"],
            "linkLowRanges": True,
        },
        "percentile tests": {
            "displayRange" : ["percentile(10)", "percentile(90)"],
            "clippingRange": ["percentile(50) - 2 * std", "percentile(95) - percentile(25)"],
            "linkLowRanges": False,
        }
    }
    return colourscheme

# Convert overlayList to list of strings
def overlay_to_string(overlayList):
    return [repr(ovl) for ovl in overlayList]

# Test #1: check if the title matches the expected value
def test_title():
    assert isinstance(MRSResultsControl.title(), str)
    assert MRSResultsControl.title() == "MRSI map control"

# Test #2: check if supportedViews include the MRSView
def test_supportedViews():
    assert isinstance(MRSResultsControl.supportedViews(), list)
    assert OrthoPanel in MRSResultsControl.supportedViews()

# Test #3: check MRSResultsControl basic functionality on a single metabolite file
def test_toggle():
    run_with_viewpanel(_test_toggle, OrthoPanel)

def _test_toggle(view, overlayList, displayCtx):

    img = fslimage.Image(op.join(datadir, 'data'))
    overlayList.append(img)
    realYield(25)

    # toggle the panel off and on
    view.togglePanel(MRSResultsControl)
    realYield(25)

    view.togglePanel(MRSResultsControl)
    realYield(25)

# Test #4: check generateWidgets functionality
def test_generateWidgets():
    run_with_viewpanel(_test_generateWidgets, OrthoPanel)

def _test_generateWidgets(view, overlayList, displayCtx):
    img = fslimage.Image(op.join(datadir, 'data'))
    overlayList.append(img)
    realYield(25)

    # toggle the panel on
    if not view.isPanelOpen(MRSResultsControl):
        view.togglePanel(MRSResultsControl)
    panel = view.getPanel(MRSResultsControl)
    realYield(25)
    
    groupName = 'mrsi_results'
    widgetList = panel.getWidgetList()
    assert groupName in widgetList.GetGroups()
    # check that the following widgets are present
    disp_names = ['Metabolite', 'Type', 'Replace?']
    my_widgets = widgetList._WidgetList__groups[groupName].widgets
    for name in disp_names:
        assert any(w.displayName == name for w in my_widgets.values()), \
            f"No widget found with displayName == '{name}'"
    # check that the widgetList is expanded
    assert widgetList.IsExpanded(groupName) == True

# Test #5: check update_choices functionality
def test_update_choices():
    run_with_viewpanel(_test_update_choices, OrthoPanel)

def _test_update_choices(view, overlayList, displayCtx):
    img = fslimage.Image(op.join(datadir, 'data'))
    overlayList.append(img)
    realYield(25)

    # toggle the panel on
    if not view.isPanelOpen(MRSResultsControl):
        view.togglePanel(MRSResultsControl)
    panel = view.getPanel(MRSResultsControl)
    realYield(25)

    # Mock update_choice inputs
    metabolites    = ['Asc', 'Cr+PCr', 'NAA']
    overlay_types  = ['raw', 'internal', 'SNR']
    tree           = None
    colourscheme   = None

    panel.update_choices(metabolites, overlay_types, tree, colourscheme)

    # Check that the choices were updated in the propStore
    assert panel._propStore.getProp('metabolite').getChoices(instance=panel._propStore) == metabolites
    assert panel._propStore.getProp('overlay_type').getChoices(instance=panel._propStore) == overlay_types

# Test #6: check _selected_result_change functionality
def test_selected_result_change():
    run_with_viewpanel(_test_selected_result_change, OrthoPanel)

def _test_selected_result_change(view, overlayList, displayCtx):
    img = fslimage.Image(op.join(datadir, 'data'))
    overlayList.append(img)
    realYield(25)

    # toggle the panel on
    if not view.isPanelOpen(MRSResultsControl):
        view.togglePanel(MRSResultsControl)
    panel = view.getPanel(MRSResultsControl)
    realYield(25)

    initial_overlayList = overlay_to_string(panel.overlayList)
    logger, handler, log_stream = capture_logs('fsleyes_plugin_mrs.tools')

    # Test if empty _overlay_types results in early return
    panel._overlay_types = None
    panel._selected_result_change()
    assert overlay_to_string(panel.overlayList) == initial_overlayList

    # Test if empty _overlay_types results in early return
    panel._overlay_types = True
    panel._tree = None
    panel._selected_result_change()
    handler.flush()
    log_output = log_stream.getvalue()
    assert 'ERROR:' in log_output
    assert overlay_to_string(panel.overlayList) == initial_overlayList
    # Clear the stream for the next log
    log_stream.truncate(0)
    log_stream.seek(0)

    # Test if file does not exist results in early return
    with patch('fsleyes_plugin_mrs.tools.Path.exists', return_value=False):
        panel._overlay_types = True
        panel._tree = mock_tree(datadir / 'data.nii.gz')
        panel._selected_result_change()
        handler.flush()
        log_output = log_stream.getvalue()
        assert 'WARNING:' in log_output
        assert overlay_to_string(panel.overlayList) == initial_overlayList
        # Clear the stream for the next log
        log_stream.truncate(0)
        log_stream.seek(0)
    
    # Test if a new overlay is created without replacing
    with patch('fsleyes_plugin_mrs.tools.Path.exists', return_value=True):
        panel._overlay_types = True
        panel._tree = mock_tree(datadir / 'data.nii.gz')
        panel._selected_result_change()
        new_overlayList = overlay_to_string(panel.overlayList)
        assert new_overlayList      != initial_overlayList
        assert new_overlayList[:-1] == initial_overlayList
        assert len(new_overlayList) == len(initial_overlayList) + 1
        # update initial_overlayList to match latest changes
        initial_overlayList = new_overlayList

    # Test if a new overlay is created by replacing the previous overlay
    with patch('fsleyes_plugin_mrs.tools.Path.exists', return_value=True):
        panel._overlay_types = True
        panel._tree = mock_tree(datadir / 'fit.nii.gz')
        panel._propStore.replace = True
        panel._selected_result_change()
        new_overlayList = overlay_to_string(panel.overlayList)
        assert new_overlayList[:-1] == initial_overlayList[:-1]
        assert new_overlayList[-1]  != initial_overlayList[-1]
        assert len(new_overlayList) == len(initial_overlayList)

    # Remove logger handler
    logger.removeHandler(handler)

# Test #7: check _set_overlay_display functionality
def test_set_overlay_display():
    run_with_viewpanel(_test_set_overlay_display, OrthoPanel)

def _test_set_overlay_display(view, overlayList, displayCtx):
    img = fslimage.Image(op.join(datadir, 'metab_map'))
    overlayList.append(img)
    realYield(25)

    # toggle the panel on
    if not view.isPanelOpen(MRSResultsControl):
        view.togglePanel(MRSResultsControl)
    panel = view.getPanel(MRSResultsControl)
    realYield(25)

    opts = panel.displayCtx.getOpts(img)
    logger, handler, log_stream = capture_logs('fsleyes_plugin_mrs.tools')

    # calculate default displayRange limits
    nonzero = img.data[np.nonzero(img.data)]
    min_val = np.median(nonzero) - 2 * np.std(nonzero)
    min_val = np.maximum(min_val, 0.0)
    max_val = np.median(nonzero) + 2 * np.std(nonzero)

    # Test if empty _colourscheme results in using defaults
    panel._colourscheme = None
    panel._set_overlay_display(None)
    handler.flush()
    log_output = log_stream.getvalue()
    assert 'WARNING:' in log_output
    assert opts.cmap.name == "fsleyes_hot"
    assert opts.displayRange == [float(min_val), float(max_val)]
    # Clear the stream for the next log
    log_stream.truncate(0)
    log_stream.seek(0)

    # Get non-empty colourscheme for subsequent tests
    panel._colourscheme = mock_colourscheme()

    # Test if type is not in colourscheme keys results in using defaults
    panel._set_overlay_display(None)
    handler.flush()
    log_output = log_stream.getvalue()
    assert 'WARNING:' in log_output
    assert opts.cmap.name == "fsleyes_hot"
    assert opts.displayRange == [float(min_val), float(max_val)]
    # Clear the stream for the next log
    log_stream.truncate(0)
    log_stream.seek(0)
    
    # Test _colourscheme type with partially invalid fields
    panel._set_overlay_display("partially_invalid")
    handler.flush()
    log_output = log_stream.getvalue()
    assert 'WARNING:' in log_output
    assert not hasattr(opts, "Cmap")
    assert opts.cmap.name == "fsleyes_hot"
    new_max_val = np.min(nonzero) + np.std(nonzero)
    assert opts.displayRange == [0.0, float(new_max_val)]
    # Clear the stream for the next log
    log_stream.truncate(0)
    log_stream.seek(0)

    # Test _colourscheme type with valid fields
    panel._set_overlay_display("full-valid")
    assert opts.cmap.name == "fsleyes_cool"
    assert opts.linkLowRanges == True
    new_min_val = np.min(nonzero)
    new_min_val = np.maximum(new_min_val, 0.0)
    new_max_val = np.median(nonzero) + 3 * np.std(nonzero)
    assert opts.displayRange  == [float(new_min_val), float(new_max_val)]
    new_max_val = np.max(nonzero)
    assert opts.clippingRange == [float(new_min_val), float(new_max_val)]
    
    # Test _colourscheme type with various percentile expressions
    panel._set_overlay_display("percentile tests")
    assert opts.cmap.name == "fsleyes_hot"
    assert opts.linkLowRanges == False
    low_val  = np.percentile(nonzero, 10)
    low_val  = np.maximum(low_val, 0.0)
    high_val = np.percentile(nonzero, 90)
    assert opts.displayRange  == [float(low_val), float(high_val)]
    low_val  = np.percentile(nonzero, 50) - 2 * np.std(nonzero)
    low_val  = np.maximum(low_val, 0.0)
    high_val = np.percentile(nonzero, 95) - np.percentile(nonzero, 25)
    assert opts.clippingRange == [float(low_val), float(high_val)]

    # Remove logger handler
    logger.removeHandler(handler)
