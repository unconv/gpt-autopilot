#!/usr/bin/env python3

import openai
import json
import time
import os

# SETTINGS
DEBUG = False

# GET API KEY
with open(f".api_key", "r") as f:
    openai.api_key = f.read()

# CREATE CODE DIRECTORY
if not os.path.exists( "code/" ):
    os.mkdir( "code" )

# FUNCTIONS FOR CHATGPT
def write_file(filename, content):
    print(f"FUNCTION: Writing to file code/{filename}...")
    if DEBUG: print(f"\n {content}")

    # force newline in the end
    if content[-1] != "\n":
        content = content + "\n"

    with open(f"code/{filename}", "w") as f:
        f.write(content)
    return f"File {filename} written successfully"

def append_file(filename, content):
    print(f"FUNCTION: Appending to file code/{filename}...")
    if DEBUG: print(f"\n {content}")
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

def delete_file(filename):
    print(f"FUNCTION: Deleting file code/{filename}")
    if not os.path.exists(f"code/{filename}"):
        print(f"File {filename} does not exist")
        return f"ERROR: File {filename} does not exist"
    os.remove(f"code/{filename}")
    return f"File {filename} successfully deleted"

def list_files(list):
    files = os.listdir("code/")
    print(f"FUNCTION: Files in code/ directory:\n{files}")
    return f"List of files in the project:\n{files}"

def ask_clarification(question):
    answer = input(f"## ChatGPT Asks a Question ##\n```{question}```\nAnswer: ")
    return answer

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
            "description": "Write content to a file with given name. Existing files will be overwritten",
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
        }
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
            "content": "You are an AI bot that can do anything by writing and reading files form the computer. You have been given specific functions that you can run. Only use those functions, and do not respond with a message directly. The user will describe their project to you and you will help them build it. Build the project step by step by calling the provided functions. If you need any clarification, use the ask_clarification function."
        })

    # add list of current files to user prompt
    prompt += "\n\nCurrent project files:\n" + "\n".join(os.listdir("code/"))

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
                next_message = input("Do you want to ask something else?\nAnswer (y/n): ")
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
