import os

configs = {}


def _get_config(property: str, optional=False):
    if not optional and property not in configs:
        raise Exception(f"Undefined {property}")
    return configs[property] if property in configs else None


def _get_config(property: str, optional=False):
    return os.environ[property] if property in os.environ else _get_config(property, optional)


OPENAI_API_KEY = _get_config('OPENAI_API_KEY')
EMBEDDING_MODEL = _get_config('EMBEDDING_MODEL', "text-embedding-ada-002")