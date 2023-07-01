#!/usr/bin/env python3

import subprocess
import sys
import os

BASE_PATH = os.path.dirname(__file__)

tests = []

for test in os.scandir(BASE_PATH):
    if os.path.isdir(test):
        test_name = os.path.basename(test)

        if test_name == "results":
            continue

        if len(sys.argv) > 1 and sys.argv[1] != test_name:
            continue

        prompt_file = os.path.join(test, "prompt.txt")
        command = os.path.join(BASE_PATH, "..", "gpt-autopilot.py")
        command += " --prompt-file " + prompt_file
        command += " --create-dir"
        command += " --dir " + os.path.join(BASE_PATH, "results", test_name)
        command += " --delete"
        command += " --not-better"
        command += " --use-system"
        command += " --no-questions"
        command += " --use-tasklist"
        command += " --one-task"
        command += " --continue"
        command += " --max-price 2"

        flag_file = os.path.join(test, "flags.txt")
        if os.path.exists(flag_file):
            with open(flag_file) as f:
                command += " " + f.read().strip()

        print("---- RUNNING TEST: " + test_name + " ----\n")

        subprocess.run(command, shell=True)

        print()

