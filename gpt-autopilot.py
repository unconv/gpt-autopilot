#!/usr/bin/env python3

import traceback
import openai
import shutil
import random
import json
import copy
import time
import sys
import os
import re

from modules.helpers import yesno, safepath, codedir, numberfile, reset_code_folder, relpath, ask_input
from modules.config import get_config, save_config
from modules import prompt_selector
from modules import gpt_functions
from modules import betterprompter
from modules import filesystem
from modules import checklist
from modules import cmd_args
from modules import chatgpt
from modules import tokens
from modules import paths
from modules import git

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
        print(f"ERROR:    Partial write response for {filename}...")
        return "ERROR: No END_OF_FILE_CONTENT detected"

    # detect wrongly formatted response
    if "START_OF_FILE_CONTENT" not in content:
        print(f"ERROR:    Invalid content format for {filename}...")
        return "ERROR: No START_OF_FILE_CONTENT detected"

    # detect gpt-3.5 stupidity
    if "`START_OF_FILE_CONTENT` and `END_OF_FILE_CONTENT`" in content:
        print(f"ERROR:    Invalid content format for {filename}...")
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
    fullpath = safepath(filename)
    relative = relpath(fullpath)

    check = check_content_format(relative, content)
    if check is not None:
        return check

    content = parse_file_content(content)

    # Create parent directories if they don't exist
    parent_dir = os.path.dirname(fullpath)
    filesystem.makedirs(parent_dir)

    if filesystem.isdir(fullpath):
        return "ERROR: There is already a directory with this name"

    filesystem.write(fullpath, content)

    print(f"DONE:     Wrote to file {relative}")
    return f"File {relative} written successfully"

def actually_append_file(filename, content):
    fullpath = safepath(filename)
    relative = relpath(fullpath)

    check = check_content_format(relative, content)
    if check is not None:
        return check

    content = parse_file_content(content)

    # Create parent directories if they don't exist
    parent_dir = os.path.dirname(fullpath)
    filesystem.makedirs(parent_dir)

    if filesystem.isdir(fullpath):
        return "ERROR: This is a directory, not a file"

    filesystem.write(fullpath, content, "a")

    new_file_content = filesystem.read(fullpath)

    return f"APPEND_OK: File {relative} appended successfully. IMPORTANT: If you appended code to a file, you might have appended it after the main function or an event listener or other code scope accidentally. Please check the code and rewrite the whole file if you made a mistake. The content of the file is now this:\n\n{new_file_content}"

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
    if yesno("\nERROR: You don't seem to have access to the GPT-4 API. Would you like to change to GPT-3.5?") == "y":
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

def function_list(model, exclude=[]):
    func_list = ""
    for func in gpt_functions.get_definitions(model):
        if func["name"] in exclude:
            continue
        func_list += func["name"] + "("
        func_list += ", ".join([key for key in func["parameters"]["properties"].keys()])
        func_list += ")\n"
    return func_list.strip()

def parse_filename(arguments):
    filename_pattern = r'"filename"\s*:\s*"([^"]*)"'
    match = re.search(filename_pattern, arguments)
    if match is None:
        raise Exception("Invalid filename argument")
    return match.group(1)

def fix_json_arguments(function_name, arguments_plain, message):
    if function_name == "write_file":
        print("ERROR:    Switching to file_open_for_writing")
        function_name = "file_open_for_writing"
    elif function_name == "append_file":
        print("ERROR:    Switching to file_open_for_appending")
        function_name = "file_open_for_appending"
    else:
        print("ERROR:    Failed to parse arguments")
        return (
            function_name,
            "ERROR: Failed to parse arguments",
            message,
            None,
        )

    arguments = {
        "filename": parse_filename(arguments_plain)
    }
    message["function_call"]["name"] = function_name
    message["function_call"]["arguments"] = json.dumps(arguments)

    return (
        function_name,
        None,
        message,
        arguments,
    )

def create_zip():
    if "zip-dir" in cmd_args.args:
        zip_folder = cmd_args.args["zip-dir"]
        if not os.path.isdir(zip_folder):
            print("ERROR: Specified zip folder doesn't exist")
            return
    else:
        zip_folder = "projects"
        os.makedirs(paths.relative(zip_folder), exist_ok=True)

    if "zip-name" in cmd_args.args:
        zip_filename = os.path.basename(cmd_args.args["zip-name"])
    else:
        zip_filename = "project.zip"

    unique_filename = zip_filename

    num = 0
    zip_filepath = paths.relative(zip_folder, unique_filename)
    while os.path.exists(zip_filepath):
        num += 1
        unique_filename = zip_filename.removesuffix(".zip") + "-" + str(num) + ".zip"
        zip_filepath = paths.relative(zip_folder, unique_filename)
        if num > 1000:
            print("ERROR: Too many projects in " + zip_folder + " folder")
            return

    filesystem.create_zip(zip_filepath)
    print("###################################################################")
    print("# The project has been saved to: " + relpath(zip_filepath, os.path.dirname(__file__)).rjust(32, " ") + " #")
    print("###################################################################")
    print()

# MAIN FUNCTION
def run_conversation(prompt, model = "gpt-3.5-turbo-16k-0613", messages = [], conv_id = None, recursive = True, temp = 1.0, extra_messages = []):
    if conv_id is None:
        conv_id = numberfile(paths.relative("history"))

    # format user message for ChatGPT
    user_message = {
        "role": "user",
        "content": prompt
    }

    # add extra messages
    if extra_messages != []:
        messages.append(user_message)
        messages += extra_messages

        # take user message from last extra message
        user_message = messages.pop()

    # save message history
    chatgpt.save_message_history(conv_id, messages)

    # add user prompt to chatgpt messages
    try:
        messages = chatgpt.send_message(
            message=user_message,
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
        function_message = None
        if message.get("function_call"):
            # sometimes ChatGPT hallucinates dots in function name
            message["function_call"]["name"] = re.sub(r'\W+', '', message["function_call"]["name"])

            # get function name and arguments
            function_name = message["function_call"]["name"]
            arguments_plain = message["function_call"]["arguments"]
            arguments = None

            # fix hallucinations
            function_name = fix_function_name(function_name)
            function_response = "ERROR: Invalid parameters"

            if not gpt_functions.function_available(function_name, model):
                print(f"NOTICE:   GPT called function '{function_name}' that doesn't exist.")
                function_response = f"Function '{function_name}' does not exist. You can call these functions:"
                function_response += function_list(model)
            else:
                try:
                    # try to parse arguments
                    arguments = json.loads(arguments_plain)

                # if parsing fails, switch file operation functions
                except:
                    try:
                        function_name, function_response, message, arguments = fix_json_arguments(
                            function_name,
                            arguments_plain,
                            message
                        )
                    except Exception as e:
                        print("ERROR:    Failed to fix arguments: " + str(e))
                        function_response = "ERROR: Failed to parse arguments"

                if arguments is not None:
                    # fix hallucinations
                    arguments = fix_arguments(function_name, arguments)

                    # call the function given by chatgpt
                    try:
                        function_response = getattr(gpt_functions, function_name)(**arguments)

                        if function_name not in ["task_finished", "project_finished", "make_tasklist"]:
                            gpt_functions.task_operation_performed = True

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

                    except (TypeError, KeyError):
                        function_response = "ERROR: Invalid function parameters"
                        print("ERROR:    Invalid function parameters")

            messages = remove_hallucinations(messages)

            gpt_functions.tasklist_skipped = False

            # make git commit after finishing task and running a command
            if "git" in cmd_args.args and (function_response == "PROJECT_FINISHED" or (
                function_name == "run_cmd" and function_response != "I don't want to run that command"
            )):
                commit = git.commit(copy.deepcopy(messages), model, temp)
                if commit is not None:
                    messages.append(commit)

                # save message history
                chatgpt.save_message_history(conv_id, messages)

            # if we got answers to clarifying questions
            if isinstance(function_response, dict) and "clarifications" in function_response:
                # remove ask_clarifications function call from history
                messages.pop()

                # add questions and answers to message history
                messages += function_response["clarifications"]
                function_message = messages.pop()

            # remove task list modification requests from history
            elif isinstance(function_response, dict) and "TASK_LIST_RECEIVED" in function_response:
                # remove tasklist functions from history
                prev_message = messages.pop(-2)
                while '"name": "make_tasklist"' in json.dumps(prev_message):
                    prev_message = messages.pop(-2)
                messages.insert(-1, prev_message)

            # if we want to skip the tasklist, reset it
            elif function_response == "SKIP_TASKLIST":
                gpt_functions.tasklist = []
                gpt_functions.active_tasklist = []
                gpt_functions.tasklist_finished = False
                gpt_functions.tasklist_skipped = True

                # remove tasklist functions from history
                last_message = messages.pop()
                while '"name": "make_tasklist"' in json.dumps(last_message):
                    last_message = messages.pop()
                function_message = last_message

            # if function returns PROJECT_FINISHED, exit
            elif function_response == "PROJECT_FINISHED":
                if recursive == False:
                    checklist.activate_checklist()
                    print_task_finished(model)
                    return messages

                do_checklist = "no-checklist" not in cmd_args.args and checklist.active_list != []
                if do_checklist:
                    if "do-checklist" not in cmd_args.args and len(checklist.active_list) == len(checklist.the_list):
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

                    if "one-task" in cmd_args.args:
                        sys.exit(0)

                    checklist.activate_checklist()
                    next_message = yesno("GPT: Do you want to do something else?\nYou:", ["y", "n"])
                    print()
                    if next_message == "y":
                        git.print_help()

                        prompt = ask_input("GPT: What do you want to do?\nYou: ")
                        print()

                        while "git" in cmd_args.args and prompt in ["revert", "retry"]:
                            if git.commit_count > 1:
                                if git.commit_count > 2:
                                    end = ""
                                else:
                                    end = "\n"

                                print("REVERT:   Reverted back to previous stage\n          ", end=end, flush=True)
                                last_prompt, messages = git.revert(messages)
                                print()
                                # save message history
                                chatgpt.save_message_history(conv_id, messages)

                                if prompt == "retry":
                                    prompt = last_prompt
                                    last_prompt_trimmed = prompt.split("\n")[0]
                                    print("RETRY:    " + last_prompt_trimmed + "...")
                                    print()
                                    break
                            else:
                                print("ERROR:    No commits to revert")
                                print()

                            git.print_help()
                            prompt = ask_input("GPT: What would you like to do next?\nYou: ")
                            print()

                        while "git" in cmd_args.args and prompt == "commit":
                            prompt = git.own_commit()

                            if prompt == False:
                                print("ERROR: No changes have been made.\n")
                                git.print_help()
                                prompt = ask_input("GPT: What would you like to do next?\nYou: ")
                                print()
                    else:
                        if "zip" in cmd_args.args:
                            create_zip()
                        print("Exiting")
                        sys.exit(0)

                return run_conversation(
                    prompt=prompt,
                    model=model,
                    messages=messages,
                    conv_id=conv_id,
                    recursive=recursive,
                )

            if function_message is None:
                function_message = {
                    "role": "function",
                    "name": function_name,
                    "content": function_response,
                }

            # send function result to chatgpt
            messages = chatgpt.send_message(
                message=function_message,
                messages=messages,
                model=model,
                function_call=function_call,
                print_message=print_message,
                conv_id=conv_id,
                temp=temp,
            )
        else:
            if chatgpt.create_outline:
                chatgpt.create_outline = False

                # remove prompt about creating outline
                messages.pop(-2)

                # remove old outline
                if gpt_functions.modify_outline:
                    messages.pop(-2)

                if "use-outline" in cmd_args.args or yesno("\nGPT: Do you want to use this project outline?\nYou") == "y":
                    user_message = "Thank you. Please continue to implement fully the complete project"

                    # add outline to initial questions for versions
                    gpt_functions.initial_questions.append({
                        "role": "assistant",
                        "content": message["content"]
                    })
                    gpt_functions.initial_questions.append({
                        "role": "user",
                        "content": user_message
                    })
                else:
                    changes = ask_input("\nGPT: What would you like to modify? (type 'skip' to skip outline)\nYou: ")
                    user_message = "Thank you for the project outline. Please make the following changes to it and respond only with the new project outline in the first person: " + changes
                    gpt_functions.modify_outline = True
                    gpt_functions.outline_created = False
                print()
            elif mode == "WRITE_FILE":
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
                   "Please provide" in message["content"] or \
                   "Could you" in message["content"] or \
                   "Can you" in message["content"] or \
                   "Do you know" in message["content"] or \
                   "Tell me" in message["content"] or \
                   "Explain" in message["content"] or \
                   "What is" in message["content"] or \
                   "How does" in message["content"]:
                    if "continue" in cmd_args.args:
                        user_message = "Please continue with using the given functions."
                    else:
                        user_message = ask_input("You:\n")
                        print()
                else:
                    # if chatgpt doesn't ask a question, continue
                    if gpt_functions.tasklist_finished:
                        what_to_call = "project_finished"
                    else:
                        what_to_call = "task_finished"

                    user_message = "OK. If there is anything left to do in the project, do it. Otherwise call " + what_to_call

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

def make_prompt_better(prompt, orig_prompt=None, ask=True, temp = 1.0, messages = []):
    print("\nMaking prompt better...")

    if orig_prompt is None:
        orig_prompt = prompt

    try:
        better_prompt, messages = betterprompter.make_better(
            prompt=prompt,
            model=CONFIG["model"],
            temp=temp,
            messages=messages
        )
    except SystemExit:
        raise
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

        if ask == False or yesno("GPT: Do you want to use this prompt?\nYou") == "y":
            print("\nUsing better prompt...")
            prompt = better_prompt
        else:
            answer = ask_input("\nGPT: What do you want to modify in the prompt? (type 'orig' to use original)\nYou: ")
            if answer == "orig":
                print("\nUsing original prompt...")
                return orig_prompt

            return make_prompt_better(
                prompt=answer,
                orig_prompt=orig_prompt,
                ask=ask,
                temp=temp,
                messages=messages
            )

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
            api_key = ask_input("Input OpenAI API key: ").strip()

            if api_key == "":
                sys.exit(1)

            save = yesno("Do you want to save this key to config.json?", ["y", "n"])
            if save == "y":
                CONFIG["api_key"] = api_key
                save_config(CONFIG)
            print()
    return api_key

def warn_existing_code():
    if os.path.isdir(codedir()) and len(os.listdir(codedir())) != 0:
        if "delete" in cmd_args.args:
            reset_code_folder()
            return

        answer = yesno(
            "#####################################################\n"+
            "# WARNING!                                          #\n"+
            "# There are already files in the project folder.    #\n"+
            "# GPT-AutoPilot may base the project on these files #\n"+
            "# and and might modify or delete them.              #\n"+
            "#####################################################"+
            "\n\n"+
            gpt_functions.list_files("", print_output=False, ignore=[])+
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
        directory = paths.relative(directory)
        if not os.path.isdir(directory):
            os.mkdir(directory)

def get_temp(arguments):
    if "temp" in arguments:
        return arguments["temp"]
    return 1.0

def maybe_make_prompt_better(prompt, args, version_loop = False):
    if version_loop == True and "better-versions" not in args:
        return prompt
    if "not-better" not in args:
        if "better" in args or yesno("\nGPT: Do you want me to make your prompt better?\nYou") == "y":
            ask = "better" not in args or "ask-better" in args
            prompt = make_prompt_better(
                prompt=prompt,
                ask=ask
            )
        print()
    return prompt

def run_versions(prompt, args, version_messages, temp, prev_version = 1):
    version_id = numberfile(paths.relative("versions"), folder=True)

    if "versions" in args:
        versions = args["versions"]
        print(f"INFO:     Creating {versions} versions...\n")
    else:
        versions = 1

    version_dir = paths.relative("versions", str(version_id))
    ver_orig_dir = os.path.join(version_dir, "orig")

    if versions > 1:
        if not filesystem.isdir(version_dir):
            filesystem.makedirs(version_dir)

        filesystem.copytree(codedir(), ver_orig_dir)
        recursive = False
    else:
        recursive = True

    version_folders = []
    orig_messages = version_messages[prev_version]

    extra_prompt = ""

    # reset tasklist for every version iteration
    gpt_functions.tasklist = []
    gpt_functions.active_tasklist = []
    gpt_functions.tasklist_finished = True

    # add system message on the first round
    if orig_messages == []:
        system_message = prompt_selector.select_system_message(prompt, CONFIG["model"], temp)

        # add system message
        orig_messages.append({
            "role": "system",
            "content": system_message
        })

        # add list of current files to user prompt
        extra_prompt += "\n\n" + gpt_functions.list_files()

        # add list of functions to first prompt
        extra_prompt += "\n\nYou can call these functions among others: " + function_list(CONFIG["model"], exclude=[
            "run_cmd",
            "append_file",
            "file_open_for_appending",
            "replace_text",
            "list_files",
            "read_file",
            "delete_file",
        ])

    for version in range(1, versions+1):
        # reset message history for every version
        messages = copy.deepcopy(orig_messages)

        if versions > 1:
            print(f"\n## VERSION {version} (temp: {temp}) ##")

        # MAKE PROMPT BETTER
        version_loop = version > 1
        prompt = maybe_make_prompt_better(prompt, cmd_args.args, version_loop)

        # add extra data to prompt
        final_prompt = prompt + extra_prompt

        # messages to be added to first ChatGPT request
        # after the new user prompt
        extra_messages = []

        # add initial questions to versions' chat history
        extra_messages += gpt_functions.initial_questions

        # reset tasklist for every version
        gpt_functions.tasklist_finished = True
        if not gpt_functions.use_single_tasklist:
            gpt_functions.active_tasklist = copy.deepcopy(gpt_functions.tasklist)

        # add tasklist to every version
        if gpt_functions.active_tasklist != []:
            print("TASK:     " + gpt_functions.active_tasklist[0])
            extra_messages.append({
                "role": "assistant",
                "content": None,
                "function_call": {
                    "name": "make_tasklist",
                    "arguments": json.dumps({
                        "tasks": gpt_functions.active_tasklist
                    })
                }
            })
            extra_messages.append({
                "role": "function",
                "name": "make_tasklist",
                "content": "TASK_LIST_RECEIVED: Start with first task: " + gpt_functions.active_tasklist.pop(0) + ". Do all the steps involved in the task and only then run the task_finished function."
            })

        if version != 1:
            # randomize temperature for every version
            temp = round( float(temp_orig) + random.uniform(-0.1, 0.1), 2 )

            # always start with original version
            filesystem.copytree(ver_orig_dir, codedir())

        # RUN CONVERSATION
        messages = run_conversation(
            prompt=final_prompt,
            model=CONFIG["model"],
            messages=messages,
            recursive=recursive,
            temp=temp,
            extra_messages=extra_messages,
        )

        if versions > 1:
            version_folder = os.path.join(version_dir, f"v{version}")
            filesystem.copytree(codedir(), version_folder)
            filesystem.rmtree(codedir())
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
            next_up = ask_input(f"\nIf you want to continue, please input version number to continue from (1-{versions}) (or 'exit' to quit): ")

            if str(next_up) in ["exit", "quit", "e", "q"]:
                sys.exit(0)
            print()

        next_version = int(next_up)

        # move selected version to code folder and start over
        filesystem.copytree(version_folders[next_version-1], codedir())

        prompt = ask_input("GPT: What would you like to do next?\nYou: ")
        print()
        run_versions(prompt, args, version_messages, temp, next_version)

def print_model_info():
    print("#######################################")
    print("# USING MODEL: " + CONFIG["model"].rjust(22, " ") + " #")
    print("#######################################")
    print()

def override_model(model):
    if "model" in cmd_args.args:
        model = str(cmd_args.args["model"])
        if model in ["gpt-4", "gpt4", "4"]:
            model = "gpt-4-0613"
        elif model in ["gpt-3", "gpt3", "gpt-3.5", "gpt3.5", "3", "3.5"]:
            model = "gpt-3.5-turbo-16k-0613"
        elif model in ["gpt-3-4k", "gpt3-4k", "gpt-3.5-4k", "gpt3.5-4k", "3-4k", "3.5-4k"]:
            model = "gpt-3.5-turbo-0613"
    return model

# OVERRIDE MODEL
CONFIG["model"] = str(override_model(CONFIG["model"]))

# LOAD MESSAGE HISTORY
version_messages = {
    1: load_message_history(cmd_args.args)
}

# GET API KEY
openai.api_key = get_api_key()

# WARN IF THERE IS CODE ALREADY IN THE PROJECT
if "zip" not in cmd_args.args:
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
    prompt = ask_input("GPT: What would you like me to do?\nYou: ")
    print()

# INITIALIZE GIT
if "git" in cmd_args.args:
    git.init()

run_versions(prompt, cmd_args.args, version_messages, temp)
