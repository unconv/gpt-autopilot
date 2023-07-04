import os

BASE_PATH = os.path.realpath(os.path.join(__file__, "..", ".."))

def relative(*parts):
    return os.path.join(BASE_PATH, *parts)
