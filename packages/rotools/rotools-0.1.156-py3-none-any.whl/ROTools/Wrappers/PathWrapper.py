import os
import shutil
from pathlib import Path

class PathWrapper:
    def __init__(self, *args, offset=None, **kwargs):
        self._root = Path(*args, **kwargs)
        self._path_offset = Path()

        if offset:
            if isinstance(offset, str):
                offset = [offset,]
            self.set_offset(*offset)

    def set_offset(self, *args, **kwargs):
        self._path_offset = Path(*args, **kwargs)

    def get_path(self, *args, create_parent=False, throw=False):
        path = os.path.join(self._root, self._path_offset, *args)

        if throw and not os.path.exists(path):
            raise FileNotFoundError(path)

        if create_parent:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        return Path(path)

    def copy_file_to(self, *args, dst, flat=False):
        file_name = Path(*args)
        if flat:
            out_path = dst.get_path(args[-1], create_parent=True)
        else:
            out_path = dst.get_path(*args, create_parent=True)

        shutil.copyfile(self.get_path(file_name, throw=True), out_path)

    def read_file(self, path):
        with open(self.get_path(path)) as f:
            return f.read()

    def clear_all(self):
        _path = self.get_path()
        if os.path.exists(_path):
            shutil.rmtree(_path)
        os.makedirs(_path)






