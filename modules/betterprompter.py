import openai
import json

from modules import tokens

def make_better(prompt, model, temp = 1.0, messages = []):
    if len(prompt.split(" ")) < 80:
        words = "an 80 word"
    else:
        words = "a more"

    if messages == []:
        messages = [
            {
                "role": "system",
                "content": "You are a prompt designer for an AI agent that can read and write files from the filesystem and run commands on the computer. The AI agent is used to create all kinds of projects, including programming and content creaton. Please note that the agent can not run GUI applications or run tests. Only describe the project, not how it should be implemented. The prompt will be given to the AI agent as a description of the project to accomplish."
            },
            {
                "role": "user",
                "content": "Convert this prompt into "+ words +" detailed prompt:\n" + prompt
            }
        ]
    else:
        messages.append({
            "role": "user",
            "content": "Please make the following changes to the prompt: " + prompt + "\n\nRespond with the complete, modified version of the prompt."
        })

    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temp,
        function_call={
            "name": "give_prompt",
            "arguments": "prompt"
        },
        functions=[
            {
                "name": "give_prompt",
                "description": "Give the user the better version of the prompt, in full, including modifications",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Better version of the prompt, in full, including modifications. Can include newlines.",
                        },
                    },
                    "required": ["prompt"],
                }
            }
        ],
        request_timeout=60,
    )

    tokens.add(response, model)

    message = response["choices"][0]["message"] # type: ignore
    messages.append(message)

    args = json.loads(message["function_call"]["arguments"]) # type: ignore

    return (args["prompt"], messages)
