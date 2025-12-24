#!/usr/bin/env python

'''
test_mrsdimcontrol.py - Tests methods of MRSDimControl class in controls.py

Authors: Vasilis Karlaftis    <vasilis.karlaftis@ndcn.ox.ac.uk>

Elements taken from fsleyes/fsleyes/tests/controls/test_controls.py by Paul McCarthy <pauldmccarthy@gmail.com>
         
Copyright (C) 2025 University of Oxford
'''

from pathlib import Path
import fsl.data.image as fslimage
from tests import run_with_viewpanel, realYield

from fsleyes_plugin_mrs.controls    import MRSDimControl
from fsleyes_plugin_mrs.views       import MRSView

dim_datadir  = Path(__file__).parent / 'testdata' / 'dim'

# Test #1: check if the title matches the expected value
def test_title():
    assert isinstance(MRSDimControl.title(), str)
    assert MRSDimControl.title() == "MRS Dimension control"

# Test #2: check if supportedViews include the MRSView
def test_supportedViews():
    assert isinstance(MRSDimControl.supportedViews(), list)
    assert MRSView in MRSDimControl.supportedViews()

# Test #3: check MRSDimControl basic functionality on a single metabolite file
def test_toggle():
    run_with_viewpanel(_test_toggle, MRSView)

def _test_toggle(view, overlayList, displayCtx):

    img = fslimage.Image(dim_datadir / 'example_1.nii.gz')
    overlayList.append(img)
    realYield(25)

    # toggle the panel off and on
    view.togglePanel(MRSDimControl)
    realYield(25)

    view.togglePanel(MRSDimControl)
    realYield(25)

# Test #4: check generateDataSeriesWidgets & refreshDataSeriesWidgets functionality
# (creating 'niftiMRSDimensions' widgets)
def test_generateDataSeriesWidgets():
    run_with_viewpanel(_test_generateDataSeriesWidgets, MRSView)

def _test_generateDataSeriesWidgets(view, overlayList, displayCtx):
    img = fslimage.Image(dim_datadir / 'example_1.nii.gz')
    overlayList.append(img)
    img = fslimage.Image(dim_datadir / 'example_3.nii.gz')
    overlayList.append(img)
    realYield(25)

    # toggle the panel on
    if not view.isPanelOpen(MRSDimControl):
        view.togglePanel(MRSDimControl)
    panel = view.getPanel(MRSDimControl)
    realYield(25)

    groupName = 'niftiMRSDimensions'
    widgetList = panel.getWidgetList()
    assert groupName in widgetList.GetGroups()
    # check that the widgetList is expanded
    assert widgetList.IsExpanded(groupName) == True

    # set selectedOverlay to desired image
    idx = 0
    overlay = overlayList[idx]
    view.displayCtx.selectOverlay(overlay)
    ps = view.getDataSeries(overlay)
    # check that the following widgets are present for example_1
    disp_names = ['Link NIfTI-MRS Dimensions']
    for dim in range(5, min(8, overlay.ndim+1)):
        disp_names.append(f'DIM {dim}')
        if ps.hdr_ext[f'dim_{dim}'] != 'DIM_COIL':
            disp_names.append(f'Average DIM {dim}')
            if overlay.shape[dim-1] == 2:
                disp_names.append(f'Difference DIM {dim}')
    my_widgets = widgetList._WidgetList__groups[groupName].widgets
    for name in disp_names:
        assert any(w.displayName == name for w in my_widgets.values()), \
            f"No widget found with displayName == '{name}'"
    
    # change selectedOverlay and re-test
    idx = 1
    overlay = overlayList[idx]
    view.displayCtx.selectOverlay(overlay)
    ps = view.getDataSeries(overlay)
    # check that the following widgets are present for example_3
    disp_names = ['Link NIfTI-MRS Dimensions']
    for dim in range(5, min(8, overlay.ndim+1)):
        disp_names.append(f'DIM {dim}')
        if ps.hdr_ext[f'dim_{dim}'] != 'DIM_COIL':
            disp_names.append(f'Average DIM {dim}')
            if overlay.shape[dim-1] == 2:
                disp_names.append(f'Difference DIM {dim}')
    my_widgets = widgetList._WidgetList__groups[groupName].widgets
    for name in disp_names:
        assert any(w.displayName == name for w in my_widgets.values()), \
            f"No widget found with displayName == '{name}'"

# Test #5: check refreshInfoPanel & __selectedOverlayChanged functionality
# (creating 'niftiMRSInfo' widgets)
def test_refreshInfoPanel():
    run_with_viewpanel(_test_refreshInfoPanel, MRSView)

def _test_refreshInfoPanel(view, overlayList, displayCtx):
    img = fslimage.Image(dim_datadir / 'example_1.nii.gz')
    overlayList.append(img)
    img = fslimage.Image(dim_datadir / 'example_3.nii.gz')
    overlayList.append(img)
    realYield(25)

    # toggle the panel on
    if not view.isPanelOpen(MRSDimControl):
        view.togglePanel(MRSDimControl)
    panel = view.getPanel(MRSDimControl)
    realYield(25)

    groupName = 'niftiMRSInfo'
    widgetList = panel.getWidgetList()
    assert groupName in widgetList.GetGroups()
    # check that the widgetList is expanded
    assert widgetList.IsExpanded(groupName) == True

    # set selectedOverlay to desired image
    idx = 0
    overlay = overlayList[idx]
    view.displayCtx.selectOverlay(overlay)
    ps = view.getDataSeries(overlay)
    # check that the following widgets are present for example_1
    disp_names = ['Nucleus : \t\t\t\t', 'Frequency (MHz) : \t\t', 'Spectral width (Hz) : \t\t']
    for dim in range(5, min(8, overlay.ndim+1)):
        disp_names.append(f'DIM {dim} - Tag : \t\t\t')
        disp_names.append(f'DIM {dim} - Size : \t\t\t')
        if f'dim_{dim}_info' in ps.hdr_ext:
            disp_names.append(f'DIM {dim} - Info : \t\t\t')
        d_hdr_str = f'dim_{dim}_header'
        if d_hdr_str in ps.hdr_ext:
            for key in ps.hdr_ext[d_hdr_str]:
                tabs = '\t' * (2 if len(key) <= 10 else 1)
                disp_names.append(f'DIM {dim} - {key} : {tabs}')
    my_widgets = widgetList._WidgetList__groups[groupName].widgets
    for name in disp_names:
        assert any(w.displayName == name for w in my_widgets.values()), \
            f"No widget found with displayName == '{name}'"

    # change selectedOverlay and re-test
    idx = 1
    overlay = overlayList[idx]
    view.displayCtx.selectOverlay(overlay)
    ps = view.getDataSeries(overlay)
    # check that the following widgets are present for example_3
    disp_names = ['Nucleus : \t\t\t\t', 'Frequency (MHz) : \t\t', 'Spectral width (Hz) : \t\t']
    for dim in range(5, min(8, overlay.ndim+1)):
        disp_names.append(f'DIM {dim} - Tag : \t\t\t')
        disp_names.append(f'DIM {dim} - Size : \t\t\t')
        if f'dim_{dim}_info' in ps.hdr_ext:
            disp_names.append(f'DIM {dim} - Info : \t\t\t')
        d_hdr_str = f'dim_{dim}_header'
        if d_hdr_str in ps.hdr_ext:
            for key in ps.hdr_ext[d_hdr_str]:
                tabs = '\t' * (2 if len(key) <= 10 else 1)
                disp_names.append(f'DIM {dim} - {key} : {tabs}')
    my_widgets = widgetList._WidgetList__groups[groupName].widgets
    for name in disp_names:
        assert any(w.displayName == name for w in my_widgets.values()), \
            f"No widget found with displayName == '{name}'"

# Test #6: check _set_dim_slider_limits functionality
def test_set_dim_slider_limits():
    run_with_viewpanel(_test_set_dim_slider_limits, MRSView)

def _test_set_dim_slider_limits(view, overlayList, displayCtx):
    img = fslimage.Image(dim_datadir / 'example_1.nii.gz')
    overlayList.append(img)
    realYield(25)

    overlay = overlayList[-1]
    ps = view.getDataSeries(overlay)

    # test default limits
    for dim in range(5, min(8, overlay.ndim+1)):
        assert ps.getProp(f'dim_{dim}').isEnabled(ps)
        assert ps.getProp(f'dim_{dim}').getAttribute(ps, 'minval') == 0
        assert ps.getProp(f'dim_{dim}').getAttribute(ps, 'maxval') == overlay.shape[dim - 1] - 1
        assert ps.getProp(f'dim_{dim}_avg').isEnabled(ps)
        assert ps.getProp(f'dim_{dim}_diff').isEnabled(ps)

    # test limits when average is toggled on
    for dim in range(5, min(8, overlay.ndim+1)):
        setattr(ps, f'dim_{dim}_avg', 1)
        assert ps.getProp(f'dim_{dim}').isEnabled(ps)
        assert ps.getProp(f'dim_{dim}').getAttribute(ps, 'minval') == 0
        assert ps.getProp(f'dim_{dim}').getAttribute(ps, 'maxval') == 0
        assert ps.getProp(f'dim_{dim}_avg').isEnabled(ps)
        assert not ps.getProp(f'dim_{dim}_diff').isEnabled(ps)
    
    # test limits when difference is toggled on
    for dim in range(5, min(8, overlay.ndim+1)):
        setattr(ps, f'dim_{dim}_avg', 0)
        setattr(ps, f'dim_{dim}_diff', 1)
        assert ps.getProp(f'dim_{dim}').isEnabled(ps)
        assert ps.getProp(f'dim_{dim}').getAttribute(ps, 'minval') == 0
        assert ps.getProp(f'dim_{dim}').getAttribute(ps, 'maxval') == 0
        assert not ps.getProp(f'dim_{dim}_avg').isEnabled(ps)
        assert ps.getProp(f'dim_{dim}_diff').isEnabled(ps)
