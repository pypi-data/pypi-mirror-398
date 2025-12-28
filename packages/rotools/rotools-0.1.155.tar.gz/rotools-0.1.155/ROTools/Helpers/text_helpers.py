import hashlib


def truncate(text, width):
    text = "" if text is None else str(text)

    if len(text) <= width:
        return text

    if width == 1:
        return "…"
    return text[: width - 1] + "…"


def remove_prefix(text, prefix):
    return text[text.startswith(prefix) and len(prefix):]


def get_text_hash(value, _len=32):
    hash_object = hashlib.sha256()
    if isinstance(value, str):
        value = value.encode()
    hash_object.update(value)
    return hash_object.hexdigest()[:_len]
