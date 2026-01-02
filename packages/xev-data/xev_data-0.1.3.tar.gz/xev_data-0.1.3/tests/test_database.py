#!/usr/env/bin python3
######## Globals ########
TESTDATA = "test_database.hdf5"
TESTALIAS = "test_alias.hdf5"
TESTSHARD1 = "test_shard1.hdf5"
TESTSHARD2 = "test_shard2.hdf5"
TESTMERGE = "test_merge.hdf5"
TESTGROUP1 = "test_group1"
TESTGROUP2 = "test_group2"
TESTGROUP3 = "test_group3"
TESTDATA_NAME1 = "test1"
TESTDATA_NAME2 = "test2"
TESTDATA_NAME3 = "test3"
TESTDATA_NAME4 = "test4"
TESTDATA_NAME5 = "test5"

######## Imports ########
from xdata import Database
from pathlib import Path
import numpy as np

######## Functions ########

def test_group():
    # Create a new database
    db = Database(TESTDATA)
    # test list_items when no items are present
    items = db.list_items()
    # Assert database is empty
    assert len(items) == 0
    # Create some groups
    db.create_group(TESTGROUP1)
    db.create_group(TESTGROUP2)
    db.create_group(TESTGROUP3)
    db.dset_set(TESTDATA_NAME1, np.arange(10))
    db.dset_set(TESTGROUP1 + "/" +  TESTDATA_NAME2, np.arange(11))

    #### List tests ####
    # List items again
    items = db.list_items()
    assert (len(items) == 4)
    # List only groups
    groups = db.list_items(kind="group")
    assert(len(groups) == 3)
    # List only dsets
    dsets = db.list_items(kind="dset")
    assert(len(dsets) == 1)
    # List items in group
    groupitems = db.list_items(path=TESTGROUP1)
    assert(len(groupitems) == 1)

    #### Group tests ####
    # Initialize fresh database object pointing at a group
    db = Database(TESTDATA, group=TESTGROUP1)
    # List items in that group
    groupitems = db.list_items()
    assert(len(groupitems) == 1)
    # Global path
    assert(len(db.list_items(path="/" +TESTGROUP1)) == 1)
    # Change group
    db.change_group(group='/')
    # Assert items again
    items = db.list_items()
    assert (len(items) == 4)
    # Change back
    db.change_group(TESTGROUP1)
    # Assert groupitems again
    groupitems = db.list_items()
    assert(len(groupitems) == 1)

def test_kind():
    # Initialize a database
    db = Database(TESTDATA)
    # Check that we can differentiate groups from dsets
    assert(db.kind(TESTGROUP1) == "group")
    assert(db.kind(TESTDATA_NAME1) == "dset")

def test_exists():
    # Initialize a database
    db = Database(TESTDATA)
    # Check that the exists function works
    assert db.exists(TESTDATA_NAME1)
    # Check that there are no pink elephants
    assert not (db.exists("A pink elephant"))

def test_visit():
    # Initialize a database
    db = Database(TESTDATA)
    print("Visiting with print")
    db.visit()

def test_scan():
    # Initialize a database
    db = Database(TESTDATA)
    # Check the scan output
    db.scan()

def test_dset():
    # Initialize a database
    db = Database(TESTDATA)
    # Come up with some bogus data
    data = np.eye(10)
    # Get that data's dtype
    dtype = data.dtype
    # Get that data's shape
    shape = data.shape
    # Get that data's size
    size = data.size
    # Initialize a new database with the appropriate shape and dtype
    db.dset_init(TESTDATA_NAME3, shape, dtype)
    # Set the data to the new database
    db.dset_set(TESTDATA_NAME3, data)
    # Check that it has the right size
    assert db.dset_size(TESTDATA_NAME3) == size
    # Check that it is not compressed
    assert db.dset_compression(TESTDATA_NAME3) == None
    # Check that it has the right shape
    assert db.dset_shape(TESTDATA_NAME3) == shape
    # Check that it has the right dtype
    assert db.dset_dtype(TESTDATA_NAME3) == dtype
    # Check that it is the correct data
    assert np.allclose(db.dset_value(TESTDATA_NAME3), data)
    # Check the sum of the data
    assert db.dset_sum(TESTDATA_NAME3) == np.sum(data)
    # Check the min of the data
    assert db.dset_min(TESTDATA_NAME3) == np.min(data)
    # Check the max of the data
    assert db.dset_max(TESTDATA_NAME3) == np.max(data)
    # Create a new dataset with the same data, a different way, using compression
    db.dset_set(TESTDATA_NAME4, data, compression="gzip")
    # Check the compression of the new dataset
    assert db.dset_compression(TESTDATA_NAME4) == "gzip"
    return

def test_attrs():
    # Initialize a database
    db = Database(TESTDATA)
    # Check that these attributes we calculated in test_dset are still here
    assert db.attr_exists(TESTDATA_NAME3, "min")
    assert db.attr_exists(TESTDATA_NAME3, "max")
    assert db.attr_exists(TESTDATA_NAME3, "sum")
    # Check that attr_list works correctly
    attr_list = db.attr_list(TESTDATA_NAME3)
    assert "min" in attr_list
    assert "max" in attr_list
    assert "sum" in attr_list
    # Check that attr_dict works correctly
    attr_dict = db.attr_dict(TESTDATA_NAME3)
    for item in attr_list:
        assert not(attr_dict[item] is None)
    db.attr_set_dict(TESTDATA_NAME4, attr_dict)
    attr_dict = db.attr_dict(TESTDATA_NAME4)
    for item in attr_list:
        assert not(attr_dict[item] is None)
    # Check that groups can have attrs
    db.attr_set(TESTGROUP1, "name", TESTGROUP1)
    assert db.attr_value(TESTGROUP1, "name") == TESTGROUP1
    db.attr_set("/", "fname", TESTDATA)
    return 

def test_fields():
    return

def test_shard():
    # Initialize a database
    db = Database(TESTDATA)
    # Shard some data to a new database
    db.shard(TESTSHARD1, [TESTDATA_NAME3], compression="gzip")
    # Point to that database
    db_shard = Database(TESTSHARD1)
    # Assert that the data copied to the new shard has its attributes
    assert db_shard.attr_exists(TESTDATA_NAME3, "min")
    assert db_shard.attr_exists(TESTDATA_NAME3, "max")
    assert db_shard.attr_exists(TESTDATA_NAME3, "sum")
    # Check that the data is the same
    assert np.allclose(db.dset_value(TESTDATA_NAME3), db_shard.dset_value(TESTDATA_NAME3))
    # Check the compression
    assert db_shard.dset_compression(TESTDATA_NAME3) == "gzip"
    assert db_shard.attr_value("/", "fname") == TESTDATA

    # Point to a different group
    db = Database(TESTDATA, TESTGROUP1)
    # Check items in group
    list_items = db.list_items()
    # Copy all the data in the group
    db.shard(TESTSHARD1, list_items, compression="gzip")
    # Open the shard at the correct group
    db_shard = Database(TESTSHARD1, TESTGROUP1)
    # Check each item
    for item in list_items:
        assert db_shard.exists(item)
    # Check the attribute
    assert db_shard.attr_value(".","name") == TESTGROUP1

    # RE-initialize database
    db = Database(TESTDATA)
    # Shard some data to a new database
    db.shard(TESTSHARD2, [TESTDATA_NAME4], compression="gzip")
    # Point to that database
    db_shard = Database(TESTSHARD2)
    assert db_shard.attr_value("/", "fname") == TESTDATA
    assert db_shard.exists(TESTDATA_NAME4)
    return

def test_merge():
    # Create a new merge db
    db_merge = Database(TESTMERGE)
    # Merge db_shard1
    db_merge.merge(TESTSHARD1)
    # Check that things are still in there
    assert db_merge.exists(TESTDATA_NAME3, kind="dset")
    assert db_merge.exists(TESTGROUP1, kind="group")
    # Merge db_shard2
    db_merge.merge(TESTSHARD2)
    # Check that things are still in there
    assert db_merge.exists(TESTDATA_NAME3, kind="dset")
    assert db_merge.exists(TESTGROUP1, kind="group")
    assert db_merge.exists(TESTDATA_NAME4, kind="dset")
    assert db_merge.attr_exists(TESTDATA_NAME3, "min")
    assert db_merge.attr_exists(TESTDATA_NAME3, "max")
    assert db_merge.attr_exists(TESTDATA_NAME3, "sum")
    assert db_merge.attr_value(TESTGROUP1, "name") == TESTGROUP1
    assert db_merge.attr_value("/", "fname") == TESTDATA
    assert len(db_merge.attr_dict('/')) == 1

    return

def test_rm():
    # Initialize the database
    db = Database(TESTDATA)
    # Assert data exists
    assert db.exists(TESTDATA_NAME4, kind="dset")
    # Remove it
    db.dset_rm(TESTDATA_NAME4)
    # Assert data does not exist
    assert not db.exists(TESTDATA_NAME4)
    return

def test_copy():
    # Initialize the databse
    db = Database(TESTDATA)
    # Assert data exists
    assert db.exists(TESTDATA_NAME3, kind="dset")
    # Assert location is not used
    assert not db.exists(TESTDATA_NAME4)
    # Copy data
    db.dset_copy(TESTDATA_NAME3, TESTDATA_NAME4)
    # Assert data exists
    assert db.exists(TESTDATA_NAME4, kind="dset")
    return

def test_recompress():
    # Initialize the databse
    db = Database(TESTDATA)
    # Assert data exists
    assert db.exists(TESTDATA_NAME4, kind="dset")
    assert db.dset_compression(TESTDATA_NAME4) is None
    db.dset_recompress(TESTDATA_NAME4, compression="gzip")
    assert db.exists(TESTDATA_NAME4, kind="dset")
    assert db.dset_compression(TESTDATA_NAME4) == "gzip"
    return

def test_rebase():
    # Initialize the databse
    db = Database(TESTDATA)
    # Assert data exists
    assert db.exists(TESTDATA_NAME4, kind="dset")
    # Remove it
    db.dset_rm(TESTDATA_NAME4)
    # Get size_on_disk
    initial_size = db.size_on_disk()
    # Rebase database
    db.rebase(TESTALIAS)
    # Check on status of files
    assert not db.exists(TESTDATA_NAME4)
    assert db.exists(TESTDATA_NAME3, kind="dset")
    assert db.exists(TESTGROUP1, kind="group")
    assert db.attr_exists(TESTDATA_NAME3, "min")
    assert db.attr_exists(TESTDATA_NAME3, "max")
    assert db.attr_exists(TESTDATA_NAME3, "sum")
    assert db.attr_value(TESTGROUP1, "name") == TESTGROUP1
    assert db.attr_value("/", "fname") == TESTDATA
    assert db.size_on_disk() < initial_size

    return


######## Main ########
def main():
    # Working tests
    test_group()
    test_kind()
    test_exists()
    test_dset()
    test_attrs()
    # Tests yet to be implemented
    test_fields()
    test_shard()
    test_merge()
    test_rm()
    test_copy()
    test_recompress()
    test_rebase()
    #test_visit()
    #test_scan()
    return

######## Execution ########
if __name__ == "__main__":
    main()
