import subprocess
import openai
import json
import copy
import time
import re

from modules.helpers import codedir, reset_code_folder
from modules.platform import join_cmd
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

def safecmd(text):
    return re.sub(r'[^a-zA-Z0-9\. ]', '', text)

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
            request_timeout=10,
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

        message = response["choices"][0]["message"] # type: ignore
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
    result = subprocess.run(join_cmd([
        f"cd {codedir()}",
        f"git config user.{x}",
    ]), shell=True, capture_output=True, text=True)
    current = result.stdout.strip()

    if not current:
        subprocess.run(join_cmd([
            f"cd {codedir()}",
            f"git config user.{x} \"{safecmd(default)}\"",
        ]), shell=True)

def set_defaults():
    set_default_x("email", "gpt@gpt-autopilot.com")
    set_default_x("name", "gpt-autopilot")

def init():
    print("GIT:      ", end="", flush=True)

    if "default-branch" in cmd_args.args:
        default_branch = cmd_args.args["default-branch"]
    else:
        default_branch = "master"

    subprocess.run(join_cmd([
        f"cd {codedir()}",
        f"git -c init.defaultBranch=\"{safecmd(default_branch)}\" init",
    ]), shell=True)
    print()
    set_defaults()

def commit(messages, model, temp):
    global commit_count
    commit_message = get_commit_message(messages, model, temp)
    print()

    # update .gpt-autopilot for empty commits
    with open(codedir(".gpt-autopilot"), "w") as f:
        f.write(str(time.time()))

    try:
        output = subprocess.check_output(join_cmd([
            "cd " + codedir(),
            "git add .",
            "git commit -m \"" + safecmd(commit_message) + "\"",
        ]), shell=True).decode().strip()
        print(output)
    except subprocess.CalledProcessError:
        print("GIT:      Nothing to commit.")
        return None

    if "nothing to commit" in output:
        return None

    commit_count += 1

    return {
        "role": "git",
        "content": commit_message,
    }

def revert(messages):
    global commit_count

    if commit_count > 2:
        subprocess.run(join_cmd([
            "cd " + codedir(),
            "git reset HEAD~1 --hard",
        ]), shell=True)
    else:
        reset_code_folder()
        init()

    # pop last git message
    messages.pop()

    # revert to previous git message
    last_message = messages.pop()
    last_prompt = ""
    while last_message["role"] not in ["git", "system"]:
        if last_message["role"] == "user":
            last_prompt = last_message["content"]
        last_message = messages.pop()
    messages.append(last_message)

    commit_count -= 1

    return (last_prompt, messages)

def own_commit():
    diff = subprocess.check_output(join_cmd([
        "cd " + codedir(),
        "git add .",
        "git diff --staged",
    ]), shell=True).decode().strip()

    subprocess.run(join_cmd([
        "cd " + codedir(),
        "git restore --staged .",
    ]), shell=True)

    if diff == "":
        return False

    return "I have made the following changes to the code myself:\n\n```diff\n" + diff + "\n```\nPlease keep these changes in mind for future edits. Please summarize the changes I have made."

def print_help():
    global commit_count
    if "git" in cmd_args.args and commit_count > 1:
        helptext  = "GIT COMMANDS AVAILABLE:\n"
        helptext += "- revert   revert previous commit\n"
        helptext += "- retry    revert commit and try same prompt again\n"
        helptext += "- commit   commit your own changes and tell ChatGPT\n"

        print(helptext)