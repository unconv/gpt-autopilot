import openai
import json
import sys
import os

from modules.helpers import yesno, ask_input
from modules import checklist
from modules import cmd_args
from modules import tokens
from modules import paths

def detect_slug(prompt, model, temp):
    slugs = {}

    for filename in os.scandir(paths.relative("prompts")):
        if os.path.isdir(filename):
            description_file = os.path.join(filename, "description")
            if os.path.isfile(description_file):
                with open(description_file) as f:
                    description = f.read()
            else:
                description = ""

            slugs[os.path.basename(filename)] = description

    slugs["ambiguous"] = "For projects whose type can not be accurately detected based on the given prompt"

    messages = [
        {
            "role": "system",
            "content": f"""
You are an AI bot that can autonomously create projects from the users's description.
You have available to you some instructions for different kinds of projects.
You will search through the instructions and respond with the slug of an
instruction that fits the users's description. If the proper instruction
can not be determined accurately from the user's prompt, return "default"

List of instruction slugs and their descriptions:\n
{json.dumps(slugs, indent=4)}
"""
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    print("GPT-API:  Detecting system message...")

    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temp,
        request_timeout=10,
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
                        "certainty": {
                            "type": "number",
                            "description": "The certainty (0-100) that this prompt belongs to this category"
                        }
                    },
                    "required": ["slug", "certainty"],
                }
            }
        ]
    )

    tokens.add(response, model)

    slug = json.loads(response["choices"][0]["message"]["function_call"]["arguments"]) # type: ignore
    certainty = slug["certainty"]
    slug = slug["slug"]

    if certainty < 90:
        slug = "default"

    if slug == "ambiguous":
        slug = "default"

    if slug not in slugs:
        print(f"ERROR:    GPT detected system message '{slug}' that doesn't exist")
        slug = "default"
    elif "use-system" not in cmd_args.args:
        if yesno(f"\nDetected project type '{slug}'.\nDo you want to use this system message?\nYou") == "n":
            slug = ask_input("\nGPT: Which system message do you want to use?\nYou [default]: ") or "default"
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
    elif "use-system" in cmd_args.args:
        slug = None
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
