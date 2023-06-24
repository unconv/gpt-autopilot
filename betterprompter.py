import openai

import tokens

def make_better(prompt, model, temp = 1.0):
    if len(prompt.split(" ")) < 80:
        words = "an 80 word"
    else:
        words = "a more"

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

    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temp,
        request_timeout=60,
    )

    tokens.add(response)

    return response["choices"][0]["message"]["content"]
