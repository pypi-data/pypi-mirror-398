import hashlib

from ROTools.Helpers.text_helpers import get_text_hash


def is_primitive(obj):
    return isinstance(obj, (int, float, str, bool, type(None)))


def is_collection_of_primitive(obj):
    return isinstance(obj, (list, tuple)) and all([is_primitive(a) for a in obj])


class HashBuilder:
    def __init__(self, obj, keys):
        self.obj = obj
        self.keys = keys

    def _gen_line(self, key):
        value = self.obj.get(key)

        if is_primitive(value):
            return f"{key}={value}"

        if is_collection_of_primitive(value):
            return f"{key}={str(value)}"

        return f"{key}=hash:{value.generate_hash()}"

    def generate_text(self, _len=32):
        text = [self._gen_line(a) for a in self.keys]
        text = "\n".join(text)
        return get_text_hash(text, _len=_len)

    def generate_bin(self, _len=32):
        text = [self._gen_line(a) for a in self.keys]
        binary_data = "\n".join(text).encode('utf-8')
        sha1_hash = hashlib.sha1(binary_data).digest()
        return sha1_hash[:_len]
