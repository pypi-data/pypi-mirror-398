def key_normalization(value: str) -> str:
    value = value.title()
    value = "".join(value.split())

    return value
