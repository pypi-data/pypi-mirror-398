ALIVE_PREFIX = "alive:"
TIMEOUT_PREFIX = "timeout:"


def alive_sandbox_key(sandbox_id: str) -> str:
    return f"{ALIVE_PREFIX}{sandbox_id}"


def timeout_sandbox_key(sandbox_id: str) -> str:
    return f"{TIMEOUT_PREFIX}{sandbox_id}"
