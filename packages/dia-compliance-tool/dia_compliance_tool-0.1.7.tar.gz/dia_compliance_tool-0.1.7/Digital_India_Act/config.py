import os

class APIConfigError(Exception):
    pass

def get_api_key(name: str, required: bool = True) -> str | None:
    value = os.getenv(name)
    if required and not value:
        raise APIConfigError(
            f"{name} is not set. Please export it as an environment variable."
        )
    return value