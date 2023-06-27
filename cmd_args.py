import sys

from helpers import reset_code_folder

args = {
    "program_name": sys.argv.pop(0)
}

def parse_arguments(argv):
    global args

    while sys.argv != []:
        arg_name = sys.argv.pop(0)

        # conversation id
        if arg_name == "--conv":
            if sys.argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["conv"] = sys.argv.pop(0)
        # initial prompt
        elif arg_name == "--prompt":
            if sys.argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["prompt"] = sys.argv.pop(0)
        # temperature
        elif arg_name == "--temp":
            if sys.argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["temp"] = float(sys.argv.pop(0))
        # make prompt better with GPT
        elif arg_name == "--better":
            if "versions" in args:
                print("ERROR: --versions must come after --better")
                sys.exit(1)
            args["better"] = True
        # don't make prompt better with GPT
        elif arg_name == "--not-better":
            args["not-better"] = True
        # confirm if user wants to use bettered prompt
        elif arg_name == "--ask-better":
            args["ask-better"] = True
        # make a new better prompt for every version
        elif arg_name == "--better-versions":
            args["better-versions"] = True
            args["better"] = True
        # use first task list automatically
        elif arg_name == "--use-tasklist":
            args["use-tasklist"] = True
        # don't create a task list
        elif arg_name == "--no-tasklist":
            args["no-tasklist"] = True
        # how manu clarifying questions to ask in the beginning
        elif arg_name == "--questions":
            if sys.argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["questions"] = int(sys.argv.pop(0))
        # don't ask clarifying questions
        elif arg_name == "--no-questions":
            args["no-questions"] = True
        # delete code folder contents before starting
        elif arg_name == "--delete":
            reset_code_folder()
        elif arg_name in ["--version", "-v"]:
            print(f"GPT-AutoPilot v{VERSION} by Unconventional Coding")
            sys.exit(69)
        # make multiple versions of project
        elif arg_name == "--versions":
            if "ask-better" in args:
                print(f"ERROR: --ask-better flag is not compatible with --versions flag")
                sys.exit(1)
            if sys.argv == []:
                print(f"ERROR: Missing argument for '{arg_name}'")
                sys.exit(1)
            args["versions"] = int(sys.argv.pop(0))
        else:
            print(f"ERROR: Invalid option '{arg_name}'")
            sys.exit(1)

    if "not-better" in args and "better" in args:
        print("ERROR: --not-better is not compatible with --better")
        sys.exit(1)

    return args

parse_arguments(sys.argv)
