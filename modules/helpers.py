# Helper functions
import shutil
import sys
import os
import re

from modules import cmd_args
from modules import paths

autonomous_message_count = 0

def codedir(filename=""):
    if "dir" in cmd_args.args:
        code_base_path = str(cmd_args.args["dir"])
    else:
        code_base_path = paths.relative("code")
    return os.path.join(code_base_path, filename)

def relpath(filepath, base=None):
    if base == None:
        base = codedir()
    path = os.path.relpath(filepath, base)
    if os.path.isdir(filepath):
        path += os.sep
    return path

def reset_code_folder():
    if os.path.isdir(codedir()):
        for item in os.listdir(codedir()):
            item_path = os.path.join(codedir(), item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
    else:
        os.mkdir(codedir())

def ask_input(message):
    global autonomous_message_count
    autonomous_message_count = 0
    try:
        return input(message)
    except KeyboardInterrupt:
        print("\n\nExiting")
        sys.exit(0)

def yesno(prompt, answers = ["y", "n"]):
    answer = ""
    while answer not in answers:
        slash_list = '/'.join(answers)
        answer = ask_input(f"{prompt} ({slash_list}): ")
        if answer not in answers:
            or_list = "' or '".join(answers)
            print(f"\nERROR:    Please type '{or_list}'\n")
    return answer

def safepath(path):
    if path == ".":
        path = ""

    base = os.path.abspath(codedir())
    file = os.path.abspath(os.path.join(base, path))

    if os.path.commonpath([base, file]) != base:
        print(f"ERROR:    Tried to access file '{file}' outside of project folder!")
        sys.exit(1)

    return file

def extract_number(filename):
    match = re.search(r'\d+', filename)
    if match:
        return int(match.group())
    else:
        return 0

def numberfile(parent_folder, folder=False):
    # Get a list of all files/folders in the parent folder
    items = [item for item in os.listdir(parent_folder)]

    # Find the highest numbered file/folder
    highest_number = 0
    for item in items:
        if folder and os.path.isdir(os.path.join(parent_folder, item)):
            item_number = extract_number(item)
            if item_number > highest_number:
                highest_number = item_number
        elif not folder and os.path.isfile(os.path.join(parent_folder, item)):
            item_number = extract_number(item)
            if item_number > highest_number:
                highest_number = item_number

    # Increment the highest number
    new_item_number = highest_number + 1
    new_item_name = str(new_item_number).zfill(4)

    return new_item_name
