import sys

def join_cmd(cmd_list):
    if sys.platform.startswith('win'):
        joiner = " & "
    else:
        joiner = "; "

    return joiner.join(cmd_list)
