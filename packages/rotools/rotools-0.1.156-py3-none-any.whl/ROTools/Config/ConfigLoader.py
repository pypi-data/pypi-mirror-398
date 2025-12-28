import logging
import os
from pathlib import Path

import yaml

from ROTools.Config.Config import Config
from ROTools.core.DictObj import DictObj

log = logging.getLogger(__name__)

def load_config(config_file):
    import yaml
    return Config(DictObj(yaml.safe_load(open(config_file))))

class ConfigLoader:
    def __init__(self, file_path, env_prefix=None):

        self.file_path = file_path.absolute()

        config = load_config(config_file=self.file_path)

        self._process_services(config)
        self._process_env(config, env_prefix)

        self.config = config
        self._process_external_files(config)

    def load_section(self, file_path, section_name, cb=None):
        config = load_config(config_file=file_path)
        config = cb(config) if cb else config
        self.config.set(section_name, config)

    def get_config(self):
        return self.config

    @staticmethod
    def _process_env(config, prefix):
        if prefix is None:
            return

        extra_config = [(key[len(prefix):].lower(), value) for key, value in os.environ.items() if key.startswith(prefix)]

        for key, value in extra_config:
            _old_value = config.get(key, None)
            if _old_value is None:
                continue

            if isinstance(_old_value, bool):
                value = value in ["true", "True", "TRUE", "1", ]

            if isinstance(_old_value, int):
                value = int(value)

            if isinstance(_old_value, float):
                value = float(value)

            config.set(key, value)

    @staticmethod
    def _process_services(config):
        if not config.has("services.config_files"):
            return

        files = [Path(a) for a in config.get("services.config_files", [])]
        files = [a for a in files if a.exists()]
        if len(files) == 0:
            raise Exception("No services config files found!")

        config.services.rem("config_files")

        services = DictObj(yaml.safe_load(open(files[0])))

        for key, value in [(a, b) for a, b in services.items() if b.has("ref_name")]:
            service_config = services.get(value.ref_name, throw=True)

            value.rem("ref_name", throw=False)

            for key2, value2 in service_config.items():
                value.set(key2, value2)


        for key, value in config.services.items():
            ref_name = value if isinstance(value, str) else value.get("ref_name")
            if ref_name is None:
                continue
            service_config = services.get(ref_name, throw=True)
            if isinstance(value, DictObj):
                value.rem("ref_name")

            if isinstance(value, str):
                value = DictObj()
                config.services.set(key, value)

            for key2, value2 in service_config.items():
                value.set(key2, value2)

    def _process_external_files(self, config):
        for item in config.get("load_sections", DictObj()).values():
            self.load_section(file_path=Path(item.file).absolute(), section_name=item.name)

