#!/usr/bin/env python3
"""Handle downloading data files from the internet and storing them locally

"""
######## Imports ########
#### Standard Library ####
import argparse
import requests
from importlib import resources
import hashlib
import warnings
import random
import time
from os import listdir
from os import path
from os import remove, rename
#### Third party ####
from tqdm import tqdm

######## Argparse ########
def arg():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", help="Available actions: [download list validate save clean clear]")
    parser.add_argument("filename", nargs='?', default=[], help="basename or url of files")
    parser.add_argument("--verbose", action="store_true",help="Verbose output?")
    parser.add_argument("--all-files", "-a", action="store_true",help="Manage all files")
    parser.add_argument("--assume-yes", "-y", action="store_true", help="Assume yes")
    parser.add_argument("--retries", default=3, type=int)
    parser.add_argument("--spider", action="store_true", help="Don't download anything. Just check sizes.")
    parser.add_argument("--buffer", type=int, default=65536, help="Size of buffer (Bytes)")
    parser.add_argument("--enc", default="sha256", help="Hash encoding")
    opts = parser.parse_args()
    if type(opts.filename) == str:
        opts.filename = [opts.filename]
    return opts

######## Functions ########
def download_with_retry(url, max_retries=3, base_delay=1):
    """Download with retry logic and exponential backoff"""
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            return response
        except (requests.RequestException, requests.Timeout, requests.ConnectionError) as e:
            if attempt == max_retries:
                raise e
            # Exponential backoff with jitter
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            print(f"Download attempt {attempt + 1} failed, retrying in {delay:.1f}s...")
            time.sleep(delay)

######## Objects ########
#### File Registry ####
class FileRegistry(object):
    """Manage files stored on the disk"""
    def __init__(self, module_path, basename_hash="hash.dat"):
        """Construct an object which keeps track of some files"""
        if not path.isdir(resources.files(module_path)):
            raise ValueError(f"module_path {module_path} does not point to a directory!")
        self.module_path = module_path
        self.directory = resources.files(module_path)
        self.basename_hash = basename_hash
        self.fname_hash = path.join(self.directory, path.basename(basename_hash))

    @property
    def tracked_files(self):
        """Return a list of all the tracked files in the directory"""
        allfiles = listdir(self.directory)
        # Initialize tracked files
        tracked = []
        # Loop files
        for fname in allfiles:
            # Check if file is __init__.py
            if fname in ["__init__.py", "__pycache__", self.basename_hash]:
                continue
            # Otherwise add the absolute path to tracked
            tracked.append(path.join(self.directory,fname))
            # Check work
            if not path.isfile(tracked[-1]):
                raise RuntimeError("A file was added which does not exist on the disk")
        return tracked

    def hash(self, fname, enc="sha256", buff=65536):
        """Return the hash for a file"""
        # Get hash function
        _hash = getattr(hashlib,enc)
        # Instantiate hash object
        hash_obj = _hash()
        # Read a file
        with open(fname, 'rb') as F:
            while True:
                # Read buff bytes of data
                data = F.read(buff)
                # If we've reached the end of file (EOF), we are done
                if not data:
                    break
                # Update the hash
                hash_obj.update(data)
        return hash_obj.hexdigest(), enc

    def save_hash(self, fname, url=None, **kwargs):
        """Record the hash value for a file in the right place"""
        basename = path.basename(fname)
        if not path.isfile(fname):
            raise RuntimeError(f"Cannot hash file: {fname}; no such file exists")
        _hash, _enc = self.hash(fname, **kwargs)
        # Create hash file
        if not path.isfile(self.fname_hash):
            with open(self.fname_hash, 'w') as F:
                F.writelines(f"#basename bytesize enc hash [url]\n")
        # Open hash file
        with open(self.fname_hash, 'a') as F:
            line = f"{basename} {path.getsize(fname)} {_enc} {_hash}"
            if url is not None:
                line = line + f" {url}"
            line = line + '\n'
            F.writelines(line)

    def update_hash(self, basename, **kwargs):
        """Update a recorded hash (possibly with a different encoding)"""
        fname_data = path.join(self.directory,basename)
        fname_temp = f"{self.fname_hash}.tmp"
        if not (path.isfile(fname_data) and self.is_hashed(basename)):
            raise RuntimeError("Cannot update a hash that does not exist.")
        # Load existing hash dictionary
        hash_dict = self.load_hash(basename)
        # Get new hash
        _hash, _enc = self.hash(fname_data, **kwargs)
        # Create new hash file
        with open(fname_temp, 'w') as Fout:
            with open(self.fname_hash, 'r') as Fin:
                for line in Fin:
                    fields = line.split()
                    if fields[0] == basename:
                        line = f"{basename} {path.getsize(fname_data)} {_enc} {_hash}"
                        if "url" in hash_dict:
                            line = line + f" {hash_dict['url']}\n"
                    Fout.writelines(line)
        # move
        rename(fname_temp, self.fname_hash) # This is atomic on most filesystems

    def is_hashed(self, fname):
        """Check if we have a hash for this file"""
        basename = path.basename(fname)
        # Check for existance of hash file
        if not path.isfile(self.fname_hash):
            warnings.warn(f"Cannot find {self.basename_hash} file; downloads may not be checked")
            return False
        # hash file exists. Load it
        with open(self.fname_hash, 'r') as F:
            for line in F:
                fields = line.split()
                if fields[0] == basename:
                    return True
        return False

    def load_hash(self, fname):
        """Check the saved value of a hash"""
        basename = path.basename(fname)
        # Check if file is hashed
        if not self.is_hashed(fname):
            raise RuntimeError(f"Failed to load hash for {fname}")
        # hash file if it exists, load it
        if not path.isfile(self.fname_hash):
            raise RuntimeError(f"Failed to load hash database {self.fname_hash}")
        # Initialize hash data
        values = None
        # Read the database
        with open(self.fname_hash, 'r') as F:
            for line in F:
                fields = line.split()
                # Check for keys
                if fields[0].startswith("#"):
                    keys = fields
                    continue
                # Check for match
                if fields[0] == basename:
                    values = fields
        # Failed to find item
        if values is None:
            raise RuntimeError(f"Failed to find {basename} in {self.fname_hash}")
        # Create dictionary
        hash_dict = {}
        for i in range(len(values)):
            if keys[i] == "[url]":
                keys[i] = "url"
            elif keys[i] == "#basename":
                keys[i] = "basename"
            hash_dict[keys[i]] = values[i]
        return hash_dict

    def validate(self, fname):
        """Check if a file has a hash which matches what is saved"""
        basename = path.basename(fname)
        if not self.is_hashed(fname):
            warnings.warn(f"No hash available for {fname}")
        # Load recorded hash dictionary
        recorded_hash_dict = self.load_hash(fname)
        # Check current hash
        current_hash, current_enc = self.hash(fname,enc=recorded_hash_dict["enc"])
        # Check for match
        if not current_hash == recorded_hash_dict["hash"]:
            raise ValueError(f"Uh oh! {current_enc} hash of {basename} does not match recorded value!")

    def validate_all(self):
        """Check that all files match a recorded hash"""
        for item in self.tracked_files:
            self.validate(item)

    @property
    def total_size(self):
        """Return the total size of all tracked fiels"""
        tot = 0
        for item in self.tracked_files:
            tot += path.getsize(item)
        return tot
    
    def report(self):
        """Report on the size of each file"""
        for item in self.tracked_files:
            basename = path.basename(item)
            _size = path.getsize(item)
            _hash, _enc = self.hash(item)
            print(f"{basename}; size={_size/(1e6)} MB; enc={_enc}; hash={_hash}")
    
    def download(
            self,
            item,
            verbose=False,
            assume_yes=False,
            retries=3,
            spider=False,
            buffer=65536,
            enc="sha256",
        ):
        """Download a file from the url provided in the hash file"""
        # First argument is either a url or a filename
        # If not hashed, assume url
        if (not self.is_hashed(item)) or (path.basename(item) != item):
            hash_dict = {
                "basename" : path.basename(item),
                "url": item,
                "bytesize": 0,
                "enc" : enc,
            }
        else:
            # load the hash
            hash_dict = self.load_hash(item)
            # Check if url is in hash_dict
            if "url" not in hash_dict:
                raise ValueError(f"Unknown url for {basename}")

        # Get the basename
        basename = hash_dict["basename"]

        # Check if file is already downloaded
        if path.isfile(path.join(self.directory,basename)) and (not spider):
            warnings.warn(f"Did not download {basename}; already exists {path.join(self.directory,basename)}!")
            self.validate(path.join(self.directory,basename))
            return

        # Check size of downloadable file
        header = download_with_retry(hash_dict["url"], max_retries=retries)
        size = int(header.headers.get("Content-Length"))

        # Verify size
        if (hash_dict["bytesize"] != 0) and (size != int(hash_dict["bytesize"])):
            raise RuntimeError(f"Tried to get {basename}, but header size {size} did not equal expected {hash_dict['bytesize']}")

        # Spider return
        if spider:
            print(f"{basename} size: {size/(1e6)} MB")
            return

        # Check if hashed
        if (not self.is_hashed(basename)) and (not assume_yes):
            prompt = f"{basename} is not hashed. Download anyway? (y/[N])"
            answer = input(prompt)
            if answer.lower() not in ['y', 'yes']:
                warnings.warn("Did not download {basename}. User told me not to.")
                return

        # Check if greater than 5 MB
        if (size >= 5 * (1024**2)) and (not assume_yes):
            prompt = f"Size: {size/(1e6)} MB\n" \
                f"Download {basename} from {hash_dict['url']}? (y/[N])\n"
            answer = input(prompt)
            if answer.lower() not in ['y', 'yes']:
                warnings.warn("Did not download {basename}. User told me not to.")
                return
        # Figure out pathing
        temp_path = path.join(self.directory, f"{basename}.tmp")
        final_path = path.join(self.directory, basename)
        if verbose:
            print(f"temp_path: {temp_path}")
            print(f"final_path: {final_path}")
        # Try to download file
        try:
            # Generate request
            response = download_with_retry(hash_dict["url"], max_retries=retries)

            # Write with buffer
            with open(temp_path, 'wb') as F:
                downloaded = 0
                with tqdm(total=size, unit='B', unit_scale=True) as pbar:
                    for chunk in response.iter_content(chunk_size=buffer):
                        if chunk:
                            F.write(chunk)
                            pbar.update(len(chunk))
                            downloaded += len(chunk)
                # Verify download completed succesfully
                if downloaded != size:
                    raise RuntimeError(f"Incomplete download: {downloaded} != {size} bytes")
                # Check current hash
                current_hash, current_enc = self.hash(temp_path,enc=hash_dict["enc"])
                if "hash" not in hash_dict:
                    warnings.warn(f"Warning! Could not verify {enc} hash of {basename}")
                    hash_dict["hash"] = current_hash

                # Bad things happened
                if not current_hash == hash_dict["hash"]:
                    raise RuntimeError(f"Uh oh! {current_enc} hash of {basename} does not match recorded value!")
                
                # Move temp file to final location atomically
                if path.exists(temp_path):
                    if path.exists(final_path):
                        remove(final_path)
                    rename(temp_path, final_path) # This is atomic on most filesystems

                # Check the hash again to take advantage of the built-in validation
                if self.is_hashed(basename):
                    self.validate(final_path)
                else:
                    self.save_hash(final_path, url=hash_dict["url"], enc=hash_dict["enc"], buff=buffer)

        finally:
            # Clean up temporary files
            if path.exists(temp_path):
                remove(temp_path)


    def clean(self):
        """Clean up junk and things that shouldn't be here"""
        for item in self.tracked_files:
            # Get the basename
            basename = path.basename(item)
            # Check for files not hashed
            if not self.is_hashed(item):
                print('not hashed')
                remove(item)
                continue
            # Check for files with incorrect sizes or hashes
            hash_dict = self.load_hash(basename)
            if int(path.getsize(item)) != int(hash_dict['bytesize']):
                print('wrong size')
                remove(item)
                continue
            # Check current hash
            current_hash, current_enc = self.hash(item,enc=hash_dict["enc"])
            if not current_hash == hash_dict["hash"]:
                print('wrong hash')
                remove(item)
                continue

    def clear(self, assume_yes=False):
        """Clear the whole set of downloaded files!"""
        # Check with user
        if not assume_yes:
            prompt = f"Total file storage: {self.total_size/(1e6)} MB\n" \
                f"Delete all files in {self.directory}? (y/[N])\n"
            answer = input(prompt)
            if len(answer) > 1:
                answer = answer[0]
            if answer not in ['y', 'Y']:
                warnings.warn("User told me not to delete the files.")
                return

        # Clear files
        for item in self.tracked_files:
            remove(item)

    def remove(self, basename, assume_yes=False):
        """remove an individual file"""
        # Get fname of file
        fname = path.join(self.directory,basename)
        if not path.isfile(fname):
            raise RuntimeError("Cannot delete file {fname}; no such file exists!")
        # Check with user:
        if not assume_yes:
            prompt = f"File size: {path.getsize(fname)}\nremove? (y/[N])\n"
            answer = input(prompt)
            if answer.lower() not in ['y', 'yes']:
                warnings.warn("Did not remove {basename}. User told me not to.")
                return
        # Delete the file
        remove(fname)

######## main ########
def main(
    file_location,
    hash_basename,
    action,
    filename_list,
    verbose=False,
    all_files=False,
    assume_yes=False,
    retries=3,
    spider=False,
    buffer=65536,
    enc="sha256",
    ):
    """Main function for registry module"""
    Files = FileRegistry(file_location,hash_basename)
    # Check all files option
    if all_files or (action=="list") or ((action in ["validate"]) and (len(filename_list) == 0)):
        filename_list = Files.tracked_files
    if not type(filename_list) == list:
        raise TypeError(f"filename_list is not a list, and is of type {type(filename_list)}")
    # Download files
    if action == "download":
        for item in filename_list:
            Files.download(
                item,
                verbose=verbose,
                assume_yes=assume_yes,
                retries=retries, 
                spider=spider, 
                buffer=buffer, 
                enc=enc
            )
    elif action == "list":
        for item in filename_list:
            basename = path.basename(item)
            _size = path.getsize(item)
            _hash, _enc = Files.hash(item)
            print(f"{basename}; size={_size/1e6} MB; enc={_enc}; hash={_hash}")
    elif action == "validate":
        for item in filename_list:
            Files.validate(path.join(Files.directory,item))
    elif action == "save":
        for item in filename_list:
            if Files.is_hashed(item):
                Files.update_hash(item, enc=enc, buff=buffer)
            else:
                Files.save_hash(item, enc=enc, buff=buffer)
    elif action == "clean":
        Files.clean()
    elif action == "remove":
        for item in filename_list:
            Files.remove(item, assume_yes=assume_yes)
    elif action == "clear":
        Files.clear(assume_yes=assume_yes)
    else:
        raise ValueError(f"Unknown command {action}")

    return

######## Execution ########
if __name__ == "__main__":
    from xdata import files as FILE_LOCATION
    # Get command line arguments
    opts = arg()
    # Use command line arguments to call main
    main(
        FILE_LOCATION,
        "hash.dat",
        opts.action,
        opts.filename,
        verbose=opts.verbose,
        all_files=opts.all_files,
        assume_yes=opts.assume_yes,
        retries=opts.retries,
        spider=opts.spider,
        buffer=opts.buffer,
        enc=opts.enc,
    )
