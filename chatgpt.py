import openai
import time

import gpt_functions

# ChatGPT API Function

def send_message(
    message,
    messages,
    model = "gpt-3.5-turbo-0613",
    function_call = "auto",
    retries = 0,
    print_message = True,
):
    print("Waiting for ChatGPT...")

    # add user message to message list
    messages.append(message)

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
    except openai.error.PermissionError:
        raise
    except:
        if retries >= 5:
            raise

        # if request fails, wait 5 seconds and try again
        print("ERROR in OpenAI request... Trying again")
        time.sleep(5)

        return send_message(message, messages, model, function_call, retries + 1)

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
