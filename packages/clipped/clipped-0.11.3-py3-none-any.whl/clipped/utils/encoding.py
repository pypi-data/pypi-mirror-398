import base64


def encode(value):
    return base64.b64encode(value.encode("utf-8")).decode("utf-8")


def decode(value):
    return base64.b64decode(value).decode("utf-8")


def urlsafe_b64decode(b64string):
    if isinstance(b64string, str):
        b64string = bytes(b64string, "utf-8")
    padded = b64string + b"=" * (4 - len(b64string) % 4)
    payload = base64.urlsafe_b64decode(padded)
    try:
        return payload.decode("utf-8")
    except Exception:  # noqa
        return payload
