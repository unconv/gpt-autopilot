import copy

from modules import cmd_args

if "token-saver-level" in cmd_args.args:
    token_saver_level = int(cmd_args.args["token-saver-level"])
else:
    token_saver_level = 3

def save_tokens(messages):
    global token_saver_level

    read_file_history = {}
    write_file_history = {}

    reversed_messages = copy.deepcopy(messages)[::-1]
    for i, message in enumerate(reversed_messages):
        if "function_call" in message and message["function_call"]["name"] == "file_open_for_writing" and i >= 2:
            if message["function_call"]["arguments"] in write_file_history:
                if token_saver_level <= write_file_history[message["function_call"]["arguments"]]:
                    reversed_messages[i-2]["content"] = "START_OF_FILE_CONTENT\n<contents redacted>\nEND_OF_FILE_CONTENT"
                write_file_history[message["function_call"]["arguments"]] += 1
            else:
                write_file_history[message["function_call"]["arguments"]] = 1
        elif "function_call" in message and message["function_call"]["name"] == "read_file":
            if message["function_call"]["arguments"] in read_file_history:
                if token_saver_level <= read_file_history[message["function_call"]["arguments"]]:
                    reversed_messages[i-1]["content"] = "<contents redacted>"
                read_file_history[message["function_call"]["arguments"]] += 1
            else:
                read_file_history[message["function_call"]["arguments"]] = 1

    return reversed_messages[::-1]
