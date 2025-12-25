class EnvError(RuntimeError):
    def __init__(self, key: str, message: str):
        super().__init__(f"[envsafe] {key}: {message}")
