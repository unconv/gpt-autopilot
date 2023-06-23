import os
import re
import shutil
import subprocess

from helpers import yesno, safepath

# Implementation of the functions given to ChatGPT

def write_file(filename, content = ""):
    print(f"FUNCTION: Writing to file code/{filename}...")
    return f"Please respond in your next response with the full content of the file {filename}. Respond only with the contents of the file, no explanations. Create a fully working, complete file with no limitations on file size. End with END_OF_OUTPUT on single line"

def replace_text(find, replace, filename):
    filename = safepath(filename)

    if ( len(find) + len(replace) ) > 37:
        print(f"FUNCTION: Replacing text in code/{filename}...")
    else:
        print(f"FUNCTION: Replacing '{find}' with '{replace}' in code/{filename}...")

    with open(f"code/{filename}", "r") as f:
        file_content = f.read()

    with open(f"code/{filename}", "w") as f:
        f.write(
            re.sub(find, replace, file_content)
        )

    return "Text replaced successfully"

def append_file(filename, content):
    filename = safepath(filename)

    print(f"FUNCTION: Appending to file code/{filename}...")

    # Create parent directories if they don't exist
    parent_dir = os.path.dirname(f"code/{filename}")
    os.makedirs(parent_dir, exist_ok=True)

    with open(f"code/{filename}", "a") as f:
        f.write(content)
    return f"File {filename} appended successfully"

def read_file(filename):
    filename = safepath(filename)

    print(f"FUNCTION: Reading file code/{filename}...")
    if not os.path.exists(f"code/{filename}"):
        print(f"File {filename} does not exist")
        return f"File {filename} does not exist"
    with open(f"code/{filename}", "r") as f:
        content = f.read()
    return f"The contents of '{filename}':\n{content}"

def create_dir(directory):
    directory = safepath(directory)

    print(f"FUNCTION: Creating directory code/{directory}")
    if os.path.exists( "code/"+directory+"/" ):
        return "ERROR: Directory exists"
    else:
        os.mkdir( "code/"+directory )
        return f"Directory {directory} created!"

def move_file(source, destination):
    source = safepath(source)
    destination = safepath(destination)

    print(f"FUNCTION: Move code/{source} to code/{destination}...")

    # Create parent directories if they don't exist
    parent_dir = os.path.dirname(f"code/{destination}")
    os.makedirs(parent_dir, exist_ok=True)

    try:
        shutil.move(f"code/{source}", f"code/{destination}")
    except:
        if os.path.isdir(f"code/{source}") and os.path.isdir(f"code/{destination}"):
            return "ERROR: Destination folder already exists."
        return "Unable to move file."

    return f"Moved {source} to {destination}"

def copy_file(source, destination):
    source = safepath(source)
    destination = safepath(destination)

    print(f"FUNCTION: Copy code/{source} to code/{destination}...")

    # Create parent directories if they don't exist
    parent_dir = os.path.dirname(f"code/{destination}")
    os.makedirs(parent_dir, exist_ok=True)

    try:
        shutil.copy(f"code/{source}", f"code/{destination}")
    except:
        if os.path.isdir(f"code/{source}") and os.path.isdir(f"code/{destination}"):
            return "ERROR: Destination folder already exists."
        return "Unable to copy file."

    return f"File {source} copied to {destination}"

def delete_file(filename):
    filename = safepath(filename)

    print(f"FUNCTION: Deleting file code/{filename}")
    path = f"code/{filename}"

    if not os.path.exists(path):
        print(f"File {filename} does not exist")
        return f"ERROR: File {filename} does not exist"

    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    except:
        return "ERROR: Unable to remove file."

    return f"File {filename} successfully deleted"

def list_files(list = "", print_output = True):
    files_by_depth = {}
    directory = "code/"

    for root, _, filenames in os.walk(directory):
        depth = str(root[len(directory):].count(os.sep))

        for filename in filenames:
            file_path = os.path.join(root, filename)
            if depth not in files_by_depth:
                files_by_depth[depth] = []
            files_by_depth[depth].append(file_path)

    files = []
    counter = 0
    max_files = 20
    for level in files_by_depth.values():
        for filename in level:
            counter += 1
            if counter > max_files:
                break
            files.append(filename)

    # Remove "code/" from the beginning of file paths
    files = [file_path.replace("code/", "", 1) for file_path in files]

    if print_output: print(f"FUNCTION: Files in code/ directory:\n{files}")
    return f"The following files are currently in the project directory:\n{files}"

def ask_clarification(question):
    answer = input(f"## ChatGPT Asks a Question ##\n```{question}```\nAnswer: ")
    return answer

def run_cmd(base_dir, command, reason):
    base_dir = safepath(base_dir)
    print("FUNCTION: Run a command")
    print("## ChatGPT wants to run a command! ##")

    command = "cd code/" + base_dir.strip("/") + "; " + command
    print(f"Command: `{command}`")
    print(f"Reason: `{reason}`")

    answer = yesno(
        "Do you want to run this command?",
        ["YES", "NO"]
    )

    if answer == "YES":
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout + result.stderr

        return_value = "Result from command (last 245 chars):\n" + output[-245:]

        print(return_value)

        return return_value
    else:
        return "I don't want you to run that command"

def project_finished(finished):
    return "PROJECT_FINISHED"

# Function definitions for ChatGPT

definitions = [
    {
        "name": "list_files",
        "description": "List the files in the current project",
        "parameters": {
            "type": "object",
            "properties": {
                "list": {
                    "type": "string",
                    "description": "Set always to 'list'",
                },
            },
            "required": ["list"],
        },
    },
    {
        "name": "read_file",
        "description": "Read the contents of a file with given name. Returns the file contents as string.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The filename to read",
                },
            },
            "required": ["filename"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file with given name. Existing files will be overwritten. Parent directories will be created if they don't exist. Content of file will be asked in the next prompt.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The filename to write to",
                },
            },
            "required": ["filename"],
        },
    },
    {
        "name": "replace_text",
        "description": "Replace text in given file with regular expression",
        "parameters": {
            "type": "object",
            "properties": {
                "find": {
                    "type": "string",
                    "description": "The regular expression to look for",
                },
                "replace": {
                    "type": "string",
                    "description": "The text to replace the occurences with",
                },
                "filename": {
                    "type": "string",
                    "description": "The name of file to modify",
                },
            },
            "required": ["find", "replace", "filename"],
        },
    },
    {
        "name": "append_file",
        "description": "Write content to the end of a file with given name",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The filename to write to",
                },
                "content": {
                    "type": "string",
                    "description": "The content to write into the file",
                },
            },
            "required": ["filename", "content"],
        },
    },
    {
        "name": "move_file",
        "description": "Move a file from one place to another. Parent directories will be created if they don't exist",
        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "The source file to move",
                },
                "destination": {
                    "type": "string",
                    "description": "The new filename / filepath",
                },
            },
            "required": ["source", "destination"],
        },
    },
    {
        "name": "create_dir",
        "description": "Create a directory with given name",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Name of the directory to create",
                },
            },
            "required": ["directory"],
        },
    },
    {
        "name": "copy_file",
        "description": "Copy a file from one place to another. Parent directories will be created if they don't exist",
        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "The source file to copy",
                },
                "destination": {
                    "type": "string",
                    "description": "The new filename / filepath",
                },
            },
            "required": ["source", "destination"],
        },
    },
    {
        "name": "delete_file",
        "description": "Deletes a file with given name",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The filename to delete",
                },
            },
            "required": ["filename"],
        },
    },
    {
        "name": "ask_clarification",
        "description": "Ask the user a clarifying question about the project. Returns the answer by the user as string",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question to ask the user",
                },
            },
            "required": ["question"],
        },
    },
    {
        "name": "project_finished",
        "description": "Call this function when the project is finished",
        "parameters": {
            "type": "object",
            "properties": {
                "finished": {
                    "type": "string",
                    "description": "Set this to 'finished' always",
                },
            },
            "required": ["finished"],
        },
    },
    {
        "name": "run_cmd",
        "description": "Run a terminal command. Returns the output.",
        "parameters": {
            "type": "object",
            "properties": {
                "base_dir": {
                    "type": "string",
                    "description": "The directory to change into before running command",
                },
                "command": {
                    "type": "string",
                    "description": "The command to run",
                },
                "reason": {
                    "type": "string",
                    "description": "A reason for why the command should be run",
                },
            },
            "required": ["base_dir", "command", "reason"],
        },
    },
]
