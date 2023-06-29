import sys
import os

args = {
    "program_name": sys.argv.pop(0)
}

VERSION = "0.2.0"

help_info = {
    "--prompt": {
        "desc": "initial prompt for GPT-AutoPilot",
    },
    "--prompt-file": {
        "desc": "read initial prompt from a file",
    },
    "--dir": {
        "desc": "set the project directory",
    },
    "--create-dir": {
        "desc": "create the project directory automatically if it doesn't exist",
    },
    "--system": {
        "desc": "set system message slug to use",
    },
    "--conv": {
        "desc": "conversation id to continue from (e.g. 0123)",
    },
    "--delete": {
        "desc": "delete existing files in code folder before beginning",
    },
    "--versions": {
        "desc": "make multiple versions of the same project from a single prompt",
    },
    "--better": {
        "desc": "make prompt automatically better with ChatGPT",
    },
    "--ask-better": {
        "desc": "ask confirmation before using automatically bettered prompt (to be used with --better)",
    },
    "--not-better": {
        "desc": "don't make prompt automatically better with ChatGPT",
    },
    "--use-system": {
        "desc": "use automatically detected system message without confirmation",
    },
    "--better-versions": {
        "desc": "make a better prompt for every version",
    },
    "--model": {
        "desc": "model for ChatGPT API",
    },
    "--temp": {
        "desc": "temperature for ChatGPT API",
    },
    "--use-tasklist": {
        "desc": "use the first generated task list automatically",
    },
    "--no-tasklist": {
        "desc": "don't create a task list",
    },
    "--single-tasklist": {
        "desc": "send the task list to ChatGPT in a single message",
    },
    "--one-task": {
        "desc": "end script after 'task is finished' summary",
    },
    "--max-tokens": {
        "desc": "end script after this amount tokens are used",
    },
    "--max-price": {
        "desc": "end script after this amount of money is used",
    },
    "--do-checklist": {
        "desc": "run through checklist items automatically",
    },
    "--no-checklist": {
        "desc": "don't use checklist from custom system message",
    },
    "--questions": {
        "desc": "change number of clarifying questions to ask in the beginning",
    },
    "--no-questions": {
        "desc": "don't ask clarifying questions in the beginning",
    },
    "--continue": {
        "desc": "continue automatically if ChatGPT responds without a function call",
    },
}

allowed_cmd = []

def print_help():
    global help_info

    print(f"GPT-AutoPilot v{VERSION} by Unconventional Coding\n")
    print("Command line arguments:")

    for cmd in help_info:
        desc = help_info[cmd]["desc"]
        print("  " + cmd.ljust(21, " ") + desc)

    print()

def parse_arguments(argv):
    global args
    global allowed_cmd

    while sys.argv != []:
        arg_name = sys.argv.pop(0)

        # conversation id
        if arg_name == "--conv":
            if sys.argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["conv"] = sys.argv.pop(0) # type: ignore
        # initial prompt
        elif arg_name == "--prompt":
            if sys.argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["prompt"] = sys.argv.pop(0) # type: ignore
        # initial prompt from a file
        elif arg_name == "--prompt-file":
            if sys.argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            with open(sys.argv.pop(0)) as f:
                args["prompt"] = f.read() # type: ignore
        # automatically run this command if ChatGPT requests it
        elif arg_name == "--allow-cmd":
            if sys.argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            allowed_cmd.append(sys.argv.pop(0))
        # set the project directory
        elif arg_name == "--dir":
            if sys.argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["dir"] = sys.argv.pop(0) # type: ignore
            project_dir = args["dir"]
            if "versions" in args:
                print("ERROR: --dir is not compatible with --versions")
                sys.exit(1)
            if not os.path.exists(project_dir):
                if "create-dir" in args:
                    print(f"Creating project directory '{project_dir}'", end="")
                    answer = "y"
                else:
                    print(f"Project directory '{project_dir}' doesn't exist")
                    answer = input("Do you want to create it? (y/n) ")
                if answer == "y":
                    os.makedirs(project_dir)
                    print()
                else:
                    sys.exit(1)
            if not os.path.isdir(project_dir):
                print(f"ERROR: Project directory '{project_dir}' is not a directory")
                sys.exit(1)
        # temperature
        elif arg_name == "--temp":
            if sys.argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["temp"] = float(sys.argv.pop(0)) # type: ignore
        # maximum amount of tokens to use
        elif arg_name == "--max-tokens":
            if sys.argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["max-tokens"] = int(sys.argv.pop(0)) # type: ignore
        # maximum amount of money to use
        elif arg_name == "--max-price":
            if sys.argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["max-price"] = float(sys.argv.pop(0)) # type: ignore
        # system message slug
        elif arg_name == "--system":
            if sys.argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["system"] = sys.argv.pop(0) # type: ignore
        # use automatically detected system message without confirmation
        elif arg_name == "--use-system":
            args["use-system"] = True # type: ignore
        # make prompt better with GPT
        elif arg_name == "--better":
            if "versions" in args:
                print("ERROR: --versions must come after --better")
                sys.exit(1)
            args["better"] = True # type: ignore
        # don't make prompt better with GPT
        elif arg_name == "--not-better":
            args["not-better"] = True # type: ignore
        # confirm if user wants to use bettered prompt
        elif arg_name == "--ask-better":
            args["ask-better"] = True # type: ignore
        # make a new better prompt for every version
        elif arg_name == "--better-versions":
            args["better-versions"] = True # type: ignore
            args["better"] = True # type: ignore
        # use first task list automatically
        elif arg_name == "--use-tasklist":
            args["use-tasklist"] = True # type: ignore
        # don't create a task list
        elif arg_name == "--no-tasklist":
            args["no-tasklist"] = True # type: ignore
        # send the whole tasklist to chatgpt at once
        elif arg_name == "--single-tasklist":
            args["single-tasklist"] = True # type: ignore
        # run only one task and end the script
        elif arg_name == "--one-task":
            args["one-task"] = True # type: ignore
        # run through checklist items automatically
        elif arg_name == "--do-checklist":
            args["do-checklist"] = True # type: ignore
        # don't use checklist from custom system message
        elif arg_name == "--no-checklist":
            args["no-checklist"] = True # type: ignore
        # continue automatically if ChatGPT doesn't respond with a function call
        elif arg_name == "--continue":
            args["continue"] = True # type: ignore
        # create project directory automatically if it doesn't exist
        elif arg_name == "--create-dir":
            args["create-dir"] = True # type: ignore
        # how manu clarifying questions to ask in the beginning
        elif arg_name == "--questions":
            if sys.argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["questions"] = int(sys.argv.pop(0)) # type: ignore
        # don't ask clarifying questions
        elif arg_name == "--no-questions":
            args["no-questions"] = True # type: ignore
        # delete code folder contents before starting
        elif arg_name == "--delete":
            args["delete"] = True # type: ignore
        # which model to use for ChatGPT API
        elif arg_name == "--model":
            if sys.argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["model"] = str(sys.argv.pop(0)) # type: ignore
        elif arg_name in ["--version", "-v"]:
            print(f"GPT-AutoPilot v{VERSION} by Unconventional Coding")
            sys.exit(69)
        elif arg_name in ["--help", "-h", "/?", "/help", "help"]:
            print_help()
            sys.exit(0)
        # make multiple versions of project
        elif arg_name == "--versions":
            if "dir" in args:
                print("ERROR: --dir is not compatible with --versions")
                sys.exit(1)
            if "ask-better" in args:
                print(f"ERROR: --ask-better flag is not compatible with --versions flag")
                sys.exit(1)
            if sys.argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["versions"] = int(sys.argv.pop(0)) # type: ignore
        else:
            print(f"ERROR: Invalid option '{arg_name}'")
            sys.exit(1)

    if "not-better" in args and "better" in args:
        print("ERROR: --not-better is not compatible with --better")
        sys.exit(1)

    return args

parse_arguments(sys.argv)
