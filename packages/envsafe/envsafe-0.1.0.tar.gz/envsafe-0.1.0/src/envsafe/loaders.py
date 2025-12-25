from dotenv import load_dotenv, find_dotenv

_loaded = False


def load_env_once():
    global _loaded
    if not _loaded:
        load_dotenv(find_dotenv(), override=False)
        _loaded = True
