# Helper functions
import sys
import os

def yesno(prompt, answers = ["y", "n"]):
    answer = ""
    while answer not in answers:
        slash_list = '/'.join(answers)
        answer = input(f"{prompt} ({slash_list}): ")
        if answer not in answers:
            or_list = "' or '".join(answers)
            print(f"Please type '{or_list}'")
    return answer

def safepath(path):
    base = os.path.abspath("code/")
    file = os.path.abspath(os.path.join(base, path))

    if os.path.commonpath([base, file]) != base:
        print("ERROR: Tried to access file outside of code/ folder!")
        sys.exit(1)

    return path
