import subprocess
import signal
import copy
import time
import sys
import os

from modules.helpers import yesno, safepath, codedir, relpath, ask_input
from modules import filesystem
from modules import cmd_args
from modules import paths

tasklist = []
active_tasklist = []
tasklist_finished = True
tasklist_skipped = False
use_single_tasklist = False

# keep track of whether an operation
# has been performed after a task
task_operation_performed = False

clarification_asked = 0
initial_questions = []
outline_created = False
modify_outline = False

if "questions" in cmd_args.args:
    initial_question_count = int(cmd_args.args["questions"])
else:
    initial_question_count = 5

# detect platform
if sys.platform.startswith("win"):
    what_command = "Windows command line"
elif sys.platform.startswith("darwin"):
    what_command = "macOS terminal"
else:
    what_command = "terminal"

# Implementation of the functions given to ChatGPT

def make_tasklist(tasks):
    global tasklist
    global active_tasklist
    global tasklist_finished
    global tasklist_skipped
    global initial_questions
    global use_single_tasklist
    global task_operation_performed

    if tasklist_skipped:
        return "ERROR: Creating a task list is not allowed at this moment."

    tasklist_skipped = False

    # combine same file tasks into one task
    combined_tasklist = []
    prev_file = None
    task_string = ""
    for item in tasks:
        if prev_file != None and prev_file != item["file_involved"]:
            if "NO_FILE" not in prev_file:
                task_string = "In " + prev_file + ": " + task_string
            combined_tasklist.append(task_string)
            task_string = ""
        prev_file = item["file_involved"]
        task_string += item["task_description"] + ". "

    # add remaining task
    if task_string != "":
        if prev_file != None and "NO_FILE" not in prev_file:
            task_string = "In " + prev_file + ": " + task_string
        combined_tasklist.append(task_string)

    tasklist = copy.deepcopy(combined_tasklist)

    next_task = combined_tasklist.pop(0)
    all_tasks = ""

    all_tasks += "TASKLIST: 1. " + next_task + "\n"

    for number, item in enumerate(combined_tasklist):
        all_tasks += "          " + str( number + 2 ) + ". " + item + "\n"

    print(all_tasks, end="")

    if "use-tasklist" not in cmd_args.args and yesno("\nGPT: Do you want to continue with this task list?\nYou") != "y":
        modifications = ask_input("\nGPT: What would you like to change? (type 'skip' to skip)\nYou: ")
        print()

        if modifications == "skip":
            return "SKIP_TASKLIST"

        return "Task list modification request: " + modifications

    print()

    step_by_step = "step-by-step" in cmd_args.args
    single_tasklist = "single-tasklist" in cmd_args.args

    if not step_by_step and not single_tasklist:
        tasklist_type = yesno(
            "How do you want go though the task list?\n"+
            "1) at once (faster, cheaper, less accurate)\n"+
            "2) step by step (slower, more expensive, more accurate)\n"+
            "Answer",
            ["1", "2"]
        )
        single_tasklist = tasklist_type == "1"
        print()

    if single_tasklist:
        tasklist_finished = False
        tasklist_prompt = all_tasks + "\n\nPlease complete the project according to the above requirements"

        # reset tasklist for versions
        active_tasklist = []
        use_single_tasklist = True

        # add tasklist to initial questions for versions
        initial_questions.append({
            "role": "user",
            "content": tasklist_prompt
        })

        return tasklist_prompt

    active_tasklist = copy.deepcopy(combined_tasklist)
    tasklist_finished = False
    task_operation_performed = False

    print("TASK:     " + next_task)
    return "TASK_LIST_RECEIVED: Start with first task: \n\n```\n" + next_task + "```\n\nDo all the steps involved in the task and only then run the task_finished function."

def write_file(filename, content):
    fullpath = safepath(filename)
    relative = relpath(fullpath)

    # Create parent directories if they don't exist
    parent_dir = os.path.dirname(fullpath)
    filesystem.makedirs(parent_dir)

    if filesystem.isdir(fullpath):
        return "ERROR: There is already a directory with this name"

    # force newline in the end
    content = content.rstrip("\n") + "\n"

    filesystem.write(fullpath, content)

    print(f"FUNCTION: Wrote to file {relative}")
    return f"File {relative} written successfully"

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

    file_content = filesystem.read(fullpath)

    new_text = file_content.replace(find, replace, count)
    if new_text == file_content:
        print("ERROR:    Did not find text to replace")
        return "ERROR: Did not find text to replace"

    filesystem.write(fullpath, new_text)

    return "Text replaced successfully"

def append_file(filename, content):
    fullpath = safepath(filename)
    relative = relpath(fullpath)

    # Create parent directories if they don't exist
    parent_dir = os.path.dirname(fullpath)
    filesystem.makedirs(parent_dir)

    if filesystem.isdir(fullpath):
        return "ERROR: There is already a directory with this name"

    # force newline in the end
    content = content.rstrip("\n") + "\n"

    filesystem.write(fullpath, content)

    print(f"FUNCTION: Wrote to file {relative}")
    return f"File {relative} appended successfully"

def file_open_for_appending(filename, content = ""):
    filename = relpath(safepath(filename))
    print(f"FUNCTION: Appending to file {filename}...")
    return f"Please respond in your next response with the full text to append to the end of the file {filename}. Respond only with the contents to add to the end of the file, no explanations. Create a fully working, complete file with no limitations on file size. Put file content between lines START_OF_FILE_CONTENT and END_OF_FILE_CONTENT. Start your response with START_OF_FILE_CONTENT"

def read_file(filename):
    fullpath = safepath(filename)
    relative = relpath(fullpath)

    print(f"FUNCTION: Reading file {relative}...")

    if not filesystem.exists(fullpath):
        print(f"ERROR:    File {relative} does not exist")
        return f"File {relative} does not exist"

    content = filesystem.read(fullpath)

    return f"The contents of '{relative}':\n{content}"

def create_dir(directory):
    if isinstance(directory, list):
        output = ""
        for dir in directory:
            output += create_dir(dir)+"\n"
        return output

    fullpath = safepath(directory)
    relative = relpath(fullpath)

    print(f"FUNCTION: Creating directory {relative}")
    if filesystem.isdir(fullpath):
        return "ERROR: Directory exists"
    elif filesystem.exists(fullpath):
        return "ERROR: A file with this name already exists"
    else:
        filesystem.makedirs(fullpath)
        return f"Directory {relative} created!"

def move_file(source, destination):
    source = safepath(source)
    destination = safepath(destination)

    rel_source = relpath(source)
    rel_destination = relpath(destination)

    print(f"FUNCTION: Move {rel_source} to {rel_destination}...")

    # Create parent directories if they don't exist
    parent_dir = os.path.dirname(destination)
    filesystem.makedirs(parent_dir)

    try:
        filesystem.move(source, destination)
    except:
        if filesystem.isdir(source) and filesystem.isdir(destination):
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
    filesystem.makedirs(parent_dir)

    try:
        filesystem.copy_file(source, destination)
    except:
        if filesystem.isdir(source) and filesystem.isdir(destination):
            return "ERROR: Destination folder already exists."
        return "Unable to copy file."

    return f"File {rel_source} copied to {rel_destination}"

def delete_file(filename):
    fullpath = safepath(filename)
    relative = relpath(fullpath)

    print(f"FUNCTION: Deleting file {relative}")

    if not filesystem.exists(fullpath):
        print(f"ERROR:    File {relative} does not exist")
        return f"ERROR: File {relative} does not exist"

    try:
        filesystem.remove(fullpath)
    except:
        return "ERROR: Unable to remove file."

    return f"File {relative} successfully deleted"

def should_ignore(path, ignore):
    path = relpath(path)

    # always ignore files inside these folders
    always_ignore = [
        ".git",
        "__pycache__",
        "node_modules",
        "vendor",
        ".angular",
    ]

    for aig in always_ignore:
        if (path.startswith(aig + os.sep) or (os.sep + aig + os.sep) in path) and path != aig + os.sep and path != aig:
            return True

    for ignore_file in ignore:
        if path.startswith(ignore_file + os.sep) or path.endswith(os.sep + ignore_file) or (os.sep + ignore_file + os.sep) in path or path == ignore_file:
            return True
    return False

def list_files(list = "", print_output = True, ignore = [
    ".gpt-autopilot",
    ".git",
    "__pycache__",
    "node_modules",
    "vendor",
    ".angular",
]):
    if "zip" in cmd_args.args:
        files = filesystem.virtual.keys()
    else:
        files_by_depth = {}
        directory = codedir()

        for root, dirs, filenames in os.walk(directory):
            depth = str(root[len(directory):].count(os.sep))

            dirs = [dir_path + os.sep for dir_path in dirs]

            dirs_and_files = filenames + dirs
            for filename in dirs_and_files:
                file_path = os.path.join(root, filename)
                if depth not in files_by_depth:
                    files_by_depth[depth] = []
                files_by_depth[depth].append(file_path)

        files = []
        counter = 0
        max_files = 100
        for level in files_by_depth.values():
            for filename in level:
                # ignore special files and directories
                if should_ignore(filename, ignore):
                    continue
                counter += 1
                if counter > max_files:
                    break
                files.append(filename)

    # use paths relative to code folder
    file_list = ""
    for file in files:
        path = relpath(file)
        file_list += path + "\n"

    if print_output:
        print(f"FUNCTION: Listing files in project directory")

    if file_list == "":
        return "The project directory is currently empty."

    return f"The following files are currently in the project directory:\n{file_list.strip()}"

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
            answer = ask_input(f"\nGPT:\n{question}\n\nYou: \n")
        else:
            answer = ask_input(f"\nGPT: {question}\nYou: ")

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
    print("#########################################################")
    print(f"GPT: I want to run the following command{asynchly}:")

    print("------------------------------")
    print(f"{command}")
    print("------------------------------")
    print(reason)
    print("------------------------------")
    print("Base: " + base_dir)
    print("#########################################################")
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
        print("COMMANDS AVAILABE:")
        print("- YES     Run the command")
        print("- NO      Don't run the command")
        print("- ASYNC   Run the command asynchronously")
        print("- SYNC    Run the command synchronously")
        print("- MSG     Send a message to ChatGPT\n")

        answer = ask_input("GPT: Do you want to run this command?\nYou: ")
        while answer not in ["YES", "NO", "ASYNC", "SYNC", "MSG"]:
            print("\nERROR: Please pick an available command\n")
            answer = ask_input("GPT: Do you want to run this command?\nYou: ")
        print()
    else:
        answer = "SYNC"

    if answer == "ASYNC":
        asynch = True
        answer = "YES"

    elif answer == "SYNC":
        asynch = False
        answer = "YES"

    elif answer == "MSG":
        answer = ask_input("GPT: What do you want to do?\nYou: ")
        print()
        return answer

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
        output = ""
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
    global tasklist_finished
    global task_operation_performed

    if task_operation_performed == False:
        task_operation_performed = True # prevent loop
        print("ERROR:    Tried to finish task before operation")
        return "ERROR: You need to perform the task first"

    print("FUNCTION: Task finished")

    if len(active_tasklist) > 0:
        next_task = active_tasklist.pop(0)
        task_operation_performed = False
        print("TASK:     " + next_task)
        return "Thank you. Please do the next task, unless it has already been done: " + next_task

    tasklist_finished = True
    return "PROJECT_FINISHED"

# Function definitions for ChatGPT

replace_text_func = {
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
}

make_tasklist_func = {
    "name": "make_tasklist",
    "description": "Create a tasklist for the project",
    "parameters": {
        "type": "object",
        "properties": {
            "tasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "file_involved": {
                            "type": "string",
                            "description": "The name of the file involved in the step, or NO_FILE"
                        },
                        "task_description": {
                            "type": "string"
                        }
                    },
                    "description": "A step in the tasklist"
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
            "questions": {
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

write_file_func = {
    "name": "write_file",
    "description": "Write content to a file. Existing files will be overwritten. Parent directories will be created if they don't exist.",
    "parameters": {
        "type": "object",
        "properties": {
            "filename": {
                "type": "string",
                "description": "The filename to write to",
            },
            "content": {
                "type": "string",
                "description": "The full content to be written, max 5 MB",
            },
        },
        "required": ["filename", "content"],
    },
}

file_open_for_writing_func = {
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
}

append_file_func = {
    "name": "append_file",
    "description": "Append content to a file (after the last line).",
    "parameters": {
        "type": "object",
        "properties": {
            "filename": {
                "type": "string",
                "description": "The filename to append to",
            },
            "content": {
                "type": "string",
                "description": "The full content to be appended, max 5 MB",
            },
        },
        "required": ["filename", "content"],
    },
}

file_open_for_appending_func = {
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
}

real_write_file_func = file_open_for_writing_func
real_append_file_func = file_open_for_appending_func

definitions = [
    make_tasklist_func,
    real_write_file_func,
    #real_append_file_func,
    ask_clarification_func,
    #replace_text_func,
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
        "description": "Create a directory or directories with given name(s)",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Name of the directory to create or an array of directories to create",
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
        "description": "Run a "+what_command+" command. Returns the output. Folder navigation commands are disallowed. Do it with base_dir",
        "parameters": {
            "type": "object",
            "properties": {
                "base_dir": {
                    "type": "string",
                    "description": "The directory to change into before running command",
                },
                "command": {
                    "type": "string",
                    "description": "The command to run. Disallowed: touch, mkdir, cd",
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

    if "no-cmd" in cmd_args.args:
        func_definitions = [definition for definition in func_definitions if definition["name"] != "run_cmd"]

    return func_definitions

def function_available(function, model):
    definitions = get_definitions(model)

    for definition in definitions:
        if definition["name"] == function:
            return True

    return False
