#!/usr/env/bin python3
######## Globals ########
TESTORIGIN = "test_merge_origin.hdf5"
TESTHEAD = "test_merge_head.hdf5"

######## Imports ########
from xdata import Database
from pathlib import Path
import numpy as np

######## Functions ########

def test_merge():
    ## Create database A ##
    dbA = Database(TESTORIGIN)
    # Create top level model group
    dbA.create_group('model')
    dbA.attr_set(    'model', 'model', 'model')
    # Create a subgroup
    dbA.create_group('model/subgroup_A')
    dbA.attr_set(    'model/subgroup_A', 'subgroup_property', 'A')
    # Create a parameters group
    dbA.create_group('model/subgroup_A/params')
    dbA.attr_set(    'model/subgroup_A/params', 'parameter', 'A')
    # Create a data group
    dbA.create_group('model/subgroup_A/data')
    # Create some data
    dataA = np.zeros(7)
    dbA.dset_set('model/subgroup_A/data/dataset', dataA)
    dbA.attr_set('model/subgroup_A/data/dataset', 'size', dataA.size)
    dbA.attr_set('model/subgroup_A/data', 'size', dataA.size)

    ## Create database B ##
    dbB = Database(TESTHEAD)
    # Create top level model group
    dbB.create_group('model')
    dbB.attr_set(    'model', 'model', 'model')
    # Create a subgroup
    dbB.create_group('model/subgroup_B')
    dbB.attr_set(    'model/subgroup_B', 'subgroup_property', 'B')
    # Create a parameters group
    dbB.create_group('model/subgroup_B/params')
    dbB.attr_set(    'model/subgroup_B/params', 'parameter', 'B')
    # Create a data group
    dbB.create_group('model/subgroup_B/data')
    # Create some data
    dataB = np.zeros(13)
    dbB.dset_set('model/subgroup_B/data/dataset', dataB)
    dbB.attr_set('model/subgroup_B/data/dataset', 'size', dataB.size)
    dbB.attr_set('model/subgroup_B/data', 'size', dataB.size)

    ## Check things before the merge ##
    # Check groups 
    assert dbA.exists('model')
    assert dbA.exists('model/subgroup_A')
    assert dbA.exists('model/subgroup_A/params')
    assert dbA.exists('model/subgroup_A/data')
    assert dbB.exists('model')
    assert dbB.exists('model/subgroup_B')
    assert dbB.exists('model/subgroup_B/params')
    assert dbB.exists('model/subgroup_B/data')
    assert not dbA.exists('model/subgroup_B')
    assert not dbA.exists('model/subgroup_B/params')
    assert not dbA.exists('model/subgroup_B/data')
    # Check data
    assert dbA.exists('model/subgroup_A/data/dataset')
    assert dbA.dset_size('model/subgroup_A/data/dataset') == 7
    assert dbB.exists('model/subgroup_B/data/dataset')
    assert dbB.dset_size('model/subgroup_B/data/dataset') == 13
    assert not dbA.exists('model/subgroup_B/data/dataset')
    # Check attributes that should exist in Origin (A)
    assert dbA.attr_exists('model', 'model')
    assert dbA.attr_exists('model/subgroup_A', 'subgroup_property')
    assert dbA.attr_exists('model/subgroup_A/params', 'parameter')
    assert dbA.attr_exists('model/subgroup_A/data', 'size')
    assert dbA.attr_exists('model/subgroup_A/data/dataset', 'size')
    assert dbA.attr_value('model/subgroup_A', 'subgroup_property') == 'A'
    assert dbA.attr_value('model/subgroup_A/params', 'parameter') == 'A'
    assert dbA.attr_value('model/subgroup_A/data', 'size') == 7
    assert dbA.attr_value('model/subgroup_A/data/dataset', 'size') == 7
    # Check attributes that should exist in Head (B)
    assert dbB.attr_exists('model', 'model')
    assert dbB.attr_exists('model/subgroup_B', 'subgroup_property')
    assert dbB.attr_exists('model/subgroup_B/params', 'parameter')
    assert dbB.attr_exists('model/subgroup_B/data', 'size')
    assert dbB.attr_exists('model/subgroup_B/data/dataset', 'size')
    assert dbB.attr_value('model/subgroup_B', 'subgroup_property') == 'B'
    assert dbB.attr_value('model/subgroup_B/params', 'parameter') == 'B'
    assert dbB.attr_value('model/subgroup_B/data', 'size') == 13
    assert dbB.attr_value('model/subgroup_B/data/dataset', 'size') == 13
    # Check attributes that should not exist in Origin A
    assert not dbA.attr_exists('model', 'subgroup_property')
    assert not dbA.attr_exists('model', 'size')
    assert not dbA.attr_exists('model', 'parameter')
    assert not dbA.attr_exists('model/subgroup_A', 'model')
    assert not dbA.attr_exists('model/subgroup_A', 'size')
    assert not dbA.attr_exists('model/subgroup_A', 'parameter')
    assert not dbA.attr_exists('model/subgroup_A/params', 'size')
    assert not dbA.attr_exists('model/subgroup_A/data', 'parameter')
    ## Perform the merge ##
    dbA.merge(TESTHEAD)
    ## Check things after the merge ##
    # Check groups 
    assert dbA.exists('model')
    assert dbA.exists('model/subgroup_A')
    assert dbA.exists('model/subgroup_A/params')
    assert dbA.exists('model/subgroup_A/data')
    assert dbB.exists('model')
    assert dbB.exists('model/subgroup_B')
    assert dbB.exists('model/subgroup_B/params')
    assert dbB.exists('model/subgroup_B/data')
    assert dbA.exists('model/subgroup_B')
    assert dbA.exists('model/subgroup_B/params')
    assert dbA.exists('model/subgroup_B/data')
    # Check data
    assert dbA.exists('model/subgroup_A/data/dataset')
    assert dbA.dset_size('model/subgroup_A/data/dataset') == 7
    assert dbB.exists('model/subgroup_B/data/dataset')
    assert dbB.dset_size('model/subgroup_B/data/dataset') == 13
    assert dbA.exists('model/subgroup_B/data/dataset')
    assert dbA.dset_size('model/subgroup_B/data/dataset') == 13
    # Check attributes that should exist in Origin (A and B)
    assert dbA.attr_exists('model', 'model')
    assert dbA.attr_exists('model/subgroup_A', 'subgroup_property')
    assert dbA.attr_exists('model/subgroup_A/params', 'parameter')
    assert dbA.attr_exists('model/subgroup_A/data', 'size')
    assert dbA.attr_exists('model/subgroup_A/data/dataset', 'size')
    assert dbA.attr_value('model/subgroup_A', 'subgroup_property') == 'A'
    assert dbA.attr_value('model/subgroup_A/params', 'parameter') == 'A'
    assert dbA.attr_value('model/subgroup_A/data', 'size') == 7
    assert dbA.attr_value('model/subgroup_A/data/dataset', 'size') == 7
    assert dbA.attr_exists('model/subgroup_B', 'subgroup_property')
    assert dbA.attr_exists('model/subgroup_B/params', 'parameter')
    assert dbA.attr_exists('model/subgroup_B/data', 'size')
    assert dbA.attr_exists('model/subgroup_B/data/dataset', 'size')
    assert dbA.attr_value('model/subgroup_B', 'subgroup_property') == 'B'
    assert dbA.attr_value('model/subgroup_B/params', 'parameter') == 'B'
    assert dbA.attr_value('model/subgroup_B/data', 'size') == 13
    assert dbA.attr_value('model/subgroup_B/data/dataset', 'size') == 13
    # Check attributes that should not exist in Origin A
    assert not dbA.attr_exists('model', 'subgroup_property')
    assert not dbA.attr_exists('model', 'size')
    assert not dbA.attr_exists('model', 'parameter')
    assert not dbA.attr_exists('model/subgroup_A', 'model')
    assert not dbA.attr_exists('model/subgroup_A', 'size')
    assert not dbA.attr_exists('model/subgroup_A', 'parameter')
    assert not dbA.attr_exists('model/subgroup_A/params', 'size')
    assert not dbA.attr_exists('model/subgroup_A/data', 'parameter')
    assert not dbA.attr_exists('model/subgroup_B', 'model')
    assert not dbA.attr_exists('model/subgroup_B', 'size')
    assert not dbA.attr_exists('model/subgroup_B', 'parameter')
    assert not dbA.attr_exists('model/subgroup_B/params', 'size')
    assert not dbA.attr_exists('model/subgroup_B/data', 'parameter')
    return

######## Main ########
def main():
    # Working tests
    test_merge()
    return

######## Execution ########
if __name__ == "__main__":
    main()
