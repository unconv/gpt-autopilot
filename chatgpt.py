import openai
import time
import json
import sys
import os
import copy

from helpers import yesno
import tokens
import gpt_functions
import checklist
import cmd_args

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

# ChatGPT API Function

def send_message(
    message,
    messages,
    model = "gpt-4-0613",
    function_call = "auto",
    retries = 0,
    print_message = True,
    conv_id = None,
    temp = 0.6,
):
    print("GPT-API:  Waiting... ", end="", flush=True)

    # add user message to message list
    messages.append(message)

    # redact old messages when encountering partial output
    if "No END_OF_FILE_CONTENT" in message["content"]:
        print("\nNOTICE:   Partial output detected, redacting messages...")
        messages[-2]["content"] = "<file content redacted>"
        messages = redact_messages(messages)

    # save message history
    if conv_id is not None:
        history_file = os.path.join("history", f"{conv_id}.json")
        with open(history_file, "w") as f:
            f.write(json.dumps(messages, indent=4))

    definitions = copy.deepcopy(gpt_functions.get_definitions(model))

    if gpt_functions.tasklist != [] or checklist.active_list != []:
        remove_funcs = [
            "make_tasklist", # don't take any more task lists if there is one already
            "project_finished" # don't allow project_finished function when task list is unfinished
        ]

        definitions = [definition for definition in definitions if definition["name"] not in remove_funcs]
    else:
        # remove task_finished function if there is no task currently
        definitions = [definition for definition in definitions if definition["name"] != "task_finished"]

    # always ask clarifying questions first
    if "questions" in cmd_args.args:
        initial_question_count = cmd_args.args["questions"]
    else:
        initial_question_count = 5

    if "no-questions" not in cmd_args.args and gpt_functions.clarification_asked < initial_question_count:
        definitions = [gpt_functions.ask_clarification_func]
        function_call = {
            "name": "ask_clarification",
            "arguments": "questions"
        }

    # always ask for a task list first
    elif "no-tasklist" not in cmd_args.args and gpt_functions.tasklist_finished:
        definitions = [gpt_functions.make_tasklist_func]
        function_call = {
            "name": "make_tasklist",
            "arguments": "tasks"
        }

    try:
        # send prompt to chatgpt
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            functions=definitions,
            function_call=function_call,
            temperature=temp,
            request_timeout=60,
        )

        tokens.add(response, model)
        request_tokens = response["usage"]["total_tokens"]
        total_tokens = int(tokens.token_usage["total"])
        token_cost = round(tokens.get_token_cost(model), 2)
        print(f"OK! (+{request_tokens} tokens, total {total_tokens} / {token_cost} USD)")
    except openai.error.AuthenticationError:
        print("\nAuthenticationError: Check your API-key")
        sys.exit(1)
    except openai.InvalidRequestError as e:
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
            function_call=function_call,
            conv_id=conv_id,
            print_message=print_message,
            temp=temp,
        )
    except openai.error.PermissionError:
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

        return send_message(
            message=message,
            messages=messages,
            model=model,
            function_call=function_call,
            retries=retries+1,
            conv_id=conv_id,
            print_message=print_message,
            temp=temp,
        )

    # redact long responses that don't need to be in history
    messages = redact_always(messages)

    # add response to message list
    messages.append(response["choices"][0]["message"])

    # get message content
    response_message = response["choices"][0]["message"]["content"]

    # if response includes content, print it out
    if print_message and response_message != None:
        print("\n## ChatGPT Responded ##\n```\n")
        print(response_message)
        print("\n```\n")

    return messages
