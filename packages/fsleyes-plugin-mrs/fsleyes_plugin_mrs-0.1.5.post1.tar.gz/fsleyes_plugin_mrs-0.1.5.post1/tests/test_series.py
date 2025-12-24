#!/usr/bin/env python

'''
test_series.py - Tests methods of MDComplexPowerSpectrumSeries class 
and calcSpectrum function in series.py

Authors: Vasilis Karlaftis    <vasilis.karlaftis@ndcn.ox.ac.uk>

Elements taken from fsleyes/fsleyes/tests/test_powerspectrumseries.py by Paul McCarthy <pauldmccarthy@gmail.com>

Copyright (C) 2025 University of Oxford
'''

import numpy as np
import pytest
from unittest.mock import MagicMock
import os.path as op
from pathlib import Path
import fsl.data.image as fslimage

import fsleyes.plotting.powerspectrumseries as psseries
from fsleyes_plugin_mrs.series import MDComplexPowerSpectrumSeries, calcSpectrum, apodize
from fsleyes_plugin_mrs.views import MRSView

from tests import run_with_fsleyes, realYield

datadir = Path(__file__).parent / 'testdata' / 'svs'

# Mock series data
@pytest.fixture
def mock_series():
    """Returns a configured MDComplexPowerSpectrumSeries with mocked dependencies."""
    overlay = np.random.rand(3, 3, 3, 4, 2, 2, 2).astype(np.complex64)

    overlayList = MagicMock()
    displayCtx = MagicMock()
    plotCanvas = MagicMock()

    opts = MagicMock()
    opts.getVoxel.return_value = [1, 1, 1]
    displayCtx.getOpts.return_value = opts

    series = MDComplexPowerSpectrumSeries(overlay, overlayList, displayCtx, plotCanvas)
    return series

# Test #1: check dataAtCurrentVoxel cashes data correctly
def test_dataAtCurrentVoxel(mock_series):
    data1 = mock_series.dataAtCurrentVoxel()
    data2 = mock_series.dataAtCurrentVoxel()
    assert np.allclose(data1, data2)
    assert data1 is data2

# Test #2: check currentVoxelLocation output when input is of low dimensions (<5)
def test_currentVoxelLocation_lowDim(mock_series):
    loc = mock_series.currentVoxelLocation()
    expected = (1, 1, 1, slice(None), 0, 0, 0)
    assert loc == expected

# Test #3: check currentVoxelLocation output when input is of high dimensions (>=5)
def test_currentVoxelLocation_highDim(mock_series):
    mock_series.dim_5_avg = True
    mock_series.dim_6_diff = True
    mock_series.dim_7 = 1

    loc = mock_series.currentVoxelLocation()
    expected = (1, 1, 1, slice(None), slice(None), slice(0, 2), 1)
    assert loc == expected

# Test #4: check currentVoxelData basic functionality on a single metabolite file
def test_currentVoxelData(mock_series):
    # Define a location where higher dimensions (>=5) are all slices
    loc = (1, 1, 1, slice(None), slice(None), slice(0, 2), slice(None))

    # Fill shape [4, 2, 2, 2] = time x dim5 x dim6 x dim7
    data = np.random.rand(4, 2, 2, 2).astype(np.complex64)
    mock_series.overlay[loc] = data

    result = mock_series.currentVoxelData(loc)
    assert isinstance(result, np.ndarray)
    assert np.iscomplexobj(result)
    assert result.shape[0] == data.shape[0]

# Test #5: check calcSpectrum results match the expected values
def test_calcSpectrum():
    input_data = np.array([1, 2, 3, 4], dtype=np.complex64)

    spec = calcSpectrum(input_data.copy())

    assert np.issubdtype(spec.dtype, np.complexfloating)
    assert spec.shape == input_data.shape

    # Apply the same steps as within the function
    input_data[0] *= 0.5
    expected = np.fft.fftshift(np.fft.fft(input_data))
    assert np.allclose(spec, expected)

    # Check that the function raises an error if input is not an array
    wrong_input = list(input_data)      # set a non np.array input
    with pytest.raises(TypeError):
        calcSpectrum(wrong_input)

# Test #6: check apodize results match the expected values
def test_apodize():
    input_data = np.array([1, 2, 3, 4], dtype=np.complex64)
    data = input_data.copy()
    dwelltime = 0.1
    broadening = 1

    spec = apodize(data, dwelltime, broadening)

    assert np.issubdtype(spec.dtype, np.complexfloating)
    assert spec.shape == input_data.shape

    # Apply the same steps as within the function
    expected = np.exp(-np.linspace(0, dwelltime * (input_data.size - 1), input_data.size) * broadening) * input_data
    assert np.allclose(spec, expected)

    # Check that the function raises an error if any input is not the correct datatype
    wrong_data = list(data)         # set a non np.array input
    wrong_dwelltime = [dwelltime]   # set a non numeric dwelltime
    wrong_broadening = [broadening] # set a non numeric broadening
    with pytest.raises(TypeError):
        apodize(wrong_data, dwelltime, broadening)
    with pytest.raises(TypeError):
        apodize(data, wrong_dwelltime, broadening)
    with pytest.raises(TypeError):
        apodize(data, dwelltime, wrong_broadening)

# Test 7: integration test of MDComplexPowerSpectrumSeries and MRSView on a single metabolite file
def test_MDComplexPowerSpectrumSeries():
    run_with_fsleyes(_test_MDComplexPowerSpectrumSeries)

def _test_MDComplexPowerSpectrumSeries(frame, overlayList, displayCtx):
    img = fslimage.Image(op.join(datadir, 'metab'))
    overlayList.append(img)
    frame.addViewPanel(MRSView)
    frame.viewPanelDefaultLayout(frame.viewPanels[0])
    realYield(100)
    panel = frame.getView(MRSView)[0]
    displayCtx = panel.displayCtx
    opts = displayCtx.getOpts(img)
    ps = MDComplexPowerSpectrumSeries(img, overlayList, displayCtx, panel)
    displayCtx.location = opts.transformCoords((0, 0, 0), 'voxel', 'display')

    expx = psseries.calcFrequencies(img.shape[3], ps.sampleTime, img.dtype)
    expy = calcSpectrum(img[0, 0, 0, :].copy())

    xdata, ydata = ps.getData()
    assert np.all(np.isclose(xdata, expx))
    assert np.all(np.isclose(ydata, expy.real))

    panel.plotReal = False
    xdata, ydata = ps.getData()
    assert xdata is None
    assert ydata is None

    panel.plotImaginary = True
    panel.plotMagnitude = True
    panel.plotPhase     = True
    ips, mps, pps = ps.extraSeries()

    assert np.all(np.isclose(expy.imag,                ips.getData()[1]))
    assert np.all(np.isclose(psseries.magnitude(expy), mps.getData()[1]))
    assert np.all(np.isclose(psseries.phase(    expy), pps.getData()[1]))

    panel.plotReal               = True
    ps.zeroOrderPhaseCorrection  = 1
    ps.firstOrderPhaseCorrection = 2    # this is now in milliseconds

    exp = psseries.phaseCorrection(expy, expx, 1, 0.002)    # this function still uses input in seconds
    assert np.all(np.isclose(exp.real,                ps .getData()[1]))
    assert np.all(np.isclose(exp.imag,                ips.getData()[1]))
    assert np.all(np.isclose(psseries.magnitude(exp), mps.getData()[1]))
    assert np.all(np.isclose(psseries.phase(    exp), pps.getData()[1]))
