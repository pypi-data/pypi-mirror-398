#!/usr/bin/env python

'''
test_plugin_load.py - Tests for basic plugin functionality.
Here we test that fsleyes loads without error when the plugin is present.
We also test that it loads with the default mrs layout.

Authors: Will Clarke          <william.clarke@ndcn.ox.ac.uk>

Copyright (C) 2025 University of Oxford
'''

from pathlib import Path
from subprocess import check_call

# Data paths
datadir = Path(__file__).parent / 'testdata' / 'svs'
t1 = datadir / 'T1.nii.gz'
svs = datadir / 'metab.nii.gz'


def test_load(tmp_path):
    assert not check_call(['render',
                           '-of', tmp_path / 'test.png',
                           str(t1),
                           str(svs)])


def test_load_mrs_layout(tmp_path):
    assert not check_call(['render',
                           '-of', tmp_path / 'test.png',
                           '-smrs',
                           str(t1),
                           str(svs)])
