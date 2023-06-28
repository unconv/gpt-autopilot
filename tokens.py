import json
import os

# global token usage
token_usage = {
    "input": 0.0,
    "output": 0.0,
    "total": 0.0,
}

# global prev token usage
prev_tokens_total = 0
prev_price_total = 0

def get_token_price(model, direction):
    if model == "gpt-4-0613":
        token_price_input = 0.03 / 1000
        token_price_output = 0.06 / 1000
    elif model == "gpt-4-32k-0613":
        token_price_input = 0.06 / 1000
        token_price_output = 0.12 / 1000
    elif model == "gpt-3.5-turbo-0613":
        token_price_input = 0.0015 / 1000
        token_price_output = 0.002 / 1000
    elif model == "gpt-3.5-turbo-16k-0613":
        token_price_input = 0.003 / 1000
        token_price_output = 0.004 / 1000
    else:
        token_price_input = 0.0
        token_price_output = 0.0

    if direction == "input":
        return token_price_input
    else:
        return token_price_output

def add(response, model):
    global token_usage

    # get token counts
    prompt_tokens = response["usage"]["prompt_tokens"]
    completion_tokens = response["usage"]["completion_tokens"]
    total_tokens = response["usage"]["total_tokens"]

    # increment session token usage
    token_usage["input"] += prompt_tokens
    token_usage["output"] += completion_tokens
    token_usage["total"] += total_tokens

    # load total token usage
    if os.path.exists("token_usage.json"):
        with open("token_usage.json") as f:
            total_token_usage = json.load(f)
    else:
        total_token_usage = {
            "input": 0.0,
            "output": 0.0,
            "total": 0.0,
            "price": 0.0,
        }

    # increment total token usage
    total_token_usage["input"] += prompt_tokens
    total_token_usage["output"] += completion_tokens
    total_token_usage["total"] += total_tokens
    total_token_usage["price"] += get_token_cost(model, prompt_tokens, completion_tokens)

    # save total token usage
    with open("token_usage.json", "w") as f:
        f.write(json.dumps(total_token_usage, indent=4))

def get_token_cost(model, input_tokens=None, output_tokens=None):
    global token_usage

    if input_tokens is None:
        input_tokens = int(token_usage["input"])

    if output_tokens is None:
        output_tokens = int(token_usage["output"])

    input_price = get_token_price(
        model=model,
        direction="input",
    )

    output_price = get_token_price(
        model=model,
        direction="output",
    )

    return input_tokens * input_price + output_tokens * output_price
