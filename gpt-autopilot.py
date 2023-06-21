#!/usr/bin/env python3

import openai
import json
import os
import traceback
import sys
import shutil
import re

import gpt_functions
from helpers import yesno, safepath
import chatgpt
import betterprompter

# GET CONFIG
try:
    with open("config.json") as f:
        CONFIG = json.load(f)
except:
    CONFIG = {
        "model": "gpt-4-0613",
    }

# GET API KEY
openai.api_key = os.getenv("OPENAI_API_KEY")
if openai.api_key in [None, ""]:
    if "api_key" in CONFIG:
        openai.api_key = CONFIG["api_key"]
    else:
        print("Put your OpenAI API key into the config.json file or OPENAI_API_KEY environment variable to skip this prompt.\n")
        openai.api_key = input("Input OpenAI API key: ").strip()

        if openai.api_key == "":
            sys.exit(1)

        save = yesno("Do you want to save this key to config.json?", ["y", "n"])
        if save == "y":
            CONFIG["api_key"] = openai.api_key
            with open("config.json", "w") as f:
                f.write(json.dumps(CONFIG, indent=4))
        print()

# WARN IF THERE IS CODE ALREADY IN THE PROJECT
if os.path.exists("code/") and len(os.listdir("code")) != 0:
    answer = yesno("WARNING! There is already some code in the `code/` folder. GPT-AutoPilot may base the project on these files and has write access to them and might modify or delete them.\n\n" + gpt_functions.list_files("", False) + "\n\nDo you want to continue?", ["YES", "NO", "DELETE"])
    if answer == "DELETE":
        shutil.rmtree("code/")
    elif answer != "YES":
        sys.exit(0)

# CREATE CODE DIRECTORY
if not os.path.exists("code/"):
    os.mkdir("code")

# CREATE HISTORY DIRECTORY
if not os.path.exists("history/"):
    os.mkdir("history")

def compact_commands(messages):
    for msg in messages:
        if msg["role"] == "function" and msg["name"] == "write_file":
            msg["content"] = "Respond with file content"
    return messages

def actually_write_file(filename, content):
    filename = safepath(filename)

    print(f"Wrote to file code/{filename}...")

    parts = re.split("```.*?\n", content + "\n")
    if len(parts) > 2:
        content = parts[1]

    # force newline in the end
    if content[-1] != "\n":
        content = content + "\n"

    # Create parent directories if they don't exist
    parent_dir = os.path.dirname(f"code/{filename}")
    os.makedirs(parent_dir, exist_ok=True)

    if os.path.isdir(f"code/{filename}"):
        return "ERROR: There is already a directory with this name"

    with open(f"code/{filename}", "w") as f:
        f.write(content)

    return f"File {filename} written successfully"

# MAIN FUNCTION
def run_conversation(prompt, model = "gpt-4-0613", messages = [], conv_id = None):
    if conv_id is None:
        conv_id = str(sum(1 for entry in os.scandir("history/"))).zfill(4)

    if messages == []:
        with open("system_message", "r") as f:
            system_message = f.read()

        # add system message
        messages.append({
            "role": "system",
            "content": system_message
        })

        # add list of current files to user prompt
        prompt += "\n\n" + gpt_functions.list_files()

    # add user prompt to chatgpt messages
    messages = chatgpt.send_message(
        message={
            "role": "user",
            "content": prompt
        },
        messages=messages,
        model=model,
        conv_id=conv_id,
    )

    # get chatgpt response
    message = messages[-1]

    mode = None
    filename = None
    function_call = "auto"
    print_message = True

    # loop until project is finished
    while True:
        if message.get("function_call"):
            # get function name and arguments
            function_name = message["function_call"]["name"]
            arguments_plain = message["function_call"]["arguments"]
            arguments = None

            try:
                # try to parse arguments
                arguments = json.loads(arguments_plain)

            # if parsing fails, tell chatgpt to format arguments properly
            except:
                print("ERROR PARSING ARGUMENTS:\n---\n")
                print(arguments_plain)
                print("\n---\n")

                function_response = "Error parsing arguments. Make sure to use properly formatted JSON, with double quotes"

            if arguments is not None:
                # call the function given by chatgpt
                if hasattr(gpt_functions, function_name):
                    function_response = getattr(gpt_functions, function_name)(**arguments)
                else:
                    print(f"NOTICE: GPT called function '{function_name}' that doesn't exist.")
                    function_response = f"Function '{function_name}' does not exist."

            if function_name == "write_file":
                mode = "WRITE_FILE"
                filename = arguments["filename"]
                function_call = "none"
                print_message = False

            # if function returns PROJECT_FINISHED, exit
            if function_response == "PROJECT_FINISHED":
                print("## Project finished! ##")
                next_message = yesno("Do you want to ask something else?\nAnswer", ["y", "n"])
                if next_message == "y":
                    prompt = input("What do you want to ask?\nAnswer: ")
                    return run_conversation(
                        prompt=prompt,
                        model=model,
                        messages=messages,
                        conv_id=conv_id,
                    )
                else:
                    sys.exit(0)

            # send function result to chatgpt
            messages = chatgpt.send_message(
                message={
                    "role": "function",
                    "name": function_name,
                    "content": function_response,
                },
                messages=messages,
                model=model,
                function_call=function_call,
                print_message=print_message,
                conv_id=conv_id,
            )
        else:
            if mode == "WRITE_FILE":
                user_message = actually_write_file(filename, message["content"])

                mode = None
                filename = None
                function_call = "auto"
                print_message = True

                messages = compact_commands(messages)
            else:
                # if chatgpt doesn't respond with a function call, ask user for input
                if "?" in message["content"]:
                    user_message = input("ChatGPT didn't respond with a function. What do you want to say?\nAnswer: ")
                else:
                    # if chatgpt doesn't ask a question, continue
                    user_message = "Ok, continue."

            # send user message to chatgpt
            messages = chatgpt.send_message(
                message={
                    "role": "user",
                    "content": user_message,
                },
                messages=messages,
                model=model,
                conv_id=conv_id,
                print_message=print_message,
            )

        # save last response for the while loop
        message = messages[-1]

def make_prompt_better(prompt):
    print("Making prompt better...")

    try:
        better_prompt = betterprompter.make_better(prompt, CONFIG["model"])
    except:
        if yesno("There was an error in the request. Try again?"):
            return make_prompt_better(prompt)
        else:
            return prompt

    print("## Better prompt: ##\n" + better_prompt)

    if yesno("Do you want to use this prompt?") == "y":
        prompt = better_prompt
    return prompt

# LOAD MESSAGE HISTORY
if len(sys.argv) > 1:
    history_file = sys.argv[1]
    try:
        with open(f"history/{history_file}.json", "r") as f:
            messages = json.load(f)
        print(f"Loaded message history from {history_file}.json")
    except:
        print(f"ERROR: History file {history_file}.json not found")
        sys.exit(1)
else:
    messages = []

# ASK FOR PROMPT
prompt = input("What would you like me to do?\nAnswer: ")

# MAKE PROMPT BETTER
if yesno("Do you want GPT to make your prompt better?") == "y":
    prompt = make_prompt_better(prompt)

# RUN CONVERSATION
run_conversation(
    prompt=prompt,
    model=CONFIG["model"],
    messages=messages,
)
