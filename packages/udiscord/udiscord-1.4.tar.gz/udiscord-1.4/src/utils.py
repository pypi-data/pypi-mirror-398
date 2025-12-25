from json import dump, load
from os import path
from config import auth_file
from . import log



def load_auth():
    if not path.exists(auth_file):
        return None
    try:
        with open(auth_file, "r", encoding="utf-8") as f:
            return load(f)
    except Exception as e:
        log.warning(f"Failed to load auth file: {e}")
        return None

def save_auth(token, uid):
    with open(auth_file, "w", encoding="utf-8") as f:
        dump({"token": token, "uid": uid}, f)


