#!/usr/bin/env python3

import openai
import json
import os
import traceback
import sys
import shutil

import gpt_functions
from helpers import yesno
import chatgpt

# Read API key from environment variable or file
def get_openai_api_key():
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if openai.api_key in [None, ""]:
        try:
            with open(".api_key", "r") as f:
                openai.api_key = f.read().strip()
        except:
            print(
                "Put your OpenAI API key into a .api_key file or OPENAI_API_KEY environment variable to skip this prompt.\n"
            )
            openai.api_key = input("Input OpenAI API key: ").strip()

            if openai.api_key == "":
                sys.exit(1)

            save = yesno("Do you want to save this key to .api_key?", ["y", "n"])
            if save == "y":
                with open(".api_key", "w") as f:
                    f.write(openai.api_key)

            print()

# Check code directory and prompt user for action
def handle_code_directory():
    if os.path.exists("code/") and len(os.listdir("code")) != 0:
        answer = yesno(
            "WARNING! There is already some code in the `code/` folder. GPT-AutoPilot may base the project on these files and has write access to them and might modify or delete them.\n\n"
            + gpt_functions.list_files("", False)
            + "\n\nDo you want to continue?",
            ["YES", "NO", "DELETE"],
        )
        if answer == "DELETE":
            shutil.rmtree("code/")
        elif answer != "YES":
            sys.exit(0)

# Create code directory if it does not exist
def create_code_directory():
    if not os.path.exists("code/"):
        os.mkdir("code")

# Run the conversation with prompt and messages
def run_conversation(prompt, messages=[]):
    if messages == []:
        with open("system_message", "r") as f:
            system_message = f.read()

        # add system message
        messages.append({"role": "system", "content": system_message})

        # add list of current files to user prompt
        prompt += "\n\n" + gpt_functions.list_files()

    # add user prompt to chatgpt messages
    messages = chatgpt.send_message({"role": "user", "content": prompt}, messages)

    # get chatgpt response
    message = messages[-1]

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

                function_response = (
                    "Error parsing arguments. Make sure to use properly formatted JSON, with double quotes"
                )

            if arguments is not None:
                # call the function given by chatgpt
                if hasattr(gpt_functions, function_name):
                    function_response = getattr(gpt_functions, function_name)(**arguments)
                else:
                    print(f"NOTICE: GPT called function '{function_name}' that doesn't exist.")
                    function_response = f"Function '{function_name}' does not exist."

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
            messages = chatgpt.send_message(
                {"role": "function", "name": function_name, "content": function_response}, messages
            )
        else:
            # if chatgpt doesn't respond with a function call, ask user for input
            if "?" in message["content"]:
                user_message = input("ChatGPT didn't respond with a function. What do you want to say?\nAnswer: ")
            else:
                # if chatgpt doesn't ask a question, continue
                user_message = "Ok, continue."

            # send user message to chatgpt
            messages = chatgpt.send_message({"role": "user", "content": user_message}, messages)

        # save last response for the while loop
        message = messages[-1]

# ASK FOR PROMPT
prompt = input("What would you like me to do?\nAnswer: ")

# Get OpenAI API key
get_openai_api_key()

# Handle code directory
handle_code_directory()

# Create code directory
create_code_directory()

# RUN CONVERSATION
run_conversation(prompt)

