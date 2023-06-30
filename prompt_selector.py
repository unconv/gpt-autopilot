import openai
import tokens
import json
import sys
import os

from helpers import yesno
import checklist
import cmd_args
import paths

def detect_slug(prompt, model, temp):
    slugs = []

    for filename in os.scandir(paths.relative("prompts")):
        if os.path.isdir(filename):
            slugs.append(os.path.basename(filename))

    messages = [
        {
            "role": "user",
            "content": f"""
Categorize the following description onto the below categories. If uncertain, return 'default'
```
{prompt}
```
Note that the same technology might have different applications, such as command line tool or web application.

List of category slugs:\n
{slugs}
"""
        }
    ]

    print("GPT-API:  Detecting system message...")

    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temp,
        request_timeout=60,
        function_call={
            "name": "set_slug",
            "arguments": "slug"
        },
        functions=[
            {
                "name": "set_slug",
                "description": "Set the category slug. Default if uncertain.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "slug": {
                            "type": "string",
                            "description": "The category slug",
                        },
                    },
                    "required": ["slug"],
                }
            }
        ]
    )

    tokens.add(response, model)

    slug = json.loads(response["choices"][0]["message"]["function_call"]["arguments"]) # type: ignore
    slug = slug["slug"]

    if slug not in slugs:
        print(f"ERROR:    GPT detected system message '{slug}' that doesn't exist")
        slug = "default"
    elif "use-system" not in cmd_args.args:
        if yesno(f"\nDetected project type '{slug}'.\nDo you want to use this system message?\nYou") == "n":
            slug = input("\nGPT: Which system message do you want to use?\nYou [default]: ") or "default"
        print()

    return slug

def get_data(prompt, model, temp, slug=None):
    if slug is None:
        try:
            slug = detect_slug(prompt, model, temp)
        except SystemExit:
            raise
        except:
            print("ERROR:    Unable to detect system message")
            slug = "default"
            prompt_data = {
                "slug": slug,
                "system_message": paths.relative("prompts", "default", "system_message")
            }

    data = {
        "slug": slug
    }

    checklist_path = paths.relative("prompts", slug, "checklist.json")
    system_message_path = paths.relative("prompts", slug, "system_message")

    if os.path.exists(checklist_path):
        data["checklist"] = checklist_path

    if os.path.exists(system_message_path):
        data["system_message"] = system_message_path
    else:
        print(f"ERROR:    System message '{slug}' not found")
        sys.exit(1)

    return data

def select_system_message(prompt, model, temp):
    if "system" in cmd_args.args:
        slug = cmd_args.args["system"]
    else:
        if yesno("GPT: Do you want me to automatically detect a custom system message?\nYou") == "y":
            slug = None
        else:
            slug = "default"
        print()

    prompt_data = get_data(prompt, model, temp, slug)

    slug = prompt_data["slug"]
    print(f"SYSTEM:   Using system message '{slug}'")

    if "checklist" in prompt_data:
        print(f"SYSTEM:   Using checklist '{slug}'")
        checklist.load_checklist(prompt_data["checklist"])
        checklist.activate_checklist()
    else:
        print()

    with open(str(prompt_data["system_message"]), "r") as f:
        system_message = f.read()

    return system_message
