token_usage = {
    "input": 0.0,
    "output": 0.0,
    "total": 0.0,
}

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

def add(response):
    global token_usage
    token_usage["input"] += response["usage"]["prompt_tokens"]
    token_usage["output"] += response["usage"]["completion_tokens"]
    token_usage["total"] += response["usage"]["total_tokens"]

def get_token_cost(model):
    global token_usage

    input_price = get_token_price(
        model=model,
        direction="input",
    )

    output_price = get_token_price(
        model=model,
        direction="output",
    )

    return token_usage["input"] * input_price + token_usage["output"] * output_price
