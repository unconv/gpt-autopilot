#!/usr/bin/env python3

import openai
import json
import time
import os
import subprocess
import shutil
import traceback
import sys

# SETTINGS
DEBUG = False

# HELPERS
def yesno(prompt, answers):
    answer = ""
    while answer not in answers:
        answer = input(f"{prompt} ({answers[0]}/{answers[1]}): ")
        if answer not in answers:
            print(f"Please type '{answers[0]}' or '{answers[1]}'")
    return answer

# GET API KEY
openai.api_key = os.getenv("OPENAI_API_KEY")
if openai.api_key in [None, ""]:
    try:
        with open(".api_key", "r") as f:
            openai.api_key = f.read().strip()
    except:
        print("Put your OpenAI API key into a .api_key file or OPENAI_API_KEY environment variable to skip this prompt.\n")
        openai.api_key = input("Input OpenAI API key: ").strip()

        if openai.api_key == "":
            sys.exit(1)

        save = yesno("Do you want to save this key to .api_key?", ["y", "n"])
        if save == "y":
            with open(".api_key", "w") as f:
                f.write(openai.api_key)

        print()


# CREATE CODE DIRECTORY
if not os.path.exists( "code/" ):
    os.mkdir( "code" )

# FUNCTIONS FOR CHATGPT -------------------------------------------------------

def write_file(filename, content):
    print(f"FUNCTION: Writing to file code/{filename}...")
    if DEBUG: print(f"\n {content}")

    # force newline in the end
    if content[-1] != "\n":
        content = content + "\n"

    # Create parent directories if they don't exist
    parent_dir = os.path.dirname(f"code/{filename}")
    os.makedirs(parent_dir, exist_ok=True)

    with open(f"code/{filename}", "w") as f:
        f.write(content)
    return f"File {filename} written successfully"

def append_file(filename, content):
    print(f"FUNCTION: Appending to file code/{filename}...")
    if DEBUG: print(f"\n {content}")

    # Create parent directories if they don't exist
    parent_dir = os.path.dirname(f"code/{filename}")
    os.makedirs(parent_dir, exist_ok=True)

    with open(f"code/{filename}", "a") as f:
        f.write(content)
    return f"File {filename} appended successfully"

def read_file(filename):
    print(f"FUNCTION: Reading file code/{filename}...")
    if not os.path.exists(f"code/{filename}"):
        print(f"File {filename} does not exist")
        return f"File {filename} does not exist"
    with open(f"code/{filename}", "r") as f:
        content = f.read()
    return f"The contents of '{filename}':\n{content}"

def create_dir(directory):
    print(f"FUNCTION: Creating directory code/{directory}")
    if os.path.exists( "code/"+directory+"/" ):
        return "ERROR: Directory exists"
    else:
        os.mkdir( "code/"+directory )
        return f"Directory {directory} created!"

def move_file(source, destination):
    print(f"FUNCTION: Move code/{source} to code/{destination}...")

    # Create parent directories if they don't exist
    parent_dir = os.path.dirname(f"code/{destination}")
    os.makedirs(parent_dir, exist_ok=True)

    shutil.move(f"code/{source}", f"code/{destination}")

    return f"File {source} moved to {destination}"

def copy_file(source, destination):
    print(f"FUNCTION: Copy code/{source} to code/{destination}...")

    # Create parent directories if they don't exist
    parent_dir = os.path.dirname(f"code/{destination}")
    os.makedirs(parent_dir, exist_ok=True)

    shutil.copy(f"code/{source}", f"code/{destination}")

    return f"File {source} copied to {destination}"

def delete_file(filename):
    print(f"FUNCTION: Deleting file code/{filename}")
    if not os.path.exists(f"code/{filename}"):
        print(f"File {filename} does not exist")
        return f"ERROR: File {filename} does not exist"
    os.remove(f"code/{filename}")
    return f"File {filename} successfully deleted"

def list_files():
    files = []
    for root, _, filenames in os.walk("code/"):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            files.append(file_path)
    # Remove "code/" from the beginning of file paths
    files = [file_path.replace("code/", "", 1) for file_path in files]

    print(f"FUNCTION: Files in code/ directory:\n{files}")
    return f"List of files in the project:\n{files}"

def ask_clarification(question):
    answer = input(f"## ChatGPT Asks a Question ##\n```{question}```\nAnswer: ")
    return answer

def run_cmd(command, reason):
    print("FUNCTION: Run a command")
    print("## ChatGPT wants to run a command! ##")
    print(f"Command: `{command}`")
    print(f"Reason: `{reason}`")

    answer = yesno(
        "Do you want to run this command?",
        ["YES", "NO"]
    )

    if answer == "YES":
        result = subprocess.run("cd code/; "+command, shell=True, capture_output=True, text=True)
        output = result.stdout + result.stderr

        return_value = "Result from command (last 245 chars):\n" + output[-245:]

        print(return_value)

        return return_value
    else:
        return "I don't want you to run that command"

def project_finished(finished):
    return "PROJECT_FINISHED"

# CHATGPT API FUNCTION
def send_chatgpt_message(message, messages, function_call = "auto"):
    # add user message to message list
    messages.append(message)

    # set function definitions
    functions = [
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
            "description": "Write content to a file with given name. Existing files will be overwritten. Parent directories will be created if they don't exist",
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
                    "command": {
                        "type": "string",
                        "description": "The command to run",
                    },
                    "reason": {
                        "type": "string",
                        "description": "A reason for why the command should be run",
                    },
                },
                "required": ["command", "reason"],
            },
        },
    ]

    try:
        # send prompt to chatgpt
        response = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=messages,
            functions=functions,
            function_call=function_call,
        )
    except:
        # if request fails, wait 5 seconds and try again
        print("ERROR in OpenAI request... Trying again")
        time.sleep(5)
        return send_chatgpt_message(message, messages, function_call)

    # add response to message list
    messages.append(response["choices"][0]["message"])

    if DEBUG: print(messages)

    response_message = response["choices"][0]["message"]["content"]

    # if response includes content, print it out
    if response_message != None:
        print("## ChatGPT Responded ##\n```")
        print(response_message)
        print("```\n")

    return messages

# MAIN FUNCTION
def run_conversation(prompt, messages = []):
    if messages == []:
        # add system message
        messages.append({
            "role": "system",
            "content": "You are an AI bot that can do anything by writing and reading files form the computer. You have been given specific functions that you can run. Only use those functions, and do not respond with a message directly. The user will describe their project to you and you will help them build it. Build the project step by step by calling the provided functions. If you need any clarification, use the ask_clarification function. You are currently inside the project folder. All commands will be run from there."
        })

        # add list of current files to user prompt
        prompt += "\n\n" + list_files()

    # add user prompt to chatgpt messages
    messages = send_chatgpt_message({"role": "user", "content": prompt}, messages)

    # get chatgpt response
    message = messages[-1]

    # loop until project is finished
    while True:
        if message.get("function_call"):
            # get function name and arguments
            function_name = message["function_call"]["name"]
            arguments_plain = message["function_call"]["arguments"]

            try:
                # try to parse arguments
                arguments = json.loads(arguments_plain)

                # call the function given by chatgpt
                function_response = globals()[function_name](**arguments)

            # if parsing fails, tell chatgpt to format arguments properly
            except:
                if DEBUG:
                    print("ERROR PARSING ARGUMENTS:\n---\n")
                    print(arguments_plain)
                    print("\n---\n")
                    traceback.print_exc()
                    print("\n---\n")
                function_response = "Error parsing arguments. Make sure to use properly formatted JSON, with double quotes"

            # if function returns PROJECT_FINISHED, exit
            if function_response == "PROJECT_FINISHED":
                print("## Project finished! ##")
                next_message = yesno("Do you want to ask something else?\nAnswer", ["y", "n"])
                if next_message == "y":
                    prompt = input("What do you want to ask?\nAnswer: ")
                    return run_conversation(prompt, messages)
                else:
                    exit()

            # send function result to chatgpt
            messages = send_chatgpt_message({
                "role": "function",
                "name": function_name,
                "content": function_response,
            }, messages)
        else:
            # if chatgpt doesn't respond with a function call, ask user for input
            if "?" in message["content"]:
                user_message = input("ChatGPT didn't respond with a function. What do you want to say?\nAnswer: ")
            else:
                # if chatgpt doesn't ask a question, continue
                user_message = "Ok, continue."

            # send user message to chatgpt
            messages = send_chatgpt_message({
                "role": "user",
                "content": user_message,
            }, messages)

        # save last response for the while loop
        message = messages[-1]

# ASK FOR PROMPT
prompt = input("What would you like me to do?\nAnswer: ")

# RUN CONVERSATION
run_conversation(prompt)
