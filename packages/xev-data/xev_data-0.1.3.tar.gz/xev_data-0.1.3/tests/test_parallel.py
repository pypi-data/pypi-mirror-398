#!/usr/env/bin python3
######## Globals ########
TESTDATA = "test_database.hdf5"
TESTGROUP1 = "test_parallel"
TESTDATA_NAME1 = "test_parallel_1"
TESTDATA_NAME2 = "test_parallel_2"
NUMPTS = int(1e6)
NUMTHREADS = 4

######## Imports ########
#### Standard Library ####
from pathlib import Path
import multiprocessing as mp
import concurrent.futures
import time
#### Third party ####
import numpy as np
#### Local ####
from xdata import Database

######## Utilities ########
def load_data(fname, group, item, indices=None):
    db = Database(fname, group)
    return db.dset_value(item, samples=indices)

######## TESTS ########
def test_parallel_read_no_overlap():
    print("Test parallel access with no overlap:")
    # Let's try setting a million points
    data = np.linspace(-1.,1.,NUMPTS)
    # Set the data
    db = Database(TESTDATA, TESTGROUP1)
    tic = time.perf_counter()
    db.dset_set(TESTDATA_NAME1, data,compression="gzip")
    toc = time.perf_counter()
    setting_time = toc-tic
    print(f"  Setting {data.size:.1e} points took {setting_time:.4f} seconds!")
    # Read the data once
    tic = time.perf_counter()
    data2 = db.dset_value(TESTDATA_NAME1,samples=np.arange(data.size))
    toc = time.perf_counter()
    serial_time = toc-tic
    print(f"  Reading {data.size:.1e} points took {serial_time:.4f} seconds (serial)!")
    # Try using 4 threads
    tic = time.perf_counter()
    data3 = np.full(data.size, -4.)
    # Identify edge ids
    edge_id = np.arange(0,data.size+1,data.size//NUMTHREADS)
    # Use multiprocessing
    with concurrent.futures.ProcessPoolExecutor(max_workers=NUMTHREADS) \
            as executor:
        future_to_data = {executor.submit(
            load_data,
            TESTDATA,
            TESTGROUP1,
            TESTDATA_NAME1,
            np.arange(edge_id[i], edge_id[i+1]),
        ): i for i in range(NUMTHREADS)}
    # Check for data
    for future in concurrent.futures.as_completed(future_to_data):
        try:
            i = future_to_data[future]
            index = np.arange(edge_id[i], edge_id[i+1])
            data3[index] = future.result()
        except Exception as exc:
            raise exc
    toc = time.perf_counter()
    parallel_time = toc-tic
    # Checks 
    print(f"  Reading {data.size:.1e} points took {parallel_time:.4f} seconds (parallel)!")
    fullness = np.sum(data3 != -4.) / data.size
    correctness = np.sum(np.isclose(data, data3)) / data.size
    print(f"  Parallel fullness: {fullness}")
    print(f"  Parallel correctness: {correctness}")
    return

def test_parallel_read_with_overlap():
    print("Test parallel access with overlap:")
    # Let's try setting a million points
    data = np.linspace(-1.,1.,NUMPTS) + 8
    # Set the data
    db = Database(TESTDATA, TESTGROUP1)
    tic = time.perf_counter()
    db.dset_set(TESTDATA_NAME2, data,compression="gzip")
    toc = time.perf_counter()
    setting_time = toc-tic
    print(f"  Setting {data.size:.1e} points took {setting_time:.4f} seconds!")
    # Read the data once
    tic = time.perf_counter()
    data2 = db.dset_value(TESTDATA_NAME2)
    toc = time.perf_counter()
    serial_time = toc-tic
    print(f"  Reading {data.size:.1e} points took {serial_time:.4f} seconds (serial)!")
    # Try using 4 threads
    tic = time.perf_counter()
    data3 = np.full(data.size, -4.)
    # Identify edge ids
    edge_id = np.arange(0,data.size+1,data.size//NUMTHREADS)
    # Use multiprocessing
    with concurrent.futures.ProcessPoolExecutor(max_workers=NUMTHREADS) \
            as executor:
        future_to_data = {executor.submit(
            load_data,
            TESTDATA,
            TESTGROUP1,
            TESTDATA_NAME2,
        ): i for i in range(NUMTHREADS)}
    # Check for data
    for future in concurrent.futures.as_completed(future_to_data):
        try:
            i = future_to_data[future]
            index = np.arange(edge_id[i], edge_id[i+1])
            data3[index] = future.result()[index]
        except Exception as exc:
            raise exc
    toc = time.perf_counter()
    parallel_time = toc-tic
    # Checks 
    print(f"  Reading {data.size:.1e} points took {parallel_time:.4f} seconds (parallel)!")
    fullness = np.sum(data3 != -4.) / data.size
    correctness = np.sum(np.isclose(data, data3)) / data.size
    print(f"  Parallel fullness: {fullness}")
    print(f"  Parallel correctness: {correctness}")
    return

######## Main ########
def main():
    test_parallel_read_with_overlap()
    test_parallel_read_no_overlap()
    return

######## Execution ########
if __name__ == "__main__":
    main()
