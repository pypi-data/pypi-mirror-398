import os
from .loaders import load_env_once
from .exceptions import EnvError
from . import parsers

load_env_once()

class Env:
    def _get(self, key, default):
        val = os.getenv(key)
        if val is None:
            if default is not None:
                return default
            raise EnvError(key, "missing")
        return val

    def str(self, key, default=None):
        return self._get(key, default)

    def int(self, key, default=None):
        val = self._get(key, default)
        return val if val is None else parsers.parse_int(key, val)

    def float(self, key, default=None):
        val = self._get(key, default)
        return val if val is None else parsers.parse_float(key, val)

    def bool(self, key, default=None):
        val = self._get(key, default)
        return val if val is None else parsers.parse_bool(key, val)

    def list(self, key, default=None, *, sep=","):
        val = self._get(key, default)
        return val if val is None else parsers.parse_list(key, val, sep)

    def json(self, key, default=None):
        val = self._get(key, default)
        return val if val is None else parsers.parse_json(key, val)

    def require(self, *keys):
        for key in keys:
            if os.getenv(key) is None:
                raise EnvError(key, "missing")
