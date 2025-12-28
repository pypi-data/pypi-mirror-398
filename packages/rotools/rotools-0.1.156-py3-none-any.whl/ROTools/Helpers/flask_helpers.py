import hashlib
from functools import lru_cache
from pathlib import Path

from markupsafe import Markup


@lru_cache(maxsize=1024)
def _get_file_hash(filename) -> str:
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()[:8]

def static_url(filename, **kwargs):
    from flask import url_for
    file_path = Path('static', filename ).resolve()
    hash_value = _get_file_hash(file_path)
    return url_for('static', filename=filename, q=hash_value, **kwargs)

def render_html_attrs(**kwargs) -> str:
    items = [f'{k}="{v}"' for k, v in kwargs.items() if v is not None and v != ""]
    res = " " + " ".join(items) if items else ""
    return Markup(res)

def render_color(value) -> str:
    if not value:
        return ""
    return f"style='color: #{value};'"