import zipfile
import shutil
import copy
import os

from modules.helpers import relpath
from modules import cmd_args

virtual = {}

def create_zip(zip_filename):
    global virtual

    with zipfile.ZipFile(zip_filename, 'w') as zip_file:
        for path, content in virtual.items():
            path = relpath(path)
            if isinstance(content, str):  # File
                zip_file.writestr(path, content)
            else:  # Folder
                zip_file.writestr(path + '/', '')

def read(filename):
    global virtual

    if "zip" in cmd_args.args:
        return virtual[filename]
    else:
        with open(filename, "r") as f:
            return f.read()

def write(filename, content, mode="w"):
    global virtual

    if "zip" in cmd_args.args:
        virtual[filename] = content
    else:
        with open(filename, mode) as f:
            f.write(content)

def makedirs(directory):
    global virtual

    if "zip" in cmd_args.args:
        virtual[directory] = None
    else:
        return os.makedirs(directory, exist_ok=True)

def isdir(directory):
    global virtual

    if "zip" in cmd_args.args:
        return directory in virtual and virtual[directory] is None
    else:
        return os.path.isdir(directory)

def exists(file):
    global virtual

    if "zip" in cmd_args.args:
        return file in virtual
    else:
        return os.path.exists(file)

def move(source, destination):
    global virtual

    if "zip" in cmd_args.args:
        virtual[destination] = copy.deepcopy(source)
        del virtual[source]
    else:
        shutil.move(source, destination)

def copy_file(source, destination):
    global virtual

    if "zip" in cmd_args.args:
        virtual[destination] = copy.deepcopy(source)
    else:
        shutil.copy(source, destination)

def rmtree(directory):
    global virtual

    if "zip" in cmd_args.args:
        for filename in virtual.keys():
            if filename == directory or filename.startswith(directory+os.sep):
                del virtual[filename]
    else:
        shutil.rmtree(directory)

def copytree(source, destination):
    global virtual

    if "zip" in cmd_args.args:
        for filename in virtual.keys():
            if filename == source or filename.startswith(source+os.sep):
                virtual[destination] = copy.deepcopy(source)
    else:
        shutil.copytree(source, destination)

def remove(filename):
    global virtual

    if "zip" in cmd_args.args:
        if isdir(filename):
            rmtree(filename)
        else:
            del virtual[filename]
    else:
        if isdir(filename):
            shutil.rmtree(filename)
        else:
            os.remove(filename)

def print_contents():
    global virtual

    print("FILES IN VIRTUAL FILESYSTEM:")
    for file in virtual.keys():
        if virtual[file] == None:
            print("DIR: " + file)
        else:
            print("FILE: " + file)
            print(virtual[file])