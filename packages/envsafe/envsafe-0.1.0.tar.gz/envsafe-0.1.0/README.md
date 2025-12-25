# Envsafe
Python package for type-safe environment variables — no boilerplate, no surprises.
A tiny Python package for type-safe environment variables with automatic `.env` loading.

## Install
```
pip install envsafe
```

## Usage
```python
from envsafe import env

API_KEY = env.str("API_KEY")
DEBUG   = env.bool("DEBUG", default=False)
PORT    = env.int("PORT", default=8000)
ALLOWED = env.list("ALLOWED_HOSTS")
CONFIG  = env.json("CONFIG")
```

## Why envsafe?
- No os.getenv boilerplate
- .env auto-loaded
- Clean errors
- Zero configuration

