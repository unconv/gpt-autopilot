import json
import os

from modules import paths

def get_config():
    try:
        with open(paths.relative("config.json")) as f:
            config = json.load(f)
    except:
        config = {
            "model": "gpt-3.5-turbo-16k-0613",
        }
    return config

def save_config(config):
    with open(paths.relative("config.json"), "w") as f:
        f.write(json.dumps(config, indent=4))
