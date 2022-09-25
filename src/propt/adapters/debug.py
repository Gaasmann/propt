"""Debug utils."""
import pathlib
import pprint
from typing import Any


def dump(filename: str, obj: Any):
    """Dump data in a file under debug/"""
    dest = pathlib.Path("debug/")
    dest.mkdir(exist_ok=True)
    with open(dest / filename, "w") as f:
        f.write(pprint.pformat(obj, indent=2, width=90))
