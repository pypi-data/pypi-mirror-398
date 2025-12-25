import os
from .loaders import load_env_once
from .exceptions import EnvError
from . import parsers

load_env_once()


class Env:
    def _get(self, key, default, required):
        val = os.getenv(key)
        if val is None:
            if required:
                raise EnvError(key, "missing")
            return default
        return val

    def str(self, key, default=None, *, required=True):
        return self._get(key, default, required)

    def int(self, key, default=None, *, required=True):
        val = self._get(key, default, required)
        return val if val is None else parsers.parse_int(key, val)

    def float(self, key, default=None, *, required=True):
        val = self._get(key, default, required)
        return val if val is None else parsers.parse_float(key, val)

    def bool(self, key, default=None, *, required=True):
        val = self._get(key, default, required)
        return val if val is None else parsers.parse_bool(key, val)

    def list(self, key, default=None, *, sep=",", required=True):
        val = self._get(key, default, required)
        return val if val is None else parsers.parse_list(key, val, sep)

    def json(self, key, default=None, *, required=True):
        val = self._get(key, default, required)
        return val if val is None else parsers.parse_json(key, val)

    def require(self, *keys):
        for key in keys:
            if os.getenv(key) is None:
                raise EnvError(key, "missing")
