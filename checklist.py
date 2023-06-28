import json
import copy

the_list = []
active_list = []

def load_checklist(file):
    global the_list

    with open(file) as f:
        the_list = json.load(f)

def activate_checklist():
    global the_list
    global active_list

    active_list = copy.deepcopy(the_list)
