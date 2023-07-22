import sys
import os

from modules import config

args = {
    "program_name": sys.argv.pop(0)
}

VERSION = "0.4.1"

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
    "--simple": {
        "desc": "run in simple mode",
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
    "--git": {
        "desc": "initialize git in the project folder and commit every task",
    },
    "--default-branch": {
        "desc": "set the default git branch name to use",
    },
    "--no-commit-msg": {
        "desc": "don't create a commit message with GPT",
    },
    "--zip": {
        "desc": "create a zip file instead of writing to files directly",
    },
    "--no-cmd": {
        "desc": "don't allow terminal commands to be run",
    },
    "--allow-cmd": {
        "desc": "allow these exact terminal commands to be run automatically",
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
    "--no-outline": {
        "desc": "don't create an outline of the project in the beginning",
    },
    "--use-outline": {
        "desc": "use automatically created outline",
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
    "--step-by-step": {
        "desc": "send the task list to ChatGPT as separate messages",
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
    "--loop-limit": {
        "desc": "ask for confirmation after this many autonomous function calls (default 10)",
    },
    "--context-window": {
        "desc": "end script after this amount of money is used",
    },
    "--token-buffer": {
        "desc": "how much buffer to keep for new responses in context window (default 1500)",
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
    "--token-saver-level": {
        "desc": "set level for the token saver (lower number saves more, default 3)",
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

    while argv != []:
        arg_name = argv.pop(0)

        # conversation id
        if arg_name == "--conv":
            if argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["conv"] = argv.pop(0) # type: ignore
        # initial prompt
        elif arg_name == "--prompt":
            if argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["prompt"] = argv.pop(0) # type: ignore
        # initial prompt from a file
        elif arg_name == "--prompt-file":
            if argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            with open(argv.pop(0)) as f:
                args["prompt"] = f.read() # type: ignore
        # automatically run this command if ChatGPT requests it
        elif arg_name == "--allow-cmd":
            if argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            allowed_cmd.append(argv.pop(0))
        # set the project directory
        elif arg_name == "--dir":
            if argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["dir"] = argv.pop(0) # type: ignore
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
            if argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["temp"] = float(argv.pop(0)) # type: ignore
        # maximum amount of tokens to use
        elif arg_name == "--max-tokens":
            if argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["max-tokens"] = int(argv.pop(0)) # type: ignore
        # maximum amount of money to use
        elif arg_name == "--max-price":
            if argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["max-price"] = float(argv.pop(0)) # type: ignore
        # ask for confirmation after this many autonomous function calls
        elif arg_name == "--loop-limit":
            if argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["loop-limit"] = int(argv.pop(0)) # type: ignore
        # set a custom context window size, in tokens
        elif arg_name == "--context-window":
            if argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["context-window"] = int(argv.pop(0)) # type: ignore
        # how much buffer to keep for new responses in context window
        elif arg_name == "--token-buffer":
            if argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["token-buffer"] = int(argv.pop(0)) # type: ignore
        # system message slug
        elif arg_name == "--system":
            if argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["system"] = argv.pop(0) # type: ignore
        # use automatically detected system message without confirmation
        elif arg_name == "--use-system":
            args["use-system"] = True # type: ignore
        # make prompt better with GPT
        elif arg_name == "--better":
            if "versions" in args:
                print("ERROR: --versions must come after --better")
                sys.exit(1)
            args["better"] = True # type: ignore
        # create a zip file instead of writing to files directly
        elif arg_name == "--zip":
            args["zip"] = True # type: ignore
            args["no-cmd"] = True # type: ignore

            if "git" in args:
                print("ERROR: --git is not compatible with --zip")
                sys.exit(1)

            if len(argv) > 0:
                maybe_zip_name = argv.pop(0)
                if maybe_zip_name[0] != "-":
                    if os.sep in maybe_zip_name:
                        args["zip-dir"] = os.path.dirname(maybe_zip_name)
                    args["zip-name"] = os.path.basename(maybe_zip_name)
                else:
                    argv.insert(0, maybe_zip_name)
        # don't allow terminal commands
        elif arg_name == "--no-cmd":
            args["no-cmd"] = True # type: ignore
        # don't create an outline in the beginning
        elif arg_name == "--no-outline":
            args["no-outline"] = True # type: ignore
        # initialize git and commit every task
        elif arg_name == "--git":
            args["git"] = True # type: ignore

            if "zip" in args:
                print("ERROR: --git is not compatible with --zip")
                sys.exit(1)
        # set default git branch name
        elif arg_name == "--default-branch":
            if argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["default-branch"] = argv.pop(0) # type: ignore
        # don't create a commit message with GPT
        elif arg_name == "--no-commit-msg":
            args["no-commit-msg"] = True # type: ignore
        # use automatically created outline
        elif arg_name == "--use-outline":
            args["use-outline"] = True # type: ignore
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
        # send the tasklist to chatgpt as separate messages
        elif arg_name == "--step-by-step":
            args["step-by-step"] = True # type: ignore
        # run only one task and end the script
        elif arg_name == "--one-task":
            args["one-task"] = True # type: ignore
        # run through checklist items automatically
        elif arg_name == "--do-checklist":
            args["do-checklist"] = True # type: ignore
        # don't use checklist from custom system message
        elif arg_name == "--no-checklist":
            args["no-checklist"] = True # type: ignore
        # initial prompt
        elif arg_name == "--token-saver-level":
            if argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["token-saver-level"] = int(argv.pop(0)) # type: ignore

            if args["token-saver-level"] < 1:
                print("ERROR: Token saver level must be 1 on higher")
                sys.exit(1)
        # run in simple mode
        elif arg_name == "--simple":
            args["use-system"] = True # type: ignore
            args["no-checklist"] = True # type: ignore
            args["no-questions"] = True # type: ignore
            args["no-outline"] = True # type: ignore
            args["no-tasklist"] = True # type: ignore
            args["not-better"] = True # type: ignore
        # continue automatically if ChatGPT doesn't respond with a function call
        elif arg_name == "--continue":
            args["continue"] = True # type: ignore
        # create project directory automatically if it doesn't exist
        elif arg_name == "--create-dir":
            args["create-dir"] = True # type: ignore
        # how manu clarifying questions to ask in the beginning
        elif arg_name == "--questions":
            if argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["questions"] = int(argv.pop(0)) # type: ignore
        # don't ask clarifying questions
        elif arg_name == "--no-questions":
            args["no-questions"] = True # type: ignore
        # delete code folder contents before starting
        elif arg_name == "--delete":
            args["delete"] = True # type: ignore
        # which model to use for ChatGPT API
        elif arg_name == "--model":
            if argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["model"] = str(argv.pop(0)) # type: ignore
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
            if argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["versions"] = int(argv.pop(0)) # type: ignore
        else:
            print(f"ERROR: Invalid option '{arg_name}'")
            sys.exit(1)

    if "not-better" in args and "better" in args:
        print("ERROR: --not-better is not compatible with --better")
        sys.exit(1)

    return args

def get_default_args():
    default_args = []
    config_data= config.get_config()
    if "args" in config_data:
        args = config_data["args"]
        if isinstance(args, str):
            args = args.split(" ")

        for arg in args:
            if isinstance(arg, list):
                default_args += arg
            else:
                arglist = arg.split(" ")
                default_args += arglist
    return default_args

parse_arguments(
    get_default_args() + sys.argv
)
