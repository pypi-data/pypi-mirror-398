#!/usr/env/bin python3
"""Handle connections with the h5py.File object

"""
######## Imports ########
#### Standard Library ####
import os
import time
from pathlib import Path
#### Third Party ####
import numpy as np
import h5py
#### Local ####

######## Objects ########
class Connection(object):
    """Create a connection to the hdf5 databse"""
    def __init__(
            self,
            filename,
            mode = 'r',
            retries = 0,
            sleep = 0.,
            verbose = False,
            **open_kwargs
        ):
        self._filename = filename
        self._mode = None
        self.mode = mode
        self._file = None
        self.retries = retries
        self.sleep = sleep
        self.verbose = verbose
        self._open_kwargs = open_kwargs
        # Check inputs
        # Report status
        self.report("__init__")
    # Properties set only once
    @property
    def file(self):
        return self._file
    @property
    def filename(self):
        return self._filename
    @property
    def open_kwargs(self):
        return self._open_kwargs

    # Properties that need a setter for testing
    @property
    def mode(self):
        return self._mode
    @mode.setter
    def mode(self, value):
        if not isinstance(value, str):
            raise ValueError(
                f"mode should be type {str}, but is type {type(value)}!")
        if (value in ['r', 'r+']) and (not self.isfile):
            raise RuntimeError(f"Cannot open {self.filename} " + \
                f" in mode '{self.value}'; File does not exist!")
        elif (value == 'w-') and (self.isfile):
            raise RuntimeError(f"Cannot open {self.filename} " + \
                f" in mode '{self.value}'; File exists!")
        elif ('a' in value):
            if not self.isfile:
                path = Path(self.filename)
                path.touch()
                value = 'r+'
        self._mode = value
        
    # Properties with a setter for changeability
    @property
    def retries(self):
        return self._retries
    @retries.setter
    def retries(self,value):
        self._retries = int(value)

    @property
    def sleep(self):
        return self._sleep
    @sleep.setter
    def sleep(self, value):
        self._sleep = float(value)

    @property
    def verbose(self):
        return self._verbose
    @verbose.setter
    def verbose(self, value):
        self._verbose = bool(value)

    # Property that returns an os.path.ifile call for filename
    @property
    def isfile(self):
        return os.path.isfile(self.filename)

    # h5py.File.id.id
    @property
    def id(self):
        if self.file is None:
            return 0
        else:
            return self.file.id.id

    # Property to determine if the file is closed
    @property
    def closed(self):
        if self.id == 0:
            return True
        else:
            return False

    # Property to determine if the file is open
    @property
    def opened(self):
        if self.id != 0:
            return True
        else:
            return False

    # Property determining if the file is readable
    @property
    def readable(self):
        return self.opened

    # Property determining if the file is writable
    @property
    def writable(self):
        if self.closed:
            return False
        else:
            if self.file.mode == 'r':
                return False
            else:
                return True

    # Property returning string containing info about the status of the file
    @property
    def status(self):
        if self.file is None:
            return "None"
        elif self.closed:
            return "closed"
        else:
            return "opened"

    # Print status if verbose
    def report(self, msg = None):
        if self.verbose:
            message = f"Connection for {self.filename} " + \
                f"(in mode {self.mode}) " + \
                f"status: {self.status}"
            if msg is not None:
                message = msg + ' ' + message
            print(message)

    # Open the file
    def __enter__(self):
        self.report("enter (before)")
        try_index = 0
        load = False
        while (not load) and (try_index <= self.retries):
            try:
                self._file = h5py.File(self.filename, self.mode)
                load = True
            except OSError:
                try_index += 1
                if try_index < self.retries:
                    time.sleep(np.random.random()*self.sleep)
        self.report("enter (after)")
        return self

    # Close the file
    def __exit__(self,ex_type,ex_value,ex_traceback):
        if self.verbose and (
                (ex_type is not None) or \
                (ex_value is not None) or \
                (ex_traceback is not None)):
            print(f"type: {ex_type}; value: {ex_value}; " + \
                f"ex_traceback: {ex_traceback}")
        self.report("exit (before)")
        self.file.close()
        self.report("exit (after)")

######## Tests ########
def test_connection():
    # Remove any existing test_connection.hdf5 file
    if os.path.isfile("test_connection.hdf5"):
        os.remove("test_connection.hdf5")
    # Try and fail to read the file
    try:
        conn = Connection("test_connection.hdf5", 'r')
        failed = False
    except:
        failed = True
    if not failed:
        raise RuntimeError(f"Tried to read a file that doesn't exist!")
    # Try and fail to read the file
    try:
        conn = Connection("test_connection.hdf5", 'r+')
        failed = False
    except:
        failed = True
    if not failed:
        raise RuntimeError(f"Tried to read a file that doesn't exist!")
    # Try to write the file 
    with Connection("test_connection.hdf5", 'w-') as conn:
        assert conn.opened, "Connection should be opened!"
        if not (conn.readable and conn.writable):
            raise RuntimeError(f"Connection readable: {conn.readable} " + \
                f"writable: {conn.writable}")
    assert conn.closed, "Connection should be closed"
    if not os.path.isfile("test_connection.hdf5"):
        raise RuntimeError(f"Failed to write file test_connection.hdf5")
    # Write the file again, verbosely this time
    with Connection("test_connection.hdf5", 'w', verbose=False) as conn:
        assert conn.opened, "Connection should be opened!"
        conn.report("block")
        if not (conn.readable and conn.writable):
            raise RuntimeError(f"Connection readable: {conn.readable} " + \
                f"writable: {conn.writable}")
    conn.report("outside")
    assert conn.closed, "Connection should be closed"
    if not os.path.isfile("test_connection.hdf5"):
        raise RuntimeError(f"Failed to write file test_connection.hdf5")
    # Read the file
    with Connection("test_connection.hdf5", 'r') as conn:
        assert conn.opened, "Connection should be opened!"
        if not (conn.readable and (not conn.writable)):
            raise RuntimeError(f"Connection readable: {conn.readable} " + \
                f"writable: {conn.writable}")
    # Check that closed means closed
    assert conn.closed, "Connection should be closed"

######## Execution ########
if __name__ == "__main__":
    test_connection()
