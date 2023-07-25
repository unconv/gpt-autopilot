import subprocess
import atexit
import select

from modules import cmd_args
from modules import tokens
from modules import paths

puppeteer_gpt = None
model = "gpt-4"

def close_browser():
    global puppeteer_gpt
    if puppeteer_gpt and puppeteer_gpt.poll() is None:
        puppeteer_gpt.terminate()
        try:
            puppeteer_gpt.wait(timeout=1)
        except:
            pass

def browse_internet(objective):
    global puppeteer_gpt

    cost_before = tokens.get_token_cost(model)

    if puppeteer_gpt is None:
        if "headless" in cmd_args.args:
            headless = cmd_args.args["headless"]
        else:
            headless = True

        puppeteer_gpt = subprocess.Popen(
            [
                "node", paths.relative("puppeteer-gpt", "index.js"),
                "--model", model,
                "--headless", str(headless).lower(),
                "--autopilot",
            ],
            text=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        atexit.register(close_browser)
    else:
        puppeteer_gpt.stdin.write(objective + "\n")
        puppeteer_gpt.stdin.flush()

    while True:
        if puppeteer_gpt.poll() is not None:
            break

        ready_to_read, _, _ = select.select([puppeteer_gpt.stdout], [], [], 5)
        if ready_to_read:
            for line in puppeteer_gpt.stdout:
                line = line.strip()
                if line == "<!_PROMPT_!>":
                    puppeteer_gpt.stdin.write(objective + "\n")
                    puppeteer_gpt.stdin.flush()
                    break
                elif line.startswith("<!_TASK_!>"):
                    print("GPT: " + line.removeprefix("<!_TASK_!>"))
                elif line.startswith("<!_RESPONSE_!>"):
                    cost_after = tokens.get_token_cost(model)
                    browsing_cost = cost_after - cost_before
                    print(f"GPT: Browsing cost: {round(browsing_cost, 2)} USD")
                    return line.removeprefix("<!_RESPONSE_!>")
                elif line.startswith("<!_TOKENS_!>"):
                    token_count = line.removeprefix("<!_TOKENS_!>").split(" ")
                    tokens.add({
                        "usage": {
                            "prompt_tokens": int(token_count[0]),
                            "completion_tokens": int(token_count[1]),
                            "total_tokens": int(token_count[2]),
                        }
                    }, model)

    return "Unable to browse the internet"
