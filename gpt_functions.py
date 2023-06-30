import os
import sys
import copy
import time
import shutil
import signal
import subprocess

from helpers import yesno, safepath, codedir, relpath
import cmd_args

tasklist = []
active_tasklist = []
tasklist_finished = True
tasklist_skipped = False

clarification_asked = 0
initial_questions = []

if "questions" in cmd_args.args:
    initial_question_count = int(cmd_args.args["questions"])
else:
    initial_question_count = 5

# Implementation of the functions given to ChatGPT

def make_tasklist(tasks):
    global tasklist
    global active_tasklist
    global tasklist_finished
    global tasklist_skipped

    tasklist_skipped = False

    tasklist = copy.deepcopy(tasks)

    next_task = tasks.pop(0)
    all_tasks = ""

    all_tasks += "TASKLIST: 1. " + next_task + "\n"

    for number, item in enumerate(tasks):
        all_tasks += "          " + str( number + 2 ) + ". " + item + "\n"

    print(all_tasks, end="")

    if "use-tasklist" not in cmd_args.args and yesno("\nGPT: Do you want to continue with this task list?\nYou") != "y":
        modifications = input("\nGPT: What would you like to change? (type 'skip' to skip)\nYou: ")
        print()

        if modifications == "skip":
            return "SKIP_TASKLIST"

        return "Task list modification request: " + modifications

    print()

    if "single-tasklist" in cmd_args.args:
        tasklist_finished = False
        return all_tasks + "\n\nPlease complete the project according to the above requirements"

    active_tasklist = copy.deepcopy(tasks)
    tasklist_finished = False

    print("TASK:     " + next_task)
    return "TASK_LIST_RECEIVED: Start with first task: " + next_task + ". Do all the steps involved in the task and only then run the task_finished function. If the task is already done in a previous task, you can call task_finished right away"

def file_open_for_writing(filename, content = ""):
    filename = relpath(safepath(filename))
    print(f"FUNCTION: Writing to file {filename}...")
    return f"Please respond in your next response with the full content of the file {filename}. Respond only with the contents of the file, no explanations. Create a fully working, complete file with no limitations on file size. Put file content between lines START_OF_FILE_CONTENT and END_OF_FILE_CONTENT. Start your response with START_OF_FILE_CONTENT"

def replace_text(find, replace, filename, count = -1):
    fullpath = safepath(filename)
    relative = relpath(fullpath)

    if ( len(find) + len(replace) ) > 37:
        print(f"FUNCTION: Replacing text in {relative}...")
    else:
        print(f"FUNCTION: Replacing '{find}' with '{replace}' in {relative}...")

    with open(fullpath, "r") as f:
        file_content = f.read()

    new_text = file_content.replace(find, replace, count)
    if new_text == file_content:
        print("ERROR:    Did not find text to replace")
        return "ERROR: Did not find text to replace"

    with open(fullpath, "w") as f:
        f.write(new_text)

    return "Text replaced successfully"

def file_open_for_appending(filename, content = ""):
    filename = relpath(safepath(filename))
    print(f"FUNCTION: Appending to file {filename}...")
    return f"Please respond in your next response with the full text to append to the end of the file {filename}. Respond only with the contents to add to the end of the file, no explanations. Create a fully working, complete file with no limitations on file size. Put file content between lines START_OF_FILE_CONTENT and END_OF_FILE_CONTENT. Start your response with START_OF_FILE_CONTENT"

def read_file(filename):
    fullpath = safepath(filename)
    relative = relpath(fullpath)

    print(f"FUNCTION: Reading file {relative}...")
    if not os.path.exists(fullpath):
        print(f"ERROR:    File {relative} does not exist")
        return f"File {relative} does not exist"
    with open(fullpath, "r") as f:
        content = f.read()
    return f"The contents of '{relative}':\n{content}"

def create_dir(directory):
    fullpath = safepath(directory)
    relative = relpath(fullpath)

    print(f"FUNCTION: Creating directory {relative}")
    if os.path.isdir(fullpath):
        return "ERROR: Directory exists"
    elif os.path.exists(fullpath):
        return "ERROR: A file with this name already exists"
    else:
        os.makedirs(fullpath)
        return f"Directory {relative} created!"

def move_file(source, destination):
    source = safepath(source)
    destination = safepath(destination)

    rel_source = relpath(source)
    rel_destination = relpath(destination)

    print(f"FUNCTION: Move {rel_source} to {rel_destination}...")

    # Create parent directories if they don't exist
    parent_dir = os.path.dirname(destination)
    os.makedirs(parent_dir, exist_ok=True)

    try:
        shutil.move(source, destination)
    except:
        if os.path.isdir(source) and os.path.isdir(destination):
            return "ERROR: Destination folder already exists."
        return "Unable to move file."

    return f"Moved {source} to {destination}"

def copy_file(source, destination):
    source = safepath(source)
    destination = safepath(destination)

    rel_source = relpath(source)
    rel_destination = relpath(destination)

    print(f"FUNCTION: Copy {rel_source} to {rel_destination}...")

    # Create parent directories if they don't exist
    parent_dir = os.path.dirname(destination)
    os.makedirs(parent_dir, exist_ok=True)

    try:
        shutil.copy(source, destination)
    except:
        if os.path.isdir(source) and os.path.isdir(destination):
            return "ERROR: Destination folder already exists."
        return "Unable to copy file."

    return f"File {rel_source} copied to {rel_destination}"

def delete_file(filename):
    fullpath = safepath(filename)
    relative = relpath(fullpath)

    print(f"FUNCTION: Deleting file {relative}")

    if not os.path.exists(fullpath):
        print(f"ERROR:    File {relative} does not exist")
        return f"ERROR: File {relative} does not exist"

    try:
        if os.path.isdir(fullpath):
            shutil.rmtree(fullpath)
        else:
            os.remove(fullpath)
    except:
        return "ERROR: Unable to remove file."

    return f"File {relative} successfully deleted"

def list_files(list = "", print_output = True):
    files_by_depth = {}
    directory = codedir()

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

    # Remove code folder from the beginning of file paths
    files = [relpath(file_path) for file_path in files]

    if print_output: print(f"FUNCTION: Listing files in project directory")
    return f"The following files are currently in the project directory:\n{files}"

def ask_clarification(questions):
    global clarification_asked
    global initial_question_count
    global initial_questions

    answers = {
        "clarifications": []
    }

    # if these are initial questions, save them for next versions
    save_initial_questions = "no-questions" not in cmd_args.args and clarification_asked < initial_question_count

    for question in questions:
        # stop after limit
        if clarification_asked >= initial_question_count:
            break

        # get answer to question
        if "\n" in question:
            answer = input(f"\nGPT:\n{question}\n\nYou: \n")
        else:
            answer = input(f"\nGPT: {question}\nYou: ")

        # skip unanswered questions
        if answer == "":
            print("\nSKIPPED:  Previous question/answer not included in message history")
            continue

        # add question to clarifications
        answers["clarifications"].append({
            "role": "assistant",
            "content": question
        })

        # add answer to clarifications
        answers["clarifications"].append({
            "role": "user",
            "content": answer
        })

        clarification_asked += 1

        # save initial questions for next versions
        if save_initial_questions:
            initial_questions += answers["clarifications"]

    print()

    return answers

def run_cmd(base_dir, command, reason, asynch=False):
    base_dir = safepath(base_dir)
    base_dir = base_dir.rstrip("/").rstrip("\\")

    if asynch == True:
        asynchly = " asynchronously"
    else:
        asynchly = ""

    print()
    print(f"GPT: I want to run the following command{asynchly}:")

    print("------------------------------")
    print(f"{command}")
    print("------------------------------")
    print(reason)
    print("------------------------------")
    print("Base: " + base_dir)
    print()

    # add cd command
    full_command = "cd " + base_dir + "; " + command

    if asynch == True:
        print("#################################################")
        print("# WARNING: This command will run asynchronously #")
        print("# and it will not be automatically killed after #")
        print("# GPT-AutoPilot is closed. You must close the   #")
        print("# program manually afterwards!                  #")
        print("#################################################")
        print()

    if command.strip() not in cmd_args.allowed_cmd:
        answer = yesno(
            "Do you want to run this command?",
            ["YES", "NO", "ASYNC", "SYNC"]
        )
        print()
    else:
        answer = "SYNC"

    if answer == "ASYNC":
        asynch = True
        answer = "YES"

    elif answer == "SYNC":
        asynch = False
        answer = "YES"

    if answer == "YES":
        process = subprocess.Popen(
            full_command + " > gpt-autopilot-cmd-output.txt 2>&1",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Run command asynchronously in the background
        if asynch:
            # Wait for 4 seconds
            time.sleep(4)
        else:
            try:
                # Wait for the subprocess to finish
                process.wait()
            except KeyboardInterrupt:
                # Send Ctrl+C signal to the subprocess
                process.send_signal(signal.SIGINT)

        # read possible output
        output_file = os.path.join(base_dir, "gpt-autopilot-cmd-output.txt")
        if os.path.exists(output_file):
            with open(output_file) as f:
                output = f.read()
            os.remove(output_file)

        return_value = "Result from command (first 400 chars):\n" + output[:400]

        if len(output) > 400:
            return_value += "\nResult from command (last 245 chars):\n" + output[-245:]

        if output.strip() == "":
            return_value += "<no output from command>"

        return_value = return_value.strip()

        print(return_value)
        print()

        return return_value
    else:
        return "I don't want to run that command"

def project_finished(finished=True):
    global tasklist_finished
    tasklist_finished = True
    return "PROJECT_FINISHED"

def task_finished(finished=True):
    global active_tasklist

    print("FUNCTION: Task finished")

    if len(active_tasklist) > 0:
        next_task = active_tasklist.pop(0)
        print("TASK:     " + next_task)
        return "Thank you. Please do the next task, unless it has already been done: " + next_task

    tasklist_finished = True
    return "PROJECT_FINISHED"

# Function definitions for ChatGPT

make_tasklist_func = {
    "name": "make_tasklist",
    "description": """
Convert the next steps to be taken into a list of tasks and pass them as a list into this function. Don't add already done tasks.
Explain the task clearly so that there can be no misunderstandings.
Don't include testing or other operations that require user interaction, unless specifically asked.
For a trivial project, make just one task
""",
    "parameters": {
        "type": "object",
        "properties": {
            "tasks": {
                "type": "array",
                "items": {
                    "type": "string",
                },
                "description": "The task list",
            },
        },
        "required": ["tasks"],
    },
}

ask_clarification_func = {
    "name": "ask_clarification",
    "description": "Ask the user clarifying question(s) about the project that are needed to implement it properly",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "A list of clarifying questions for the user",
            },
        },
        "required": ["questions"],
    },
}

definitions = [
    make_tasklist_func,
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
        "name": "file_open_for_writing",
        "description": "Open a file for writing. Existing files will be overwritten. Parent directories will be created if they don't exist. Content of file will be asked in the next prompt.",
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
        "description": "Replace text in given file",
        "parameters": {
            "type": "object",
            "properties": {
                "find": {
                    "type": "string",
                    "description": "The text to look for",
                },
                "replace": {
                    "type": "string",
                    "description": "The text to replace the occurences with",
                },
                "filename": {
                    "type": "string",
                    "description": "The name of file to modify",
                },
                "count": {
                    "type": "number",
                    "description": "The number of occurences to replace (default = all occurences)",
                },
            },
            "required": ["find", "replace", "filename"],
        },
    },
    {
        "name": "file_open_for_appending",
        "description": "Open a file for appending content to the end of a file with given name (after the last line). The content to append will be given in the next prompt",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The filename to append to",
                },
            },
            "required": ["filename"],
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
    ask_clarification_func,
    {
        "name": "project_finished",
        "description": "Call this function when the whole project is finished",
        "parameters": {
            "type": "object",
            "properties": {
                "finished": {
                    "type": "boolean",
                    "description": "Set this to true always",
                },
            },
            "required": ["finished"],
        },
    },
    {
        "name": "task_finished",
        "description": "Call this function when a task from the tasklist has been finished",
        "parameters": {
            "type": "object",
            "properties": {
                "finished": {
                    "type": "boolean",
                    "description": "Set this to true always",
                },
            },
            "required": ["finished"],
        },
    },
    {
        "name": "run_cmd",
        "description": "Run a terminal command. Returns the output. Folder navigation commands are disallowed. Do it with base_dir",
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
                "asynch": {
                    "type": "boolean",
                    "description": "Whether to run the program asynchronously (in the background)",
                },
            },
            "required": ["base_dir", "command", "reason"],
        },
    },
]

def get_definitions(model):
    global definitions
    global tasklist_skipped

    func_definitions = copy.deepcopy(definitions)

    # gpt-3.5 is not responsible enough for these functions
    gpt3_disallow = [
        "move_file",
        "copy_file",
        "replace_text",
    ]

    if "gpt-4" not in model:
        func_definitions = [definition for definition in func_definitions if definition["name"] not in gpt3_disallow]

    if "no-tasklist" in cmd_args.args or tasklist_skipped == True:
        func_definitions = [definition for definition in func_definitions if definition["name"] != "make_tasklist"]

    if "no-questions" in cmd_args.args:
        func_definitions = [definition for definition in func_definitions if definition["name"] != "ask_clarification"]

    return func_definitions
