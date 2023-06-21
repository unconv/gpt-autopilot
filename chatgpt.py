import openai
import time
import json

import gpt_functions

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

            # redact first unredacted assistant message
            redacted = False
            for msg in messages:
                if msg["role"] == "assistant" and msg["content"] not in [None, "<message redacted>"]:
                    msg["content"] = "<message redacted>"
                    redacted = True
                    break

            # show error if no message could be redacted
            if redacted == False:
                raise

        return send_message(
            message=message,
            messages=messages,
            model=model,
            function_call=function_call,
            conv_id=conv_id,
        )
    except openai.error.PermissionError:
        raise
    except:
        if retries >= 4:
            raise

        # if request fails, wait 5 seconds and try again
        print("ERROR in OpenAI request... Trying again")
        time.sleep(5)

        return send_message(
            message=message,
            messages=messages,
            model=model,
            function_call=function_call,
            retries=retries+1,
            conv_id=conv_id,
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
