# Custom System Prompts

This folder contains specific system messages and checklists for different projects and technologies. GPT-AutoPilot will automatically pick a fitting system message from this folder when it creates a project. This way, projects using specific technologies can be created more reliably.

Each folder in `prompts/` represents a different project type or technology. Each folder includes a `system_message` file and an optional `checklist.json` file. The default system message will be replaced with the specific system message of that project type. If the `checklist.json` file exists, GPT-AutoPilot will run through every step in it every time a task is finished.

# Contributions wanted

Feel free to submit a pull request with a system message and checklist for a technology you know and I will add it to this folder if it works.
