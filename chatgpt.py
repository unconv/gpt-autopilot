import openai
import time
import json
import sys
import copy

import gpt_functions

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
):
    print("Waiting for ChatGPT...")

    # add user message to message list
    messages.append(message)

    # redact old messages when encountering partial output
    if "No END_OF_OUTPUT" in message["content"]:
        print("## NOTICE: Partial output detected, dropping messages... ##")
        messages[-2]["content"] = "<file content redacted>"
        messages = redact_messages(messages)

    # save message history
    if conv_id is not None:
        with open(f"history/{conv_id}.json", "w") as f:
            f.write(json.dumps(messages, indent=4))

    try:
        # send prompt to chatgpt
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            functions=gpt_functions.definitions,
            function_call=function_call,
        )
    except openai.error.AuthenticationError:
        print("AuthenticationError: Check your API-key")
        sys.exit(1)
    except openai.InvalidRequestError as e:
        if "maximum context length" in str(e):
            print("## NOTICE: Context limit reached, dropping old messages... ##")

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
        )
    except openai.error.PermissionError:
        raise
    except:
        if retries >= 4:
            raise

        # if request fails, wait 5 seconds and try again
        print("ERROR in OpenAI request... Trying again")
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
        )

    # add response to message list
    messages.append(response["choices"][0]["message"])

    # get message content
    response_message = response["choices"][0]["message"]["content"]

    # if response includes content, print it out
    if print_message and response_message != None:
        print("## ChatGPT Responded ##\n```\n")
        print(response_message)
        print("\n```\n")

    return messages
