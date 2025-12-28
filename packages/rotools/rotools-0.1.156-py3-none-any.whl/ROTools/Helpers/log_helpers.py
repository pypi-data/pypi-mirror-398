import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import humanize
import yaml


def print_info():
    python_ver = sys.version.replace('\n', ' ')
    print()
    print(f"Build version    \t: {os.getenv('RR_BUILD_VERSION', 'undefined')}")
    print(f"Build time UTC   \t: {os.getenv('RR_BUILD_TIME', 'undefined')}")
    print(f"Current time UTC \t: {datetime.now(timezone.utc)}")
    if os.getenv('RR_BUILD_TIME') is not None:
        build_old = humanize.naturaltime(datetime.now(timezone.utc) - datetime.fromisoformat(os.getenv('RR_BUILD_TIME')))
        print(f"Build old\t\t: {build_old}")
    print(f"PWD              \t: {os.getcwd()}")
    print(f"Python           \t: {python_ver}")
    print("---")
    print()


def init_logging(path):
    if not path.exists():
        raise FileNotFoundError(f"File {path} not found")

    import logging.config
    log_file_path = Path(".logs")
    log_file_path.mkdir(parents=True, exist_ok=True)

    with open(path, "rt") as f:
        config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)