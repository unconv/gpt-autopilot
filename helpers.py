# Helper functions

def yesno(prompt, answers):
    answer = ""
    while answer not in answers:
        slash_list = '/'.join(answers)
        answer = input(f"{prompt} ({slash_list}): ")
        if answer not in answers:
            or_list = "' or '".join(answers)
            print(f"Please type '{or_list}'")
    return answer
