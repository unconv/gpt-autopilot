#!/usr/bin/env python3

import openai
import json
import os
import traceback
import sys
import shutil
import re
import time
import random
import copy

import gpt_functions
from helpers import yesno, safepath, codedir, numberfile, reset_code_folder
import chatgpt
import betterprompter
from config import get_config, save_config
import tokens
import cmd_args
import checklist
import prompt_selector

CONFIG = get_config()

def compact_commands(messages):
    for msg in messages:
        if msg["role"] == "function" and msg["name"] == "file_open_for_writing":
            msg["content"] = "Respond with file content. Put file content between lines START_OF_FILE_CONTENT and END_OF_FILE_CONTENT"
    return messages

def remove_hallucinations(messages):
    for msg in messages:
        if msg["role"] == "function" and msg["name"] == "file_open_for_writing":
            try:
                args = json.loads(msg["function_call"]["arguments"])
                if "content" in args:
                    args.pop("content")
                    msg["function_call"]["arguments"] = json.dumps(args)
            except:
                continue
    return messages

def unwrap_comments(content, tags):
    for tag in tags:
        # Remove HTML-style comments
        content = re.sub(r"<!--([\s]+)?"+tag+r"([\s]+)?-->", tag, content, flags=re.DOTALL)

        # Remove C-style comments
        content = re.sub(r"/\*([\s]+)?"+tag+r"([\s]+)?\*/", tag, content, flags=re.DOTALL)

        # Remove PHP-style comments
        content = re.sub(r"//([\s]+)?"+tag+r"([\s]+)?$", tag, content, flags=re.MULTILINE)

        # Remove Python-style comments
        content = re.sub(r"#([\s]+)?"+tag+r"$", tag, content, flags=re.MULTILINE)
    return content

def strip_markdown(content):
    content = content.strip()
    if content[0:3] == "```":
        content = re.sub(r"^\s*```[^\n]+\n", "", content)
        content = re.sub(r"\n```\s*$", "", content)
    return content

def check_content_format(filename, content):
    # detect partial file content response
    if "END_OF_FILE_CONTENT" not in content:
        print(f"ERROR:    Partial write response for code/{filename}...")
        return "ERROR: No END_OF_FILE_CONTENT detected"

    # detect wrongly formatted response
    if "START_OF_FILE_CONTENT" not in content:
        print(f"ERROR:    Invalid content format for code/{filename}...")
        return "ERROR: No START_OF_FILE_CONTENT detected"

    # detect gpt-3.5 stupidity
    if "`START_OF_FILE_CONTENT` and `END_OF_FILE_CONTENT`" in content:
        print(f"ERROR:    Invalid content format for code/{filename}...")
        return "ERROR: Your response needs to start with START_OF_FILE_CONTENT and end with END_OF_FILE_CONTENT, with the file content in between. No other explanations. No apologies. Just the file content."

    return None

def parse_file_content(content):
    # Sometimes ChatGPT makes the start and
    # end tags comments, so we have to remove
    # comment syntax around these
    content = unwrap_comments(content, [
        "START_OF_FILE_CONTENT",
        "END_OF_FILE_CONTENT",
    ])

    parts = content.split("START_OF_FILE_CONTENT")
    content = parts[1]
    parts = content.split("END_OF_FILE_CONTENT")
    content = parts[0]

    content = strip_markdown(content)

    # force newline in the end
    if content != "" and content[-1] != "\n":
        content = content + "\n"

    return content

def actually_write_file(filename, content):
    filename = safepath(filename)

    check = check_content_format(filename, content)
    if check is not None:
        return check

    content = parse_file_content(content)

    fullpath = codedir(filename)

    # Create parent directories if they don't exist
    parent_dir = os.path.dirname(fullpath)
    os.makedirs(parent_dir, exist_ok=True)

    if os.path.isdir(fullpath):
        return "ERROR: There is already a directory with this name"

    with open(fullpath, "w") as f:
        f.write(content)

    print(f"DONE:     Wrote to file code/{filename}...")
    return f"File {filename} written successfully"

def actually_append_file(filename, content):
    filename = safepath(filename)

    check = check_content_format(filename, content)
    if check is not None:
        return check

    content = parse_file_content(content)

    # Create parent directories if they don't exist
    parent_dir = os.path.dirname(codedir(filename))
    os.makedirs(parent_dir, exist_ok=True)

    with open(codedir(filename), "a") as f:
        f.write(content)

    with open(codedir(filename), "r") as f:
        new_file_content = f.read()

    return f"APPEND_OK: File {filename} appended successfully. IMPORTANT: If you appended code to a file, you might have appended it after the main function or an event listener or other code scope accidentally. Please check the code and rewrite the whole file if you made a mistake. The content of the file is now this:\n\n{new_file_content}"

def print_task_finished(model):
    tokens_total = int(tokens.token_usage["total"])
    totaltokens = str(tokens_total).rjust(13, " ")

    price_total = round(tokens.get_token_cost(model), 2)
    total_price = (str(price_total)+" USD").rjust(13, " ")

    task_tokens = tokens_total - tokens.prev_tokens_total
    task_tokens = str(task_tokens).rjust(13, " ")
    task__price = round(price_total - tokens.prev_price_total, 2)
    task__price = (str(task__price)+" USD").rjust(13, " ")

    print()
    print(f"###############################")
    print(f"# Task is finished!           #")
    print(f"# Task tokens:  {task_tokens} #")
    print(f"# Task price:   {task__price} #")
    print(f"# Total tokens: {totaltokens} #")
    print(f"# Total price:  {total_price} #")
    print(f"###############################")
    print()

    tokens.prev_tokens_total = tokens_total
    tokens.prev_price_total = price_total

def ask_model_switch():
    if yesno("ERROR: You don't seem to have access to the GPT-4 API. Would you like to change to GPT-3.5?") == "y":
        CONFIG["model"] = "gpt-3.5-turbo-16k-0613"
        save_config(CONFIG)
        return CONFIG["model"]
    else:
        sys.exit(1)

def fix_function_name(function_name):
    if function_name in ["new_file", "create_file"]:
        return "file_open_for_writing"
    return function_name

def fix_arguments(function_name, arguments):
    if function_name == "file_open_for_writing" and "path" in arguments:
        arguments["filename"] = arguments["path"]
        del arguments["path"]
    if function_name == "ask_clarification" and "question" in arguments:
        arguments["questions"] = arguments["question"]
        del arguments["question"]
    return arguments

def function_list(model):
    func_list = ""
    for func in gpt_functions.get_definitions(model):
        func_list += func["name"] + "("
        func_list += ", ".join([key for key in func["parameters"]["properties"].keys()])
        func_list += ")\n"
    return func_list.strip()

# MAIN FUNCTION
def run_conversation(prompt, model = "gpt-4-0613", messages = [], conv_id = None, recursive = True, temp = 0.6):
    if conv_id is None:
        conv_id = numberfile("history")

    if messages == []:
        print("GPT-API:  Selecting system message...")
        try:
            prompt_data = prompt_selector.get_data(prompt, model, temp)
        except:
            print("ERROR:    Unable to detect system message")
            prompt_data = {
                "slug": "default",
                "system_message": path.join("prompts", "default", "system_message")
            }

        slug = prompt_data["slug"]
        if slug != "default":
            print(f"SYSTEM:   Using system message '{slug}'")

        if "checklist" in prompt_data:
            print(f"SYSTEM:   Using checklist '{slug}'")
            checklist.load_checklist(prompt_data["checklist"])
            checklist.activate_checklist()
        else:
            print()

        with open(prompt_data["system_message"], "r") as f:
            system_message = f.read()

        # add system message
        messages.append({
            "role": "system",
            "content": system_message
        })

        # add list of current files to user prompt
        prompt += "\n\n" + gpt_functions.list_files()

        # add list of functions to first prompt
        prompt += "\n\nYou can call these functions: " + function_list(model)

    # add user prompt to chatgpt messages
    try:
        messages = chatgpt.send_message(
            message={
                "role": "user",
                "content": prompt
            },
            messages=messages,
            model=model,
            conv_id=conv_id,
            temp=temp,
        )
    except Exception as e:
        if "The model: `gpt-4-0613` does not exist" in str(e):
            model = ask_model_switch()
        else:
            raise

    # get chatgpt response
    message = messages[-1]

    mode = None
    filename = None
    function_call = "auto"
    print_message = True

    # loop until project is finished
    while True:
        if message.get("function_call"):
            # sometimes ChatGPT hallucinates dots in function name
            message["function_call"]["name"] = re.sub(r'\W+', '', message["function_call"]["name"])

            # get function name and arguments
            function_name = message["function_call"]["name"]
            arguments_plain = message["function_call"]["arguments"]
            arguments = None

            # fix hallucinations
            function_name = fix_function_name(function_name)

            if not hasattr(gpt_functions, function_name):
                print(f"NOTICE:   GPT called function '{function_name}' that doesn't exist.")
                function_response = f"Function '{function_name}' does not exist. You can call these functions:"
                function_response += function_list(model)
            else:
                try:
                    # try to parse arguments
                    arguments = json.loads(arguments_plain)

                # if parsing fails, try to fix format
                except:
                    try:
                        # gpt-3.5 sometimes uses backticks
                        # instead of double quotes in JSON value
                        print("ERROR:    Invalid JSON arguments. Fixing...")
                        arguments_fixed = arguments_plain.replace("`", '"')
                        arguments = json.loads(arguments_fixed)
                    except:
                        try:
                            # gpt-3.5 sometimes omits single quotes
                            # from around keys
                            print("ERROR:    Invalid JSON arguments. Fixing again...")
                            arguments_fixed = re.sub(r'(\b\w+\b)(?=\s*:)', r'"\1"')
                            arguments = json.loads(arguments_fixed)
                        except:
                            try:
                                # gpt-3.5 sometimes uses single quotes
                                # around keys, instead of double quotes
                                print("ERROR:    Invalid JSON arguments. Fixing third time...")
                                arguments_fixed = re.sub(r"'(\b\w+\b)'(?=\s*:)", r'"\1"')
                                arguments = json.loads(arguments_fixed)
                            except:
                                print("ERROR:    Failed to parse function arguments")
                                #print("ERROR PARSING ARGUMENTS:\n---\n")
                                #print(arguments_plain)
                                #print("\n---\n")

                                if function_name == "replace_text":
                                    function_response = "ERROR! Please try to replace a shorter text or try another method"
                                else:
                                    function_response = "Error parsing arguments. Make sure to use properly formatted JSON, with double quotes. If this error persist, change tactics"

                if arguments is not None:
                    # fix hallucinations
                    arguments = fix_arguments(function_name, arguments)

                    # call the function given by chatgpt
                    try:
                        function_response = getattr(gpt_functions, function_name)(**arguments)
                    except TypeError:
                        function_response = "ERROR: Invalid function parameters"

                    if function_name == "file_open_for_writing":
                        mode = "WRITE_FILE"
                        filename = arguments["filename"]
                        function_call = "none"
                        print_message = False

                    if function_name == "file_open_for_appending":
                        mode = "APPEND_FILE"
                        filename = arguments["filename"]
                        function_call = "none"
                        print_message = False

            messages = remove_hallucinations(messages)

            # if function returns PROJECT_FINISHED, exit
            if function_response == "PROJECT_FINISHED":
                if recursive == False:
                    checklist.activate_checklist()
                    print_task_finished(model)
                    return

                do_checklist = "no-checklist" not in cmd_args.args and checklist.active_list != []
                if do_checklist:
                    if "use-checklist" not in cmd_args.args and len(checklist.active_list) == len(checklist.the_list):
                        if yesno("\nGPT: Do you want to run through the checklist?\nYou") == "n":
                            checklist.active_list = []
                            do_checklist = False
                        print()
                    if do_checklist:
                        gpt_functions.tasklist_finished = False
                        prompt = checklist.active_list.pop(0)
                        print("CHECKLIST: " + prompt)

                if not do_checklist:
                    print_task_finished(model)
                    checklist.activate_checklist()
                    next_message = yesno("GPT: Do you want to ask something else?\nYou:", ["y", "n"])
                    print()
                    if next_message == "y":
                        prompt = input("GPT: What do you want to ask?\nYou: ")
                        print()
                    else:
                        print("Exiting")
                        sys.exit(0)

                return run_conversation(
                    prompt=prompt,
                    model=model,
                    messages=messages,
                    conv_id=conv_id,
                    recursive=recursive,
                )

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
                temp=temp,
            )
        else:
            if mode == "WRITE_FILE":
                user_message = actually_write_file(filename, message["content"])

                if "ERROR" not in user_message:
                    mode = None
                    filename = None
                    function_call = "auto"
                    print_message = True

                messages = compact_commands(messages)
            elif mode == "APPEND_FILE":
                user_message = actually_append_file(filename, message["content"])

                if "ERROR" not in user_message:
                    mode = None
                    filename = None
                    function_call = "auto"
                    print_message = True

                messages = compact_commands(messages)
            else:
                if len(message["content"]) > 400:
                    user_message = "ERROR: Please use function calls"
                # if chatgpt doesn't respond with a function call, ask user for input
                elif "?" in message["content"] or \
                   "Let me know" in message["content"] or \
                   "Please provide" in message["content"] or \
                   "Could you" in message["content"] or \
                   "Can you" in message["content"] or \
                   "Do you know" in message["content"] or \
                   "Tell me" in message["content"] or \
                   "Explain" in message["content"] or \
                   "What is" in message["content"] or \
                   "How does" in message["content"]:
                    user_message = input("You:\n")
                    print()
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
                temp=temp,
            )

        # save last response for the while loop
        message = messages[-1]

def make_prompt_better(prompt, ask=True):
    print("\nMaking prompt better...")

    try:
        better_prompt = betterprompter.make_better(prompt, CONFIG["model"])
    except Exception as e:
        better_prompt = prompt
        if "The model: `gpt-4-0613` does not exist" in str(e):
            ask_model_switch()
            return make_prompt_better(prompt, ask)
        elif yesno("Unable to make prompt better. Try again?") == "y":
            return make_prompt_better(prompt, ask)
            print()
        else:
            print()
            return prompt

    if prompt != better_prompt:
        print()
        print("## Better prompt: ##\n" + better_prompt)
        print()

        if ask == False or yesno("Do you want to use this prompt?") == "y":
            print("Using better prompt...")
            prompt = better_prompt
        else:
            print("Using original prompt...")

    return prompt

def load_message_history(arguments):
    if "conv" in arguments:
        history_file = arguments["conv"]
        try:
            with open(f"history/{history_file}.json", "r") as f:
                messages = json.load(f)
            print(f"INFO:     Loaded message history from {history_file}.json")
        except:
            print(f"ERROR:    History file {history_file}.json not found")
            sys.exit(1)
    else:
        messages = []

    return messages

def get_api_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key in [None, ""]:
        if "api_key" in CONFIG:
            api_key = CONFIG["api_key"]
        else:
            print("Put your OpenAI API key into the config.json file or OPENAI_API_KEY environment variable to skip this prompt.\n")
            api_key = input("Input OpenAI API key: ").strip()

            if api_key == "":
                sys.exit(1)

            save = yesno("Do you want to save this key to config.json?", ["y", "n"])
            if save == "y":
                CONFIG["api_key"] = api_key
                save_config(CONFIG)
            print()
    return api_key

def warn_existing_code():
    if os.path.isdir("code") and len(os.listdir("code")) != 0:
        answer = yesno(
            "#####################################################\n"+
            "# WARNING!                                          #\n"+
            "# There is already some code in the `code/` folder. #\n"+
            "# GPT-AutoPilot may base the project on these files #\n"+
            "# and and might modify or delete them.              #\n"+
            "#####################################################"+
            "\n\n"+
            gpt_functions.list_files("", False)+
            "\n\n"+
            "Do you want to continue?", ["YES", "NO", "DELETE"])
        if answer == "DELETE":
            reset_code_folder()
        elif answer != "YES":
            sys.exit(0)
        print()

def create_directories():
    dirs = ["code", "history", "versions"]
    for directory in dirs:
        if not os.path.isdir(directory):
            os.mkdir(directory)

def get_temp(arguments):
    if "temp" in arguments:
        return arguments["temp"]
    return 0.6

def maybe_make_prompt_better(prompt, args, version_loop = False):
    if version_loop == True and "better-versions" not in args:
        return prompt
    if "not-better" not in args:
        if "better" in args or yesno("GPT: Do you want me to make your prompt better?\nYou") == "y":
            ask = "better" not in args or "ask-better" in args
            prompt = make_prompt_better(prompt, ask)
        print()
    return prompt

def run_versions(prompt, args, version_messages, temp, prev_version = 1):
    version_id = numberfile("versions", folder=True)

    if "versions" in args:
        versions = args["versions"]
        print(f"INFO:     Creating {versions} versions...")
    else:
        versions = 1

    version_dir = os.path.join("versions", str(version_id))
    ver_orig_dir = os.path.join(version_dir, "orig")

    if versions > 1:
        if not os.path.isdir(version_dir):
            os.mkdir(version_dir)

        shutil.copytree("code", ver_orig_dir)
        recursive = False
    else:
        recursive = True

    version_folders = []
    orig_messages = version_messages[prev_version]

    for version in range(1, versions+1):
        # reset message history for every version
        messages = copy.deepcopy(orig_messages)

        if versions > 1:
            print(f"\n## VERSION {version} (temp: {temp}) ##")

        # MAKE PROMPT BETTER
        version_loop = version > 1
        prompt = maybe_make_prompt_better(prompt, cmd_args.args, version_loop)

        if version != 1:
            # randomize temperature for every version
            temp = round( temp_orig + random.uniform(-0.1, 0.1), 2 )

            # always start with original version
            shutil.copytree(ver_orig_dir, "code")

        # RUN CONVERSATION
        run_conversation(
            prompt=prompt,
            model=CONFIG["model"],
            messages=messages,
            recursive=recursive,
            temp=temp,
        )

        if versions > 1:
            version_folder = os.path.join(version_dir, f"v{version}")
            shutil.copytree("code", version_folder)
            shutil.rmtree("code")
            version_folders.append(version_folder)

        # save message history of each version
        version_messages[version] = copy.deepcopy(messages)

    if versions > 1:
        print("\n# ALL VERSIONS FINISHED ##")
        print("You can find all versions here:")
        for number, verfolder in enumerate(version_folders):
            print(f"- Version {number+1}: {verfolder}")

        next_up = 0
        while int(next_up) not in range(1, versions+1):
            next_up = input(f"\nIf you want to continue, please input version number to continue from (1-{versions}) (or 'exit' to quit): ")

            if str(next_up) in ["exit", "quit", "e", "q"]:
                sys.exit(0)

        next_version = int(next_up)

        # move selected version to code folder and start over
        shutil.copytree(version_folders[next_version-1], "code")

        prompt = input("GPT: What would you like to do next?\nYou: ")
        print()
        run_versions(prompt, args, version_messages, temp, next_version)

def print_model_info():
    print("#######################################")
    print("# USING MODEL: " + CONFIG["model"].rjust(22, " ") + " #")
    if "gpt-4" not in CONFIG["model"]:
        print("# NOTICE:        GPT-4 is recommended #")
    print("#######################################")
    print()

def override_model(model):
    if "model" in cmd_args.args:
        model = cmd_args.args["model"]
        if model in ["gpt-4", "gpt4"]:
            model = "gpt-4-0613"
        elif model in ["gpt-3", "gpt3", "gpt-3.5", "gpt3.5"]:
            model = "gpt-3.5-turbo-16k-0613"
        elif model in ["gpt-3-4k", "gpt3-4k", "gpt-3.5-4k", "gpt3.5-4k"]:
            model = "gpt-3.5-turbo-0613"
    return model

# OVERRIDE MODEL
CONFIG["model"] = override_model(CONFIG["model"])

# LOAD MESSAGE HISTORY
version_messages = {
    1: load_message_history(cmd_args.args)
}

# GET API KEY
openai.api_key = get_api_key()

# WARN IF THERE IS CODE ALREADY IN THE PROJECT
warn_existing_code()

# CREATE DATA DIRECTORIES
create_directories()

# GET TEMPERATURE
temp = get_temp(cmd_args.args)
temp_orig = temp

# PRINT MODEL
print_model_info()

# ASK FOR PROMPT
if "prompt" in cmd_args.args:
    prompt = cmd_args.args["prompt"]
else:
    prompt = input("GPT: What would you like me to do?\nYou: ")
    print()

run_versions(prompt, cmd_args.args, version_messages, temp)
