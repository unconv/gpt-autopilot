import os

BASE_PATH = os.path.dirname(__file__)

def relative(*parts):
    return os.path.join(BASE_PATH, *parts)
