import json

def get_config():
    try:
        with open("config.json") as f:
            config = json.load(f)
    except:
        config = {
            "model": "gpt-4-0613",
        }
    return config

def save_config(config):
    with open("config.json", "w") as f:
        f.write(json.dumps(config, indent=4))
