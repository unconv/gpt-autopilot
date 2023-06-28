import openai
import tokens
import json
import sys
import os

def get_data(prompt, model, temp):
    slugs = []

    for filename in os.scandir("prompts"):
        if os.path.isdir(filename):
            slugs.append(os.path.basename(filename))

    messages = [
        {
            "role": "user",
            "content": f"""
Select the most fitting category slug for the following prompt (if any):
```
{prompt}
```

Available slugs are:\n
{slugs}
"""
        }
    ]

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
                "description": "Set the most fitting slug for the prompt",
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

    slug = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])
    slug = slug["slug"]

    if slug not in slugs:
        slug = "default"

    data = {
        "slug": slug
    }

    checklist_path = os.path.join("prompts", slug, "checklist.json")
    system_message_path = os.path.join("prompts", slug, "system_message")

    if os.path.exists(checklist_path):
        data["checklist"] = checklist_path

    if os.path.exists(system_message_path):
        data["system_message"] = system_message_path
    else:
        print(f"ERROR:    System message '{slug}' not found")
        sys.exit(1)

    return data
