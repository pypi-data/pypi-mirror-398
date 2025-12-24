#!/usr/bin/env python

'''
test_mrsview.py - Tests methods of MRSView class in views.py

Authors: Vasilis Karlaftis    <vasilis.karlaftis@ndcn.ox.ac.uk>

Elements taken from fsleyes/fsleyes/tests/controls/test_views.py by Paul McCarthy <pauldmccarthy@gmail.com>
         
Copyright (C) 2025 University of Oxford
'''

import ast
import os.path as op
from pathlib import Path
import fsl.data.image as fslimage
from tests import run_with_fsleyes, realYield

from fsleyes_plugin_mrs.views import MRSView
from fsleyes.plotting.powerspectrumseries import (ImaginaryPowerSpectrumSeries,
                                                  MagnitudePowerSpectrumSeries,
                                                  PhasePowerSpectrumSeries)


svs_datadir  = Path(__file__).parent / 'testdata' / 'svs'
mrsi_datadir = Path(__file__).parent / 'testdata' / 'mrsi'
dim_datadir  = Path(__file__).parent / 'testdata' / 'dim'

# Test #1: check if the title matches the expected value
def test_title():
    assert isinstance(MRSView.title(), str)
    assert MRSView.title() == "MRS"

# Test #2: check if the controlOrder method returns the right datatype
# and all elements are defined as a class in the expected files
def test_controlOrder():
    assert isinstance(MRSView.controlOrder(), list)

    # find classes defined in our control file
    controls_filename = 'fsleyes_plugin_mrs/controls.py'
    with open(controls_filename, "r") as file:
        node = ast.parse(file.read(), filename=controls_filename)
    valid_classes = [n.name for n in node.body if isinstance(n, ast.ClassDef)]
    # find classes defined in the parent class of MRSView
    for cls in MRSView.__bases__:
        valid_classes.extend(cls.controlOrder())
    for layout in MRSView.controlOrder():
        assert layout in valid_classes

# Test #3: check if the defaultLayout method returns the right datatype
# and all elements are defined as a class in the expected files
def test_defaultLayout():
    assert isinstance(MRSView.defaultLayout(), list)

    # find classes defined in our control file
    controls_filename = 'fsleyes_plugin_mrs/controls.py'
    with open(controls_filename, "r") as file:
        node = ast.parse(file.read(), filename=controls_filename)
    valid_classes = [n.name for n in node.body if isinstance(n, ast.ClassDef)]
    # find classes defined in the parent class of MRSView
    for cls in MRSView.__bases__:
        valid_classes.extend(cls.defaultLayout())
    for layout in MRSView.defaultLayout():
        assert layout in valid_classes

# Test #4: check if MRSView props have the correct default values
def test_defaultProps():
    run_with_fsleyes(_test_defaultProps)

def _test_defaultProps(frame, overlayList, displayCtx):
    img = fslimage.Image(op.join(svs_datadir, 'metab'))
    overlayList.append(img)

    view = frame.addViewPanel(MRSView)
    frame.viewPanelDefaultLayout(frame.viewPanels[0])
    realYield(100)

    assert view.linkPhase     == True
    assert view.linkApod      == False
    assert view.plotReal      == True
    assert view.plotImaginary == False
    assert view.plotMagnitude == False
    assert view.plotPhase     == False
    assert view.zeroOrderPhaseCorrection  == 0.0
    assert view.firstOrderPhaseCorrection == 0.0
    assert view.apodizeSeries == 0

# Test #5: check MRSView colour pallette
def test_colours():
    run_with_fsleyes(_test_colours)

def _test_colours(frame, overlayList, displayCtx):

    img = fslimage.Image(op.join(svs_datadir, 'metab'))
    overlayList.append(img)

    view = frame.addViewPanel(MRSView)
    frame.viewPanelDefaultLayout(frame.viewPanels[0])
    realYield(100)
    
    # check if background colour is near white
    assert all(c >= 0.9 for c in view.canvas.bgColour[0:3])
    # check if grid colour is mid-grey to black
    assert all(c <= 0.5 for c in view.canvas.gridColour[0:3])
    assert all(abs(c - view.canvas.gridColour[0]) <= 0.01 for c in view.canvas.gridColour[1:3])

# Test #6: check MRSView plot projections functionality
def test_plotProj():
    run_with_fsleyes(_test_plotProj)

def _test_plotProj(frame, overlayList, displayCtx):
    img = fslimage.Image(op.join(mrsi_datadir, 'fit'))
    overlayList.append(img)
    img = fslimage.Image(op.join(mrsi_datadir, 'baseline'))
    overlayList.append(img)
    img = fslimage.Image(op.join(mrsi_datadir, 'residual'))
    overlayList.append(img)

    view = frame.addViewPanel(MRSView)
    frame.viewPanelDefaultLayout(frame.viewPanels[0])
    realYield(100)

    # Test plotReal prop works correctly
    view.plotReal = True
    for overlay in overlayList:
        ds = view.getDataSeries(overlay)
        assert all(data is not None for data in ds.getData())
    view.plotReal = False
    for overlay in overlayList:
        ds = view.getDataSeries(overlay)
        assert all(data is None for data in ds.getData())
    # testing view.getDataSeriesToPlot() when plotReal is True/False is not working here
    # as MDComplexPowerSpectrumSeries are by default returned in this function

    # Test plotImaginary prop works correctly
    view.plotImaginary = True
    for overlay in overlayList:
        ds = view.getDataSeries(overlay)
        # each dataseries should have ImaginaryPowerSpectrumSeries object in extraSeries
        assert any(isinstance(obj, ImaginaryPowerSpectrumSeries) for obj in ds.extraSeries())
    # the number of ImaginaryPowerSpectrumSeries objects to plot should match the number of overlays
    assert sum(isinstance(obj, ImaginaryPowerSpectrumSeries) for obj in view.getDataSeriesToPlot()) == len(overlayList)
    view.plotImaginary = False
    for overlay in overlayList:
        ds = view.getDataSeries(overlay)
        # each dataseries should not have ImaginaryPowerSpectrumSeries object in extraSeries
        assert not any(isinstance(obj, ImaginaryPowerSpectrumSeries) for obj in ds.extraSeries())
    # the number of ImaginaryPowerSpectrumSeries objects to plot should be zero
    assert sum(isinstance(obj, ImaginaryPowerSpectrumSeries) for obj in view.getDataSeriesToPlot()) == 0

    # Test plotMagnitude prop works correctly
    view.plotMagnitude = True
    for overlay in overlayList:
        ds = view.getDataSeries(overlay)
        # each dataseries should have MagnitudePowerSpectrumSeries object in extraSeries
        assert any(isinstance(obj, MagnitudePowerSpectrumSeries) for obj in ds.extraSeries())
    # the number of MagnitudePowerSpectrumSeries objects to plot should match the number of overlays
    assert sum(isinstance(obj, MagnitudePowerSpectrumSeries) for obj in view.getDataSeriesToPlot()) == len(overlayList)
    view.plotMagnitude = False
    for overlay in overlayList:
        ds = view.getDataSeries(overlay)
        # each dataseries should not have MagnitudePowerSpectrumSeries object in extraSeries
        assert not any(isinstance(obj, MagnitudePowerSpectrumSeries) for obj in ds.extraSeries())
    # the number of MagnitudePowerSpectrumSeries objects to plot should be zero
    assert sum(isinstance(obj, MagnitudePowerSpectrumSeries) for obj in view.getDataSeriesToPlot()) == 0

    # Test plotPhase prop works correctly
    view.plotPhase = True
    for overlay in overlayList:
        ds = view.getDataSeries(overlay)
        # each dataseries should have PhasePowerSpectrumSeries object in extraSeries
        assert any(isinstance(obj, PhasePowerSpectrumSeries) for obj in ds.extraSeries())
    # the number of PhasePowerSpectrumSeries objects to plot should match the number of overlays
    assert sum(isinstance(obj, PhasePowerSpectrumSeries) for obj in view.getDataSeriesToPlot()) == len(overlayList)
    view.plotPhase = False
    for overlay in overlayList:
        ds = view.getDataSeries(overlay)
        # each dataseries should not have PhasePowerSpectrumSeries object in extraSeries
        assert not any(isinstance(obj, PhasePowerSpectrumSeries) for obj in ds.extraSeries())
    # the number of PhasePowerSpectrumSeries objects to plot should be zero
    assert sum(isinstance(obj, PhasePowerSpectrumSeries) for obj in view.getDataSeriesToPlot()) == 0

    # Test plotProj props for new overlays when it is already enabled
    view.plotReal      = False
    view.plotImaginary = True
    view.plotMagnitude = False
    view.plotPhase     = True
    img = fslimage.Image(op.join(mrsi_datadir, 'data'))
    overlayList.append(img)
    realYield(20)
    ds = view.getDataSeries(overlayList[-1])
    assert all(data is None for data in ds.getData())
    assert any(isinstance(obj, ImaginaryPowerSpectrumSeries) for obj in ds.extraSeries())
    assert not any(isinstance(obj, MagnitudePowerSpectrumSeries) for obj in ds.extraSeries())
    assert any(isinstance(obj, PhasePowerSpectrumSeries) for obj in ds.extraSeries())

# Test #7: check MRSView linkPhase functionality
def test_linkPhase():
    run_with_fsleyes(_test_linkPhase)

def _test_linkPhase(frame, overlayList, displayCtx):
    img = fslimage.Image(op.join(mrsi_datadir, 'fit'))
    overlayList.append(img)
    img = fslimage.Image(op.join(mrsi_datadir, 'baseline'))
    overlayList.append(img)
    img = fslimage.Image(op.join(mrsi_datadir, 'residual'))
    overlayList.append(img)

    view = frame.addViewPanel(MRSView)
    frame.viewPanelDefaultLayout(frame.viewPanels[0])
    realYield(100)

    zero_values  = [50 , 0, 100]
    first_values = [0.2, 2, 0]

    # Test phase correction when linkPhase==True
    view.linkPhase = True
    # when setting global phase
    for z, f in zip(zero_values, first_values):
        view.zeroOrderPhaseCorrection  = z
        view.firstOrderPhaseCorrection = f
        for overlay in overlayList:
            ps = view.getDataSeries(overlay)
            assert ps.zeroOrderPhaseCorrection  == z
            assert ps.firstOrderPhaseCorrection == f
    # when setting the selected overlay's phase
    for z, f in zip(zero_values, first_values):
        overlay = displayCtx.getSelectedOverlay()
        ps = view.getDataSeries(overlay)
        ps.zeroOrderPhaseCorrection  = z
        ps.firstOrderPhaseCorrection = f
        assert view.zeroOrderPhaseCorrection  == z
        assert view.firstOrderPhaseCorrection == f
        for overlay in overlayList:
            ps = view.getDataSeries(overlay)
            assert ps.zeroOrderPhaseCorrection  == z
            assert ps.firstOrderPhaseCorrection == f

    # Test phase correction when linkPhase==False
    view.linkPhase = False
    for overlay, z, f in zip(overlayList, zero_values, first_values):
        ps = view.getDataSeries(overlay)
        ps.zeroOrderPhaseCorrection  = z
        ps.firstOrderPhaseCorrection = f
    # when setting global phase, they should each keep their initial values
    # make sure you give it a different value than the ones above
    # this also inherently tests for the selected overlay case too
    view.zeroOrderPhaseCorrection  = sum(zero_values)
    view.firstOrderPhaseCorrection = sum(first_values)
    for overlay, z, f in zip(overlayList, zero_values, first_values):
        ps = view.getDataSeries(overlay)
        assert ps.zeroOrderPhaseCorrection  == z
        assert ps.zeroOrderPhaseCorrection  != view.zeroOrderPhaseCorrection 
        assert ps.firstOrderPhaseCorrection == f
        assert ps.firstOrderPhaseCorrection != view.firstOrderPhaseCorrection 

    # Test phase correction when re-enabling linkPhase
    view.linkPhase = True
    # all dataseries should get the phase of the selected overlay
    overlay = displayCtx.getSelectedOverlay()
    ps_ref = view.getDataSeries(overlay)
    assert view.zeroOrderPhaseCorrection  == ps_ref.zeroOrderPhaseCorrection
    assert view.firstOrderPhaseCorrection == ps_ref.firstOrderPhaseCorrection
    for overlay in overlayList:
        ps = view.getDataSeries(overlay)
        assert ps.zeroOrderPhaseCorrection  == ps_ref.zeroOrderPhaseCorrection
        assert ps.firstOrderPhaseCorrection == ps_ref.firstOrderPhaseCorrection

    # Test phase correction for new overlays when it is already enabled
    img = fslimage.Image(op.join(mrsi_datadir, 'data'))
    overlayList.append(img)
    realYield(20)
    ps = view.getDataSeries(overlayList[-1])
    assert ps.zeroOrderPhaseCorrection  == ps_ref.zeroOrderPhaseCorrection
    assert ps.firstOrderPhaseCorrection == ps_ref.firstOrderPhaseCorrection

# Test #8: check MRSView linkApod functionality
def test_linkApod():
    run_with_fsleyes(_test_linkApod)

def _test_linkApod(frame, overlayList, displayCtx):
    img = fslimage.Image(op.join(mrsi_datadir, 'fit'))
    overlayList.append(img)
    img = fslimage.Image(op.join(mrsi_datadir, 'baseline'))
    overlayList.append(img)
    img = fslimage.Image(op.join(mrsi_datadir, 'residual'))
    overlayList.append(img)

    view = frame.addViewPanel(MRSView)
    frame.viewPanelDefaultLayout(frame.viewPanels[0])
    realYield(100)

    apod_values = [10, 0, 25]

    # Test apodization when linkApod==True
    view.linkApod = True
    # when setting global apodization
    for a in apod_values:
        view.apodizeSeries = a
        for overlay in overlayList:
            ps = view.getDataSeries(overlay)
            assert ps.apodizeSeries == a
    # when setting the selected overlay's apodization
    for a in apod_values:
        overlay = displayCtx.getSelectedOverlay()
        ps = view.getDataSeries(overlay)
        ps.apodizeSeries = a
        assert view.apodizeSeries == a
        for overlay in overlayList:
            ps = view.getDataSeries(overlay)
            assert ps.apodizeSeries == a

    # Test apodization when linkApod==False
    view.linkApod = False
    for overlay, a in zip(overlayList, apod_values):
        ps = view.getDataSeries(overlay)
        ps.apodizeSeries = a
    # when setting global apodization, they should each keep their initial values
    # make sure you give it a different value than the ones above
    # this also inherently tests for the selected overlay case too
    view.apodizeSeries = sum(apod_values)
    for overlay, a in zip(overlayList, apod_values):
        ps = view.getDataSeries(overlay)
        assert ps.apodizeSeries == a
        assert ps.apodizeSeries != view.apodizeSeries

    # Test apodization when re-enabling linkApod
    view.linkApod = True
    # all dataseries should get apodization of the selected overlay
    overlay = displayCtx.getSelectedOverlay()
    ps_ref = view.getDataSeries(overlay)
    assert view.apodizeSeries == ps_ref.apodizeSeries
    for overlay in overlayList:
        ps = view.getDataSeries(overlay)
        assert ps.apodizeSeries == ps_ref.apodizeSeries

    # Test apodization for new overlays when it is already enabled
    img = fslimage.Image(op.join(mrsi_datadir, 'data'))
    overlayList.append(img)
    realYield(20)
    ps = view.getDataSeries(overlayList[-1])
    assert ps.apodizeSeries == ps_ref.apodizeSeries
    
# Test #9: check MRSView linkDim functionality
def test_linkDim():
    run_with_fsleyes(_test_linkDim)

def _test_linkDim(frame, overlayList, displayCtx):
    img = fslimage.Image(dim_datadir / 'example_1.nii.gz')
    overlayList.append(img)
    img = fslimage.Image(dim_datadir / 'example_2.nii.gz')
    overlayList.append(img)
    img = fslimage.Image(dim_datadir / 'example_3.nii.gz')
    overlayList.append(img)

    view = frame.addViewPanel(MRSView)
    frame.viewPanelDefaultLayout(frame.viewPanels[0])
    realYield(100)
    
    # set selectedOverlay to desired image
    idx = 0
    ref_overlay = overlayList[idx]
    view.displayCtx.selectOverlay(ref_overlay)
    ref_ps = view.getDataSeries(ref_overlay)

    # Test MRSDimControl when linkDim==True
    view.linkDim = True
    # test that the display name has been updated
    assert view.displayCtx.getDisplay(ref_overlay).name.endswith(' (Link Dim ref)')
    # when setting the global dim_values only
    dim_values = [3, 8, 1]
    for dim in range(5, min(8, ref_overlay.ndim+1)):
        setattr(view, f'dim_{dim}', dim_values[dim-5])
        setattr(view, f'dim_{dim}_avg',  0)
        setattr(view, f'dim_{dim}_diff', 0)
    for overlay in overlayList:
        ps = view.getDataSeries(overlay)
        if ps is None:
            continue
        for dim in range(5, min(len(view.dim_size), overlay.ndim)+1):
            if ps.hdr_ext[f'dim_{dim}'] == view.hdr_ext[f'dim_{dim}']\
                and overlay.shape[dim-1] == view.dim_size[dim-1]:
                assert getattr(ps, f'dim_{dim}')      == dim_values[dim-5]
                assert getattr(ps, f'dim_{dim}_avg')  == 0
                assert getattr(ps, f'dim_{dim}_diff') == 0
    # when setting the selected overlay's dim_values only
    dim_values = [1, 4, 0]
    for dim in range(5, min(8, ref_overlay.ndim+1)):
        setattr(ref_ps, f'dim_{dim}', dim_values[dim-5])
        setattr(ref_ps, f'dim_{dim}_avg',  0)
        setattr(ref_ps, f'dim_{dim}_diff', 0)
    for dim in range(5, min(8, ref_overlay.ndim+1)):
        assert getattr(view, f'dim_{dim}')      == dim_values[dim-5]
        assert getattr(view, f'dim_{dim}_avg')  == 0
        assert getattr(view, f'dim_{dim}_diff') == 0
    for overlay in overlayList:
        ps = view.getDataSeries(overlay)
        if ps is None:
            continue
        for dim in range(5, min(len(view.dim_size), overlay.ndim)+1):
            if ps.hdr_ext[f'dim_{dim}'] == view.hdr_ext[f'dim_{dim}']\
                and overlay.shape[dim-1] == view.dim_size[dim-1]:
                assert getattr(ps, f'dim_{dim}')      == dim_values[dim-5]
                assert getattr(ps, f'dim_{dim}_avg')  == 0
                assert getattr(ps, f'dim_{dim}_diff') == 0
    # when setting the global dim_values_avg & dim_values_diff
    dim_values_avg = [0, 0, 1]
    dim_values_diff = [0, 1, 0]
    for dim in range(5, min(8, ref_overlay.ndim+1)):
        # reset diff prop if it was previously enabled, so the next command does not crash
        if getattr(view, f'dim_{dim}_diff') == 1:
            setattr(view, f'dim_{dim}_diff', 0)
        setattr(view, f'dim_{dim}_avg',      dim_values_avg[dim-5])
        if getattr(view, f'dim_{dim}_avg') == 0:
            setattr(view, f'dim_{dim}_diff', dim_values_diff[dim-5])
    for overlay in overlayList:
        ps = view.getDataSeries(overlay)
        if ps is None:
            continue
        for dim in range(5, min(len(view.dim_size), overlay.ndim)+1):
            if ps.hdr_ext[f'dim_{dim}'] == view.hdr_ext[f'dim_{dim}']\
                and overlay.shape[dim-1] == view.dim_size[dim-1]:
                if dim_values_avg[dim-5] == 0 and dim_values_diff[dim-5] == 0:
                    assert getattr(ps, f'dim_{dim}')  == dim_values[dim-5]
                else:
                    assert getattr(ps, f'dim_{dim}')  == 0
                assert getattr(ps, f'dim_{dim}_avg')  == dim_values_avg[dim-5]
                assert getattr(ps, f'dim_{dim}_diff') == dim_values_diff[dim-5]
    # when setting the selected overlay's dim_values_avg & dim_values_diff
    dim_values_avg = [0, 1, 0]
    dim_values_diff = [0, 0, 1]
    for dim in range(5, min(8, ref_overlay.ndim+1)):
        # reset diff prop if it was previously enabled, so the next command does not crash
        if getattr(ref_ps, f'dim_{dim}_diff') == 1:
            setattr(ref_ps, f'dim_{dim}_diff', 0)
        setattr(ref_ps, f'dim_{dim}_avg',      dim_values_avg[dim-5])
        if getattr(ref_ps, f'dim_{dim}_avg') == 0:
            setattr(ref_ps, f'dim_{dim}_diff', dim_values_diff[dim-5])
    for dim in range(5, min(8, ref_overlay.ndim+1)):
        if dim_values_avg[dim-5] == 0 and dim_values_diff[dim-5] == 0:
            assert getattr(view, f'dim_{dim}')  == dim_values[dim-5]
        else:
            assert getattr(view, f'dim_{dim}')  == 0
        assert getattr(view, f'dim_{dim}_avg')  == dim_values_avg[dim-5]
        assert getattr(view, f'dim_{dim}_diff') == dim_values_diff[dim-5]
    for overlay in overlayList:
        ps = view.getDataSeries(overlay)
        if ps is None:
            continue
        for dim in range(5, min(len(view.dim_size), overlay.ndim)+1):
            if ps.hdr_ext[f'dim_{dim}'] == view.hdr_ext[f'dim_{dim}']\
                and overlay.shape[dim-1] == view.dim_size[dim-1]:
                if dim_values_avg[dim-5] == 0 and dim_values_diff[dim-5] == 0:
                    assert getattr(ps, f'dim_{dim}')  == dim_values[dim-5]
                else:
                    assert getattr(ps, f'dim_{dim}')  == 0
                assert getattr(ps, f'dim_{dim}_avg')  == dim_values_avg[dim-5]
                assert getattr(ps, f'dim_{dim}_diff') == dim_values_diff[dim-5]
    
    # Test MRSDimControl when linkDim==False
    view.linkDim = False
    # global values should have all been reset
    assert all(getattr(view, f'dim_{dim}')      == 0 for dim in range(5, 8))
    assert all(getattr(view, f'dim_{dim}_avg')  == 0 for dim in range(5, 8))
    assert all(getattr(view, f'dim_{dim}_diff') == 0 for dim in range(5, 8))
    # set and test each overlay's dim_values, dim_values_avg & dim_values_diff
    dim_values = dict({
        'example_1': [3, 0, 0],
        'example_2': [2, 3],
        'example_3': [0]
    })
    dim_values_avg  = dict({
        'example_1': [0, 1, 0],
        'example_2': [0, 0],
        'example_3': [1]
    })
    dim_values_diff = dict({
        'example_1': [0, 0, 1],
        'example_2': [0, 0],
        'example_3': [0]
    })
    for overlay in overlayList:
        ps = view.getDataSeries(overlay)
        if ps is None:
            continue
        view.displayCtx.selectOverlay(overlay)
        for dim in range(5, min(8, overlay.ndim+1)):
            # re-enable the props to allow new values to be set
            if getattr(ps, f'dim_{dim}_avg') == 1:
                setattr(ps, f'dim_{dim}_avg', 0)
                ps.getProp(f'dim_{dim}_diff').enable(ps)
            if getattr(ps, f'dim_{dim}_diff') == 1:
                setattr(ps, f'dim_{dim}_diff', 0)
                ps.getProp(f'dim_{dim}_avg').enable(ps)
            # now set the previously defined values
            setattr(ps, f'dim_{dim}',          dim_values[overlay.name][dim-5])
            setattr(ps, f'dim_{dim}_avg',      dim_values_avg[overlay.name][dim-5])
            if dim_values_avg[overlay.name][dim-5] == 0:
                setattr(ps, f'dim_{dim}_diff', dim_values_diff[overlay.name][dim-5])
    for overlay in overlayList:
        ps = view.getDataSeries(overlay)
        if ps is None:
            continue
        for dim in range(5, min(8, overlay.ndim+1)):
            assert getattr(ps, f'dim_{dim}')      == dim_values[overlay.name][dim-5]
            assert getattr(ps, f'dim_{dim}_avg')  == dim_values_avg[overlay.name][dim-5]
            assert getattr(ps, f'dim_{dim}_diff') == dim_values_diff[overlay.name][dim-5]

    # Test MRSDimControl when re-enabling linkDim
    # set selectedOverlay to desired image
    idx = 1
    ref_overlay = overlayList[idx]
    view.displayCtx.selectOverlay(ref_overlay)
    ref_ps = view.getDataSeries(ref_overlay)
    for dim in range(5, min(8, ref_overlay.ndim+1)):
        assert getattr(ref_ps, f'dim_{dim}')      == dim_values[ref_overlay.name][dim-5]
        assert getattr(ref_ps, f'dim_{dim}_avg')  == dim_values_avg[ref_overlay.name][dim-5]
        assert getattr(ref_ps, f'dim_{dim}_diff') == dim_values_diff[ref_overlay.name][dim-5]
    view.linkDim = True
    # test that the display name has been updated
    assert view.displayCtx.getDisplay(ref_overlay).name.endswith(' (Link Dim ref)')
    # test that the global values match the selected overlay
    assert view.hdr_ext  == ref_ps.hdr_ext
    assert view.dim_size == ref_overlay.shape
    for dim in range(5, min(8, ref_overlay.ndim+1)):
        assert getattr(ref_ps, f'dim_{dim}')      == dim_values[ref_overlay.name][dim-5]
        assert getattr(ref_ps, f'dim_{dim}_avg')  == dim_values_avg[ref_overlay.name][dim-5]
        assert getattr(ref_ps, f'dim_{dim}_diff') == dim_values_diff[ref_overlay.name][dim-5]
        assert getattr(view, f'dim_{dim}')        == dim_values[ref_overlay.name][dim-5]
        assert getattr(view, f'dim_{dim}_avg')    == dim_values_avg[ref_overlay.name][dim-5]
        assert getattr(view, f'dim_{dim}_diff')   == dim_values_diff[ref_overlay.name][dim-5]
    # test that all matching overlay dimensions match the global values
    for overlay in overlayList:
        ps = view.getDataSeries(overlay)
        if ps is None:
            continue
        for dim in range(5, min(len(view.dim_size), overlay.ndim)+1):
            if ps.hdr_ext[f'dim_{dim}'] == view.hdr_ext[f'dim_{dim}']\
                and overlay.shape[dim-1] == view.dim_size[dim-1]:
                assert getattr(ps, f'dim_{dim}')      == dim_values[ref_overlay.name][dim-5]
                assert getattr(ps, f'dim_{dim}_avg')  == dim_values_avg[ref_overlay.name][dim-5]
                assert getattr(ps, f'dim_{dim}_diff') == dim_values_diff[ref_overlay.name][dim-5]

    # add a new overlay and test that matchs the global values too
    img = fslimage.Image(dim_datadir / (ref_overlay.name + '.nii.gz'))
    overlayList.append(img)
    realYield(20)
    overlay = overlayList[-1]
    ps = view.getDataSeries(overlay)
    for dim in range(5, min(len(view.dim_size), overlay.ndim)+1):
        if ps.hdr_ext[f'dim_{dim}'] == view.hdr_ext[f'dim_{dim}']\
            and overlay.shape[dim-1] == view.dim_size[dim-1]:
            assert getattr(ps, f'dim_{dim}')      == getattr(view, f'dim_{dim}')
            assert getattr(ps, f'dim_{dim}_avg')  == getattr(view, f'dim_{dim}_avg')
            assert getattr(ps, f'dim_{dim}_diff') == getattr(view, f'dim_{dim}_diff')
