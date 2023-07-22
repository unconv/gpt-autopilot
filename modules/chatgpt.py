import openai
import copy
import time
import json
import sys
import os

from modules.helpers import yesno, ask_input
from modules.token_saver import save_tokens
from modules import gpt_functions
from modules import checklist
from modules import cmd_args
from modules import helpers
from modules import tokens
from modules import paths

create_outline = False

def redact_always(messages):
    messages_redact = copy.deepcopy(messages)
    for msg in messages_redact:
        if msg["role"] == "user" and "APPEND_OK" in msg["content"]:
            msg["content"] = "File appended succesfully"
            break
    return messages_redact

def redact_messages(messages):
    messages_redact = copy.deepcopy(messages)
    for msg in messages_redact:
        if msg["role"] == "assistant" and msg["content"] not in [None, "<message redacted>"]:
            msg["content"] = "<message redacted>"
            break
        if msg["role"] == "function" and msg["name"] == "read_file" and msg["content"] not in [None, "<file contents redacted>"]:
            msg["content"] = "<file contents redacted>"
            break
    return messages_redact

def filter_messages(messages):
    filtered = []

    for message in messages:
        if message["role"] not in ["git"]:
            filtered.append(message)

    return filtered

def save_message_history(conv_id, messages):
    if conv_id is not None:
        history_file = paths.relative("history", f"{conv_id}.json")
        with open(history_file, "w") as f:
            f.write(json.dumps(messages, indent=4))

# ChatGPT API Function

def send_message(
    message,
    messages,
    model = "gpt-3.5-turbo-16k-0613",
    function_call = "auto",
    retries = 0,
    print_message = True,
    conv_id = None,
    temp = 1.0,
):
    global create_outline

    if "loop-limit" in cmd_args.args:
        autonomous_message_limit = int(cmd_args.args["loop-limit"])
    else:
        autonomous_message_limit = 10

    # prevent function loop of death
    helpers.autonomous_message_count += 1
    if helpers.autonomous_message_count >= autonomous_message_limit:
        if yesno(f"\nWARNING: ChatGPT ran {helpers.autonomous_message_count} calls back to back.\nContinue?", ["YES", "NO"]) == "NO":
            prompt = ask_input("\nGPT: What would you like to do next?\nYou: ")
            print()
            message = {
                "role": "user",
                "content": prompt,
            }
        helpers.autonomous_message_count = 0

    # add user message to message list
    messages.append(message)

    # warn when partial output is detected
    if "No END_OF_FILE_CONTENT" in message["content"]:
        print("NOTICE:   Partial output detected")
        messages[-2]["content"] = "<file content redacted>"

    # determine context window size
    if "context-window" in cmd_args.args:
        token_limit = int(cmd_args.args["context-window"])
    else:
        token_limit = tokens.get_token_limit(model)

    # determine token buffer
    if "token-buffer" in cmd_args.args:
        token_buffer = int(cmd_args.args["token-buffer"])
    else:
        token_buffer = 1500

    # redact messages when context limit is getting full
    if token_limit and tokens.context_size > (token_limit - token_buffer):
        print("NOTICE:   Context limit is near. Redacting messages")
        messages = redact_messages(messages)

    definitions = copy.deepcopy(gpt_functions.get_definitions(model))

    if gpt_functions.active_tasklist != [] or checklist.active_list != []:
        remove_funcs = [
            "make_tasklist", # don't take any more task lists if there is one already
            "project_finished" # don't allow project_finished function when task list is unfinished
        ]

        definitions = [definition for definition in definitions if definition["name"] not in remove_funcs]
    else:
        # remove task_finished function if there is no task currently
        definitions = [definition for definition in definitions if definition["name"] != "task_finished"]

    if gpt_functions.task_operation_performed == False:
        # remove task_finished until an operation is performed
        definitions = [definition for definition in definitions if definition["name"] != "task_finished"]

    # always ask clarifying questions first
    if "no-questions" not in cmd_args.args and gpt_functions.clarification_asked < gpt_functions.initial_question_count:
        definitions = [gpt_functions.ask_clarification_func]
        function_call = {
            "name": "ask_clarification",
            "arguments": "questions"
        }
    elif "no-outline" not in cmd_args.args and not gpt_functions.outline_created:
        print("OUTLINE:  Creating an outline for the project")
        create_outline = True
        definitions = [gpt_functions.ask_clarification_func]
        function_call = "none"
        if not gpt_functions.modify_outline:
            messages.append({
                "role": "user",
                "content": "Please tell me in full detail how you will implement this project. Write it in the first person as if you are the one who will be creating it. Start sentences with 'I will', 'Then I will' and 'Next I will'"
            })
        gpt_functions.outline_created = True

    # always ask for a task list first
    elif "no-tasklist" not in cmd_args.args and gpt_functions.tasklist_finished and gpt_functions.tasklist == []:
        print("TASKLIST: Creating a tasklist...")
        messages.append({
            "role": "user",
            "content": """
Please create a tasklist for the next steps involved in implementing the project. Don't add tasks that have already been done.
Explain the task clearly and comprehensively so that there can be no misunderstandings.
Don't include testing or other operations that require user interaction, unless specifically asked.
For a trivial project, make just one task"""
        })
        definitions = [gpt_functions.make_tasklist_func]
        function_call = {
            "name": "make_tasklist",
            "arguments": "tasks"
        }

    print("GPT-API:  Waiting... ", end="", flush=True)

    # save message history
    save_message_history(conv_id, messages)

    try:
        # send prompt to chatgpt
        response = openai.ChatCompletion.create(
            model=model,
            messages=save_tokens(filter_messages(messages)),
            functions=definitions,
            function_call=function_call,
            temperature=temp,
            request_timeout=120,
        )

        tokens.add(response, model)
        request_tokens = response["usage"]["total_tokens"] # type: ignore
        total_tokens = int(tokens.token_usage["total"])
        token_cost = round(tokens.get_token_cost(model), 2)
        print(f"OK! (+{request_tokens} tokens, total {total_tokens} / {token_cost} USD)")
    except openai.error.AuthenticationError: # type: ignore
        print("\nAuthenticationError: Check your API-key")
        sys.exit(1)
    except openai.InvalidRequestError as e: # type: ignore
        if "maximum context length" in str(e):
            print("\nNOTICE:   Context limit reached, redacting old messages...")

            # remove last message
            messages.pop()

            # redact first unredacted assistant message
            redacted_messages = redact_messages(messages)

            # show error if no message could be redacted
            if redacted_messages == messages:
                raise

            messages = redacted_messages
        else:
            raise

        return send_message(
            message=message,
            messages=messages,
            model=model,
            function_call=function_call, # type: ignore
            conv_id=conv_id,
            print_message=print_message,
            temp=temp,
        )
    except openai.error.PermissionError: # type: ignore
        raise
    except TypeError:
        raise
    except NameError:
        raise
    except Exception as e:
        if retries >= 4:
            raise

        if "You exceeded your current quota" in str(e):
            if yesno("\n\nERROR:    You have exceeded your OpenAI API quota. Would you like to try again?") == "n":
                sys.exit(1)

        # if request fails, wait 5 seconds and try again
        print("\nERROR:    OpenAI request failed... Trying again")
        time.sleep(5)

        # remove last message
        messages.pop()

        # save message history
        save_message_history(conv_id, messages)

        return send_message(
            message=message,
            messages=messages,
            model=model,
            function_call=function_call, # type: ignore
            retries=retries+1,
            conv_id=conv_id,
            print_message=print_message,
            temp=temp,
        )

    # redact long responses that don't need to be in history
    messages = redact_always(messages)

    # add response to message list
    messages.append(response["choices"][0]["message"]) # type: ignore

    # save message history
    save_message_history(conv_id, messages)

    # get message content
    response_message = response["choices"][0]["message"]["content"] # type: ignore

    # if response includes content, print it out
    if print_message and response_message != None:
        print("\n## ChatGPT Responded ##\n```\n")
        print(response_message)
        print("\n```\n")

    return messages
