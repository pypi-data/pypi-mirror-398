#!/usr/bin/env python

'''
test_mrsfittool.py - Tests methods of MRSFitTool class in tools.py

Authors: Vasilis Karlaftis    <vasilis.karlaftis@ndcn.ox.ac.uk>

Copyright (C) 2025 University of Oxford
'''

import os.path as op
import os, shutil, wx, json
from pathlib import Path
from file_tree import FileTree, Template
from unittest.mock import patch, MagicMock, mock_open

import fsl.data.image as fslimage
from tests import run_with_viewpanel, realYield, capture_logs
from tests import capture_logs

from fsleyes.views.orthopanel       import OrthoPanel
from fsleyes_plugin_mrs.tools       import MRSFitTool, MRSResultsControl
from fsleyes_plugin_mrs.views       import MRSView

mrsidatadir = Path(__file__).parent / 'testdata' / 'mrsi'
svsdatadir  = Path(__file__).parent / 'testdata' / 'svs'


# Mock FileTree
def mock_tree(filename):
    tree = MagicMock()
    tree.get.return_value = filename
    template_key = "fit-" + filename.name.replace('.nii.gz', '')
    tree._templates = {
        template_key: Template("dummy_pattern", "dummy_unique"),
        "other": "not_a_template"
    }
    return tree

# Mock colourscheme
def mock_colourscheme():
    colourscheme = {
        "fit-fit": {
            "lineWidth": 2,
            "colour": [1, 0, 0]
        },
        "fit-baseline": {
            "lineWidth": 0.5,
            "lineStyle": '--',
            "colour": [0, 0.5, 0.5]
        },
        "fit-residual": {
            "linewidth": 2,  # invalid param for testing
            "colour": [0.2, 0.2, 0.2],
            "alpha": 0.5
        }
    }
    return colourscheme

# Mock DirDialog
class DummyDirDialog:
    def __init__(self, *a, **k):
        self._path = str(k.pop("set_path", "/default/path"))
    def ShowModal(self):
        return wx.ID_OK
    def GetPath(self):
        return self._path

# Convert overlayList to list of strings
def overlay_to_string(overlayList):
    return [repr(ovl) for ovl in overlayList]

# Test #1: check _displayFitData functionality
def test_displayFitData():
    run_with_viewpanel(_test_displayFitData, MRSView)

def _test_displayFitData(view, overlayList, displayCtx):
    tool = MRSFitTool(overlayList, displayCtx, view.frame)
    logger, handler, log_stream = capture_logs('fsleyes_plugin_mrs.tools')

    initial_overlayList = overlay_to_string(overlayList)

    # Test if file does not exist results in early return
    fit_file = 'fit'
    with patch('fsleyes_plugin_mrs.tools.Path.exists', return_value=False):
        tool.mrsi_tree = mock_tree(mrsidatadir / (fit_file + '.nii.gz'))
        tool._displayFitData(None, fit_file, {})
        handler.flush()
        log_output = log_stream.getvalue()
        assert 'WARNING:' in log_output
        assert overlay_to_string(overlayList) == initial_overlayList
        # Clear the stream for the next log
        log_stream.truncate(0)
        log_stream.seek(0)

    # Test if file exists then it is added to overlayList
    fit_file = 'fit'
    with patch('fsleyes_plugin_mrs.tools.Path.exists', return_value=True):
        tool.mrsi_tree = mock_tree(mrsidatadir / (fit_file + '.nii.gz'))
        tool._displayFitData(None, fit_file, {})
        new_overlayList = overlay_to_string(overlayList)
        assert new_overlayList[:-1] == initial_overlayList
        assert new_overlayList[-1]  == repr(fslimage.Image(str(mrsidatadir / (fit_file + '.nii.gz'))))
    
    # Test if empty colourscheme results in using defaults
    fit_files = ['fit', 'residual', 'baseline']
    for fit in fit_files:
        tool.mrsi_tree = mock_tree(mrsidatadir / (fit + '.nii.gz'))
        tool.colourscheme = {}
        tool._displayFitData(None, fit, {})
        ps = view.getDataSeries(overlayList[-1])
        assert ps.lineStyle == '-'
        assert ps.alpha     == 1.0
        assert ps.lineWidth == 1

    # Get non-empty colourscheme for subsequent tests
    tool.colourscheme = mock_colourscheme()
    
    # Test colourscheme type with partially invalid fields
    fit_file = 'residual'
    tool.mrsi_tree = mock_tree(mrsidatadir / (fit_file + '.nii.gz'))
    tool._displayFitData(None, fit_file, tool.colourscheme['fit-'+fit_file])
    ps = view.getDataSeries(overlayList[-1])
    handler.flush()
    log_output = log_stream.getvalue()
    assert 'WARNING:' in log_output
    assert not hasattr(ps, "linewidth")
    assert ps.colour[0:3] == tuple(tool.colourscheme['fit-'+fit_file]['colour'])
    assert ps.alpha       == tool.colourscheme['fit-'+fit_file]['alpha']
    assert ps.lineStyle   == '-'
    assert ps.lineWidth   == 1
    # Clear the stream for the next log
    log_stream.truncate(0)
    log_stream.seek(0)

    # Test _colourscheme type with valid fields
    fit_file = 'fit'
    tool.mrsi_tree = mock_tree(mrsidatadir / (fit_file + '.nii.gz'))
    tool._displayFitData(None, fit_file, tool.colourscheme['fit-'+fit_file])
    ps = view.getDataSeries(overlayList[-1])
    assert ps.colour[0:3] == tuple(tool.colourscheme['fit-'+fit_file]['colour'])
    assert ps.lineWidth   == tool.colourscheme['fit-'+fit_file]['lineWidth']
    assert ps.lineStyle   == '-'
    assert ps.alpha       == 1.0

    fit_file = 'baseline'
    tool.mrsi_tree = mock_tree(mrsidatadir / (fit_file + '.nii.gz'))
    tool._displayFitData(None, fit_file, tool.colourscheme['fit-'+fit_file])
    ps = view.getDataSeries(overlayList[-1])
    assert ps.colour[0:3] == tuple(tool.colourscheme['fit-'+fit_file]['colour'])
    assert ps.lineWidth   == tool.colourscheme['fit-'+fit_file]['lineWidth']
    assert ps.lineStyle   == tool.colourscheme['fit-'+fit_file]['lineStyle']
    assert ps.alpha       == 1.0
    
    # Remove logger handler
    logger.removeHandler(handler)

# Test #2: check loadFit functionality
def test_loadFit():
    run_with_viewpanel(_test_loadFit, MRSView)

def _test_loadFit(view, overlayList, displayCtx):
    tool = MRSFitTool(overlayList, displayCtx, view.frame)
    logger, handler, log_stream = capture_logs('fsleyes_plugin_mrs.tools')

    # Get non-empty colourscheme for subsequent tests
    tool.colourscheme = mock_colourscheme()

    # Test if file is not in colourscheme keys results in using defaults
    # (this inherently tests for keys not starting with "fit-")
    fit_file = 'data'
    initial_overlayList = overlay_to_string(overlayList)
    tool.mrsi_tree = mock_tree(mrsidatadir / (fit_file + '.nii.gz'))
    tool.loadFit(None)
    new_overlayList = overlay_to_string(overlayList)
    ps = view.getDataSeries(overlayList[-1])
    handler.flush()
    log_output = log_stream.getvalue()
    assert 'WARNING:' in log_output
    assert new_overlayList[:-1] == initial_overlayList
    assert new_overlayList[-1]  == repr(fslimage.Image(str(mrsidatadir / (fit_file + '.nii.gz'))))
    assert ps.lineStyle         == '-'
    assert ps.alpha             == 1.0
    assert ps.lineWidth         == 1
    # Clear the stream for the next log
    log_stream.truncate(0)
    log_stream.seek(0)

    # Test if file is in colourscheme keys
    # (this inherently tests for keys not starting with "fit-")
    fit_file = 'fit'
    initial_overlayList = overlay_to_string(overlayList)
    tool.mrsi_tree = mock_tree(mrsidatadir / (fit_file + '.nii.gz'))
    tool.loadFit(None)
    new_overlayList = overlay_to_string(overlayList)
    ps = view.getDataSeries(overlayList[-1])
    handler.flush()
    log_output = log_stream.getvalue()
    assert 'WARNING:' not in log_output
    assert new_overlayList[:-1] == initial_overlayList
    assert new_overlayList[-1]  == repr(fslimage.Image(str(mrsidatadir / (fit_file + '.nii.gz'))))
    assert ps.colour[0:3]       == tuple(tool.colourscheme['fit-'+fit_file]['colour'])
    assert ps.lineWidth         == tool.colourscheme['fit-'+fit_file]['lineWidth']
    assert ps.lineStyle         == '-'
    assert ps.alpha             == 1.0
    # Clear the stream for the next log
    log_stream.truncate(0)
    log_stream.seek(0)

    # Remove logger handler
    logger.removeHandler(handler)

# Test #3: check createResultsPanel and _setUpOrtho functionality
def test_createResultsPanel():
    run_with_viewpanel(_test_createResultsPanel, MRSView)

def _test_createResultsPanel(view, overlayList, displayCtx):
    tool = MRSFitTool(overlayList, displayCtx, view.frame)

    tool.metab_list      = ['Asc', 'Cr+PCr', 'NAA']
    tool.display_options = ['raw', 'internal', 'SNR']
    tool.mrsi_tree       = None
    tool.colourscheme    = None

    ortho = tool.createResultsPanel()

    # Test if OrthoPanel and MRSResultsControl are created
    assert isinstance(ortho, OrthoPanel)
    assert ortho.isPanelOpen(MRSResultsControl)
    # Test _setUpOrtho method
    orthoOpts = ortho.sceneOpts
    assert orthoOpts.showColourBar      == True
    assert orthoOpts.colourBarLocation  == 'left'
    assert orthoOpts.colourBarLabelSide == 'top-left'
    assert orthoOpts.labelSize          == 10

    # Test if overlayList is empty, then all Orthos are closed and one is reused
    for i in range(5):
        view.frame.addViewPanel(OrthoPanel)
        realYield()
    ortho = tool.createResultsPanel()
    assert len(overlayList) == 0
    assert len(view.frame.getView(OrthoPanel)) == 1

    # Test if the overlayList only has a T1 (non-MRS data), then the behaviour is the same as above
    img = fslimage.Image(op.join(svsdatadir, 'T1'))
    overlayList.append(img)
    realYield(25)
    for i in range(5):
        view.frame.addViewPanel(OrthoPanel)
        realYield()
    ortho = tool.createResultsPanel()
    assert len(overlayList) > 0
    assert len(view.frame.getView(OrthoPanel)) == 1

    # Test if the overlayList has some MRS data, then all previous Orthos are retained and a new one is created
    img = fslimage.Image(op.join(svsdatadir, 'metab'))
    overlayList.append(img)
    realYield(25)
    for i in range(5):
        view.frame.addViewPanel(OrthoPanel)
        realYield()
    initial_orthos = view.frame.getView(OrthoPanel)
    ortho = tool.createResultsPanel()
    assert len(overlayList) > 0
    create_ortho = False
    for overlay in overlayList:
        ps = view.getDataSeries(overlay)
        if ps is not None:
            create_ortho = True
            break
    assert create_ortho == True
    assert len(view.frame.getView(OrthoPanel)) == len(initial_orthos) + 1

# Test #4: check _checkColourschemeValidity functionality
def test_checkColourschemeValidity():
    tool = MRSFitTool([], None, None)
    logger, handler, log_stream = capture_logs('fsleyes_plugin_mrs.tools')

    # mock a valid json file
    mock_data = {"a": 1, "b": 2}
    m = mock_open(read_data=json.dumps(mock_data))

    # Test a valid json file
    with patch("builtins.open", m), patch("json.load", return_value=mock_data):
        tool._checkColourschemeValidity("valid.json")
        handler.flush()
        log_output = log_stream.getvalue()
        assert 'WARNING:' not in log_output
        assert tool.colourscheme == mock_data
        # Clear the stream for the next log
        log_stream.truncate(0)
        log_stream.seek(0)

    # Test a non-existing json file
    with patch("builtins.open", side_effect=FileNotFoundError):
        tool._checkColourschemeValidity("missing.json")
        handler.flush()
        log_output = log_stream.getvalue()
        assert 'WARNING:' in log_output
        assert "not found" in log_output
        assert tool.colourscheme is None
        # Clear the stream for the next log
        log_stream.truncate(0)
        log_stream.seek(0)

    # Test a json file with invalid format
    m = mock_open(read_data="{ invalid json }")
    with patch("builtins.open", m), patch("json.load", side_effect=json.JSONDecodeError("bad", "doc", 0)):
        tool._checkColourschemeValidity("invalid.json")
        handler.flush()
        log_output = log_stream.getvalue()
        assert 'WARNING:' in log_output
        assert "invalid JSON format" in log_output
        assert tool.colourscheme is None
        # Clear the stream for the next log
        log_stream.truncate(0)
        log_stream.seek(0)

    # Test a json file that raises an unexpected error
    m = mock_open(read_data="{}")
    with patch("builtins.open", m), patch("json.load", side_effect=RuntimeError("Unexpected crash")):
        tool._checkColourschemeValidity("crashed.json")
        handler.flush()
        log_output = log_stream.getvalue()
        assert 'WARNING:' in log_output
        assert "Unexpected error" in log_output
        assert tool.colourscheme is None
        # Clear the stream for the next log
        log_stream.truncate(0)
        log_stream.seek(0)

    # Remove logger handler
    logger.removeHandler(handler)

# Test #5: check identifyColourscheme and _findColourschemeFile functionality
def test_identifyColourscheme(tmp_path):
    tool = MRSFitTool([], None, None)
    logger, handler, log_stream = capture_logs('fsleyes_plugin_mrs.tools')

    # Test case if valid filename does not exist results in using the default file
    file = tmp_path / "my_colourscheme_wrong_name.json"
    mock_json = {"a": 1, "b": 2}
    with open(file, "w") as f:
        json.dump(mock_json, f)
    tool.identifyColourscheme(tmp_path)
    handler.flush()
    log_output = log_stream.getvalue()
    assert 'WARNING:' in log_output
    assert "No *colourscheme.json file found" in log_output
    # load default colourscheme file
    default_colourscheme = Path(__file__).parent.parent / "fsleyes_plugin_mrs" / "default_colourscheme.json"
    with open(default_colourscheme, 'r') as f:
        default_colourscheme = json.load(f)
    assert tool.colourscheme == default_colourscheme
    assert tool.colourscheme != mock_json
    # Clear the stream for the next log
    log_stream.truncate(0)
    log_stream.seek(0)

    # Test case if one file exists
    file = tmp_path / "my_1st_colourscheme.json"
    mock_json_1 = {"a": 1, "b": 2}
    with open(file, "w") as f:
        json.dump(mock_json_1, f)
    tool.identifyColourscheme(tmp_path)
    handler.flush()
    log_output = log_stream.getvalue()
    assert 'WARNING:' not in log_output
    assert tool.colourscheme == mock_json_1
    # Clear the stream for the next log
    log_stream.truncate(0)
    log_stream.seek(0)

    # Test case if multiple files exist
    file = tmp_path / "my_2nd_colourscheme.json"
    mock_json_2 = {"c": 3, "d": 4}
    with open(file, "w") as f:
        json.dump(mock_json_2, f)
    tool.identifyColourscheme(tmp_path)
    handler.flush()
    log_output = log_stream.getvalue()
    assert 'WARNING:' in log_output
    assert "Multiple *colourscheme.json files found" in log_output
    assert tool.colourscheme == mock_json_1
    assert tool.colourscheme != mock_json_2
    # Clear the stream for the next log
    log_stream.truncate(0)
    log_stream.seek(0)

    # Remove logger handler
    logger.removeHandler(handler)

# Test #6: check _findTreeFile functionality
def test_findTreeFile(tmp_path):
    tool = MRSFitTool([], None, None)
    logger, handler, log_stream = capture_logs('fsleyes_plugin_mrs.tools')

    # Test case if tree file does not exist results in using the default file
    tool._findTreeFile(tmp_path)
    handler.flush()
    log_output = log_stream.getvalue()
    assert 'WARNING:' in log_output
    assert "No .tree file found" in log_output
    # load default tree file
    default_tree = FileTree.read(Path(__file__).parent.parent / "fsleyes_plugin_mrs" /
                            'default_mrsi.tree', top_level=tmp_path)
    assert tool.mrsi_tree.to_string() == default_tree.to_string()
    # Clear the stream for the next log
    log_stream.truncate(0)
    log_stream.seek(0)

    # Test case if one file exists
    file1 = tmp_path / "1st.tree"
    mock_tree_1 = (
        "raw\n"
        "    {metab}.nii.gz (raw-concentrations)\n"
        "fit\n"
        "    fit.nii.gz (fit-fit)\n"
    )
    FileTree.from_string(mock_tree_1).write(file1)
    tool._findTreeFile(tmp_path)
    handler.flush()
    log_output = log_stream.getvalue()
    assert 'WARNING:' not in log_output
    # read the file again as writing it could change the order of the folders alphabetically
    assert tool.mrsi_tree.to_string() == FileTree.read(file1).to_string()
    # Clear the stream for the next log
    log_stream.truncate(0)
    log_stream.seek(0)

    # Test case if multiple files exist
    file2 = tmp_path / "2nd.tree"
    mock_tree_2 = (
        "internal\n"
        "    {metab}.nii.gz (conc-internal)\n"
        "fit\n"
        "    baseline.nii.gz (fit-baseline)\n"
    )
    FileTree.from_string(mock_tree_2).write(file2)
    tool._findTreeFile(tmp_path)
    handler.flush()
    log_output = log_stream.getvalue()
    assert 'WARNING:' in log_output
    assert "Multiple .tree files found" in log_output
    # read the file again as writing it could change the order of the folders alphabetically
    assert tool.mrsi_tree.to_string() == FileTree.read(file1).to_string()
    assert tool.mrsi_tree.to_string() != FileTree.read(file2).to_string()
    # Clear the stream for the next log
    log_stream.truncate(0)
    log_stream.seek(0)

    # Remove logger handler
    logger.removeHandler(handler)

# Test #7: check _checkTreeValidity functionality
def test_checkTreeValidity(tmp_path):
    tool = MRSFitTool([], None, None)
    logger, handler, log_stream = capture_logs('fsleyes_plugin_mrs.tools')

    # Test case of an invalid tree
    file = tmp_path / "invalid.tree"
    mock_tree = (
        "internal\n"
        "    {metab}.nii.gz (conc-internal)\n"
        "fit\n"
        "    baseline.nii.gz (fit-baseline)\n"
    )
    FileTree.from_string(mock_tree).write(file)
    tool.mrsi_tree = FileTree.read(file, top_level=tmp_path)
    ref_key = tool._checkTreeValidity()
    handler.flush()
    log_output = log_stream.getvalue()
    assert 'ERROR:' in log_output
    assert ref_key is None
    # Clear the stream and file for the next log
    log_stream.truncate(0)
    log_stream.seek(0)

    # Test case of a valid tree with no placeholders
    file = tmp_path / "valid_no_plc.tree"
    mock_tree = (
        "raw\n"
        "    Asc.nii.gz (raw-concentrations)\n"
        "fit\n"
        "    fit.nii.gz (fit-fit)\n"
    )
    FileTree.from_string(mock_tree).write(file)
    tool.mrsi_tree = FileTree.read(file, top_level=tmp_path)
    ref_key = tool._checkTreeValidity()
    handler.flush()
    log_output = log_stream.getvalue()
    assert 'ERROR:' not in log_output
    assert ref_key is None
    # Clear the stream for the next log
    log_stream.truncate(0)
    log_stream.seek(0)

    # Test case of a valid tree
    file = tmp_path / "valid.tree"
    mock_tree = (
        "raw\n"
        "    {metab}.nii.gz (raw-concentrations)\n"
        "fit\n"
        "    fit.nii.gz (fit-fit)\n"
    )
    FileTree.from_string(mock_tree).write(file)
    tool.mrsi_tree = FileTree.read(file, top_level=tmp_path)
    ref_key = tool._checkTreeValidity()
    handler.flush()
    log_output = log_stream.getvalue()
    assert 'ERROR:' not in log_output
    assert ref_key == 'raw-concentrations'
    # Clear the stream for the next log
    log_stream.truncate(0)
    log_stream.seek(0)
    
    # Remove logger handler
    logger.removeHandler(handler)

# Test #8: check _getListOfMetabolites functionality
def test_getListOfMetabolites(tmp_path):
    tool = MRSFitTool([], None, None)
    logger, handler, log_stream = capture_logs('fsleyes_plugin_mrs.tools')

    # Test empty ref_key results in early return
    tool._findTreeFile(tmp_path)
    tool._getListOfMetabolites(None)
    handler.flush()
    log_output = log_stream.getvalue()
    assert 'ERROR:' in log_output
    assert tool.mrsi_tree.metab_ph is None
    assert tool.metab_list == []
    # Clear the stream for the next log
    log_stream.truncate(0)
    log_stream.seek(0)

    # Test tree with empty files
    file = tmp_path / "no_files.tree"
    mock_tree = (
        "raw\n"
        "    {metab}.nii.gz (raw-concentrations)\n"
        "fit\n"
        "    fit.nii.gz (fit-fit)\n"
    )
    FileTree.from_string(mock_tree).write(file)
    tool.mrsi_tree = FileTree.read(file, top_level=tmp_path)
    os.makedirs(tmp_path / "raw", exist_ok=True)
    ref_key = tool._checkTreeValidity()
    tool._getListOfMetabolites(ref_key)
    assert tool.mrsi_tree.metab_ph == "metab"
    assert tool.metab_list == []

    # Test tree with single placeholder
    file = tmp_path / "single.tree"
    mock_tree = (
        "raw\n"
        "    {metab}.nii.gz (raw-concentrations)\n"
        "fit\n"
        "    fit.nii.gz (fit-fit)\n"
    )
    FileTree.from_string(mock_tree).write(file)
    tool.mrsi_tree = FileTree.read(file, top_level=tmp_path)
    placeholders = ['Asc', 'Cr+PCr', 'NAA']
    os.makedirs(tmp_path / "raw", exist_ok=True)
    for f in placeholders:
        (tmp_path / "raw" / f"{f}.nii.gz").touch()
    ref_key = tool._checkTreeValidity()
    tool._getListOfMetabolites(ref_key)
    handler.flush()
    log_output = log_stream.getvalue()
    assert 'ERROR:'   not in log_output
    assert 'WARNING:' not in log_output
    assert tool.mrsi_tree.metab_ph == "metab"
    assert tool.metab_list == placeholders
    # Clear the stream for the next log
    log_stream.truncate(0)
    log_stream.seek(0)
    
    # Test tree with multiple placeholders
    file = tmp_path / "multi.tree"
    mock_tree = (
        "raw_{subj}\n"
        "    {metab}.nii.gz (raw-concentrations)\n"
        "fit\n"
        "    fit.nii.gz (fit-fit)\n"
    )
    FileTree.from_string(mock_tree).write(file)
    tool.mrsi_tree = FileTree.read(file, top_level=tmp_path)
    subjects     = ['subj1', 'subj2']
    placeholders = ['Asc', 'Cr+PCr', 'NAA']
    for subj in subjects:
        os.makedirs(tmp_path / ("raw_" + subj), exist_ok=True)
        for f in placeholders:
            (tmp_path / ("raw_" + subj) / f"{f}.nii.gz").touch()
    ref_key = tool._checkTreeValidity()
    tool._getListOfMetabolites(ref_key)
    handler.flush()
    log_output = log_stream.getvalue()
    assert 'ERROR:'   not in log_output
    assert 'WARNING:' in log_output
    assert "Multiple placeholders" in log_output
    assert tool.mrsi_tree.metab_ph == "metab"
    assert tool.metab_list == placeholders
    # Clear the stream for the next log
    log_stream.truncate(0)
    log_stream.seek(0)

    # Remove logger handler
    logger.removeHandler(handler)

# Test #9: check identifyResults functionality
def test_identifyResults(tmp_path):
    tool = MRSFitTool([], None, None)
    logger, handler, log_stream = capture_logs('fsleyes_plugin_mrs.tools')

    # Test case of an invalid tree
    file = tmp_path / "invalid.tree"
    mock_tree = (
        "internal\n"
        "    {metab}.nii.gz (conc-internal)\n"
    )
    FileTree.from_string(mock_tree).write(file)
    placeholders = ['Asc', 'Cr+PCr', 'NAA']
    for fd in ["internal"]:
        os.makedirs(tmp_path / fd, exist_ok=True)
        for f in placeholders:
            (tmp_path / fd / f"{f}.nii.gz").touch()

    tool.identifyResults(tmp_path)
    handler.flush()
    log_output = log_stream.getvalue()
    assert 'ERROR:' in log_output
    assert "The mrsi_tree does not contain the mandatory" in log_output
    assert tool.mrsi_tree.metab_ph is None
    assert tool.metab_list      == []
    assert tool.display_options == []
    # Clear the stream and file for the next log
    log_stream.truncate(0)
    log_stream.seek(0)
    file.unlink()

    # Test case of a valid tree with no placeholders
    file = tmp_path / "valid_no_plc.tree"
    mock_tree = (
        "raw_no_plc\n"
        "    Asc.nii.gz (raw-concentrations)\n"
    )
    FileTree.from_string(mock_tree).write(file)
    os.makedirs(tmp_path / "raw_no_plc", exist_ok=True)
    (tmp_path / "raw_no_plc" / "Asc.nii.gz").touch()

    tool.identifyResults(tmp_path)
    handler.flush()
    log_output = log_stream.getvalue()
    assert 'ERROR:' in log_output
    assert "No required placeholders found" in log_output
    assert tool.mrsi_tree.metab_ph is None
    assert tool.metab_list      == []
    assert tool.display_options == []
    # Clear the stream and file for the next log
    log_stream.truncate(0)
    log_stream.seek(0)
    file.unlink()

    # Test tree with empty files
    file = tmp_path / "no_files.tree"
    mock_tree = (
        "raw_no_files\n"
        "    {metab}.nii.gz (raw-concentrations)\n"
    )
    FileTree.from_string(mock_tree).write(file)
    os.makedirs(tmp_path / "raw_no_files", exist_ok=True)

    tool.identifyResults(tmp_path)
    assert tool.mrsi_tree.metab_ph == "metab"
    assert tool.metab_list         == []
    assert tool.display_options    == ["raw-concentrations"]
    file.unlink()
   
    # Test case of a valid tree with various key options
    file = tmp_path / "valid.tree"
    mock_tree = (
        "raw\n"
        "    {metab}.nii.gz (raw-concentrations)\n"
        "no_key\n"
        "    {metab}.nii.gz\n"
        "no_folder_{metab}.nii.gz (key1)\n"
        "other_plc\n"
        "    {other}.nii.gz (key2)\n"
        "optional\n"
        "    [{metab}.nii.gz] (key3)\n"
        "no_plc\n"
        "    my_file.nii.gz (key4)\n"
    )
    FileTree.from_string(mock_tree).write(file)
    placeholders = ['Asc', 'Cr+PCr', 'NAA']
    for fd in ["raw", "no_key", ".", "optional"]:
        os.makedirs(tmp_path / fd, exist_ok=True)
        for f in placeholders:
            (tmp_path / fd / f"{f}.nii.gz").touch()
    os.makedirs(tmp_path / "other_plc", exist_ok=True)
    for f in ['A', 'B', 'C']:
        (tmp_path / "other_plc" / f"{f}.nii.gz").touch()
    os.makedirs(tmp_path / "no_plc", exist_ok=True)
    (tmp_path / "no_plc" / "my_file.nii.gz").touch()

    tool.identifyResults(tmp_path)
    assert tool.mrsi_tree.metab_ph      == "metab"
    assert tool.metab_list              == placeholders
    assert sorted(tool.display_options) == sorted(['raw-concentrations', '{metab}', 'key1', 'key3'])

    # Remove logger handler
    logger.removeHandler(handler)

# Test #10: check loadResults functionality (without errors)
def test_loadResults(monkeypatch, tmp_path):
    run_with_viewpanel(_test_loadResults, MRSView, tmp_path, monkeypatch)

def _test_loadResults(view, overlayList, displayCtx, tmp_path, monkeypatch):
    tool = MRSFitTool(overlayList, displayCtx, view.frame)
    logger, handler, log_stream = capture_logs("fsleyes_plugin_mrs.tools")

    # Create a valid tree
    file = tmp_path / "valid.tree"
    mock_tree = (
        "raw\n"
        "    {metab}.nii.gz (raw-concentrations)\n"
        "fit\n"
        "    fit.nii.gz (fit-fit)\n"
        "    residual.nii.gz (fit-residual)\n"
    )
    FileTree.from_string(mock_tree).write(file)

    # Create dummy data files
    metab_dir = tmp_path / "raw"
    fit_dir   = tmp_path / "fit"
    os.makedirs(metab_dir, exist_ok=True)
    os.makedirs(fit_dir, exist_ok=True)
    placeholders = ["Asc", "NAA"]
    for f in placeholders:
        (metab_dir / f"{f}.nii.gz").touch()
    shutil.copy(mrsidatadir / "fit.nii.gz",       fit_dir)
    shutil.copy(mrsidatadir / "residual.nii.gz", fit_dir)

    # Create a valid colourscheme
    colourscheme_file = tmp_path / "my_colourscheme.json"
    colourscheme = mock_colourscheme()
    with open(colourscheme_file, "w") as f:
        json.dump(colourscheme, f)

    # Patch wx.DirDialog to return the tmp_path as the selected folder
    monkeypatch.setattr("fsleyes_plugin_mrs.tools.wx.DirDialog", 
                        lambda *a, **k: DummyDirDialog(set_path=tmp_path, *a, **k))

    initial_overlayList = overlay_to_string(overlayList)

    tool.loadResults()
    handler.flush()
    log_output = log_stream.getvalue()

    assert "ERROR:" not in log_output
    # Assertions for identifyResults step
    assert tool.mrsi_tree.metab_ph  == "metab"
    assert tool.metab_list          == placeholders
    assert tool.display_options     == ['raw-concentrations']
    # Assertions for identifyColourscheme step
    assert tool.colourscheme == colourscheme
    # Assertions for loadFit step
    new_overlayList = overlay_to_string(overlayList)
    assert new_overlayList[:-2] == initial_overlayList
    assert len(new_overlayList) == len(initial_overlayList) + 2
    assert new_overlayList[-2]  == repr(fslimage.Image(str(fit_dir / "fit.nii.gz")))
    assert new_overlayList[-1]  == repr(fslimage.Image(str(fit_dir / "residual.nii.gz")))

    # Remove logger handler
    logger.removeHandler(handler)

# Test #11: check loadResults functionality (with errors)
def test_loadResults_failure(monkeypatch, tmp_path):
    run_with_viewpanel(_test_loadResults_failure, MRSView, tmp_path, monkeypatch)

def _test_loadResults_failure(view, overlayList, displayCtx, tmp_path, monkeypatch):
    tool = MRSFitTool(overlayList, displayCtx, view.frame)
    logger, handler, log_stream = capture_logs("fsleyes_plugin_mrs.tools")

    # Test case of user cancelling
    class DummyCancelDialog:
        def __init__(self, *a, **k):
            self._path = str(k.pop("set_path", "/default/path"))
        def ShowModal(self):
            return wx.ID_CANCEL
        def GetPath(self):
            return self._path

    monkeypatch.setattr("fsleyes_plugin_mrs.tools.wx.DirDialog", 
                        lambda *a, **k: DummyCancelDialog(set_path=tmp_path, *a, **k))
    initial_overlayList = overlay_to_string(overlayList)
    tool.loadResults()
    handler.flush()
    log_output = log_stream.getvalue()
    assert "ERROR:" not in log_output
    assert not hasattr(tool, "mrsi_tree")
    assert not hasattr(tool, "metab_list")
    assert not hasattr(tool, "display_options")
    assert not hasattr(tool, "colourscheme")
    assert overlay_to_string(overlayList) == initial_overlayList
    # Clear the stream for the next log
    log_stream.truncate(0)
    log_stream.seek(0)

    # Test case of an invalid tree
    file = tmp_path / "invalid.tree"
    mock_tree = (
        "internal\n"
        "    {metab}.nii.gz (conc-internal)\n"
        "fit\n"
        "    baseline.nii.gz (fit-baseline)\n"
    )
    FileTree.from_string(mock_tree).write(file)

    # Create dummy data files
    fit_dir = tmp_path / "fit"
    os.makedirs(fit_dir, exist_ok=True)
    (fit_dir / "baseline.nii.gz").touch()

    monkeypatch.setattr("fsleyes_plugin_mrs.tools.wx.DirDialog", 
                        lambda *a, **k: DummyDirDialog(set_path=tmp_path, *a, **k))

    initial_overlayList = overlay_to_string(overlayList)
    tool.loadResults()
    handler.flush()
    log_output = log_stream.getvalue()    
    assert "ERROR:" in log_output
    assert overlay_to_string(overlayList) == initial_overlayList
    assert tool.mrsi_tree.to_string()     == FileTree.read(file).to_string()
    assert tool.metab_list                == []
    assert tool.display_options           == []
    # load default colourscheme file
    default_colourscheme = Path(__file__).parent.parent / "fsleyes_plugin_mrs" / "default_colourscheme.json"
    with open(default_colourscheme, 'r') as f:
        default_colourscheme = json.load(f)
    assert tool.colourscheme == default_colourscheme
    # Clear the stream for the next log
    log_stream.truncate(0)
    log_stream.seek(0)

    # Remove logger handler
    logger.removeHandler(handler)
