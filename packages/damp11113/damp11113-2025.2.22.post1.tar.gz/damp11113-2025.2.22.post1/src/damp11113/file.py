"""
damp11113-library - A Utils library and Easy to use. For more info visit https://github.com/damp11113/damp11113-library/wiki
Copyright (C) 2021-present damp11113 (MIT)

Visit https://github.com/damp11113/damp11113-library

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import re
import zipfile
import json
import natsort
import psutil
import configparser

#-----------------------------read---------------------------------------

def quickRead(file, decode='utf-8'):
    with open(file, 'r', encoding=decode) as f:
        return f.read()

def quickReadJson(file):
    with open(file, 'r', encoding='utf-8') as f:
        return json.load(f)

def readini(filename, section_name, parameter_name):
    config = configparser.ConfigParser()
    config.read(filename)

    if section_name in config and parameter_name in config[section_name]:
        return config[section_name][parameter_name]
    else:
        print(f"Section '{section_name}' or parameter '{parameter_name}' not found in the INI file.")
        return None

#----------------------------------write------------------------------------

def quickWrite(file, data, encode="utf-8"):
    with open(file, 'w', encoding=encode) as f:
        f.write(data)
        f.close()

def quickWriteJson(file, data):
    with open(f'{file}.json', 'w') as f:
        json.dump(data, f)

#--------------------------------------zip----------------------------------

def unzip(file, to):
    with zipfile.ZipFile(file, 'r') as zip_ref:
        zip_ref.extractall(to)

def comzip(file, to):
    with zipfile.ZipFile(file, 'w') as zip_ref:
        zip_ref.write(to)

#----------------------------------size------------------------------------

def sizefile(file):
    size = 0

    for path, dirs, files in os.walk(file):
        for f in files:
            size += os.path.getsize(os.path.join(path, f))

    return size / 1000000

def sizefolder(folder):
    size = 0

    for path, dirs, files in os.walk(folder):
        for f in files:
            fp = os.path.join(path, f)
            size += os.path.getsize(fp)

    return size / 1000000

def sizefolder2(folder):
    size = psutil.disk_usage(folder).used
    return size / 1000000

def sizefolder3(folder):
    size = 0

    for path, dirs, files in os.walk(folder):
        for f in files:
            fp = os.path.join(path, f)
            size += os.path.getsize(fp)

    return size

#----------------------------------all-------------------------------------

def allfiles(folder, scan_subfolders=False, include_path=False, sort_by=None, sort_reverse=False, valid_extensions=None):
    """
    Scans files in a specified folder (and optionally its subfolders), and returns a list of file names
    with options for sorting and including the full file path.

    Parameters:
    - folder (str): The path of the folder to scan for files.
    - scan_subfolders (bool): If True, recursively scans subfolders. Defaults to False.
    - include_path (bool): If True, includes the full path of each file. Defaults to False.
    - sort_by (str or None): Defines the sorting criterion. Options are:
        - 'name': Sort files alphabetically.
        - 'size': Sort files by size.
        - 'created': Sort files by creation time.
        - 'modified': Sort files by last modified time.
        Defaults to None (no sorting).
    - sort_reverse (bool): If True, sorts in reverse order (descending). Defaults to False.
    - valid_extensions (tuple or None): A tuple of file extensions to include (e.g., ('.mp4', '.jpg')). If None, no filter is applied.

    Returns:
    - list: A list of file names or paths, sorted as per the specified options.

    Example:
    - allfiles("/path/to/folder", scan_subfolders=True, include_path=True, sort_by="name", sort_reverse=True, valid_extensions=('.mp4', '.jpg'))
    """

    # If valid_extensions is None, disable the filter and return all files
    if valid_extensions is None:
        valid_extensions = []

    all_files = []

    # Scan files in subfolders if needed
    if scan_subfolders:
        for root, dirs, files in os.walk(folder):
            for file in files:
                # If valid_extensions is empty, no filtering is applied
                if not valid_extensions or file.endswith(valid_extensions):
                    file_path = os.path.join(root, file) if include_path else file
                    all_files.append(file_path)
    else:
        for file in os.listdir(folder):
            # If valid_extensions is empty, no filtering is applied
            if not valid_extensions or file.endswith(valid_extensions):
                file_path = os.path.join(folder, file) if include_path else file
                all_files.append(file_path)

    # Sorting the files if requested
    if sort_by:
        # Sorting options
        if sort_by == 'name':
            all_files.sort(key=lambda x: [int(text) if text.isdigit() else text.lower() for text in re.split('(\d+)', x)], reverse=sort_reverse)  # Sort alphabetically (case insensitive)
        elif sort_by == 'size':
            all_files.sort(key=lambda x: os.path.getsize(x), reverse=sort_reverse)  # Sort by file size
        elif sort_by == 'created':
            all_files.sort(key=lambda x: os.path.getctime(x), reverse=sort_reverse)  # Sort by creation time
        elif sort_by == 'modified':
            all_files.sort(key=lambda x: os.path.getmtime(x), reverse=sort_reverse)  # Sort by last modified time

        return all_files

    return all_files

#----------------------------------count-------------------------------------

def countline(file, decode='utf-8'):
    with open(file, 'r', encoding=decode) as f:
        line = sum(1 for _ in f)
    return line

#-------------------------------sort_files-------------------------

def sort_files(file_list, reverse=False):
    flist = []
    for file in file_list:
        flist.append(file)
    return natsort.natsorted(flist, reverse=reverse)
