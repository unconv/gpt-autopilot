import subprocess
import openai
import shlex
import json
import copy

from modules.helpers import codedir
from modules import cmd_args
from modules import chatgpt
from modules import tokens

commit_count = 1
git_log = [
    {
        "role": "assistant",
        "content": "",
        "function_call": {
            "name": "set_commit_message",
            "arguments": "{\n \"commit_message\": \"initial commit\"\n}"
        }
    }
]

def get_commit_message(messages, model, temp):
    global git_log
    global commit_count

    commit_message = "commit " + str(commit_count)

    if "no-commit-msg" in cmd_args.args:
        return commit_message

    context = []

    while len(messages) > 0:
        message = messages.pop()
        context.insert(0, message)
        if len(context) > 2 and message["role"] == "user":
            break

    context = copy.deepcopy(git_log) + context

    print("GIT:      Generating commit message... ", end="", flush=True)

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=chatgpt.filter_messages(context),
            temperature=temp,
            request_timeout=20,
            function_call={
                "name": "set_commit_message",
                "arguments": "commit_message"
            },
            functions=[
                {
                    "name": "set_commit_message",
                    "description": "Set the next commit message",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "commit_message": {
                                "type": "string",
                                "description": "A relevant commit message based on the history and latest changes"
                            },
                        },
                        "required": ["commit_message"],
                    }
                }
            ]
        )

        tokens.add(response, model)

        message = response["choices"][0]["message"]
        git_log.append(message)

        answer = json.loads(message["function_call"]["arguments"]) # type: ignore
        commit_message = answer["commit_message"]

        request_tokens = response["usage"]["total_tokens"] # type: ignore
        total_tokens = int(tokens.token_usage["total"])
        token_cost = round(tokens.get_token_cost(model), 2)

        print(f"OK! (+{request_tokens} tokens, total {total_tokens} / {token_cost} USD)")
    except Exception as e:
        print("\nERROR:    Unable to generate commit message: " + str(e))

    return commit_message

def set_default_x(x, default):
    result = subprocess.run(f"cd {shlex.quote(codedir())}; git config user.{x}", shell=True, capture_output=True, text=True)
    current = result.stdout.strip()

    if not current:
        subprocess.run(f'cd {shlex.quote(codedir())}; git config user.{x} {shlex.quote(default)}', shell=True)

def set_defaults():
    set_default_x("email", "gpt@gpt-autopilot.com")
    set_default_x("name", "gpt-autopilot")

def init():
    print("GIT:      ", end="", flush=True)

    if "default-branch" in cmd_args.args:
        default_branch = cmd_args.args["default-branch"]
    else:
        default_branch = "master"

    subprocess.run(f"cd {shlex.quote(codedir())}; git -c init.defaultBranch={shlex.quote(default_branch)} init", shell=True)
    set_defaults()

def commit(messages, model, temp):
    global commit_count
    commit_message = get_commit_message(messages, model, temp)
    print()
    subprocess.run("cd " + shlex.quote(codedir()) + "; git add .; git commit -m " + shlex.quote(commit_message), shell=True)
    commit_count += 1

    return {
        "role": "git",
        "content": commit_message,
    }

def revert(messages):
    global commit_count
    subprocess.run("cd " + shlex.quote(codedir()) + "; git reset HEAD~1 --hard", shell=True)
    messages.pop() # pop last git message

    # revert to previous git message
    last_message = messages.pop()
    while last_message["role"] not in ["git", "system"]:
        last_message = messages.pop()
    messages.append(last_message)

    commit_count -= 1

    return messages

def revert_text():
    global commit_count
    if "git" in cmd_args.args and commit_count > 2:
        return " (type 'revert' to revert previous commit)"
    else:
        return ""