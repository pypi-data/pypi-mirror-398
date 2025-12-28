import os
from pathlib import Path

from ROTools.Helpers.Attr import setattr_ex, getattr_ex
from ROTools.core.DictObj import DictObj

class Config(DictObj):
    def __init__(self, parent):
        super().__init__(parent)

    def print_config(self):
        dump = self.get("dump_config.enabled", False)
        if not dump:
            return

        config = self.clone()
        for item in self.get("dump_config.exclude", []):
            config.rem(item, throw=False)
        config.dump()
        print()

