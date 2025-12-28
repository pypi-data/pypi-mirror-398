import logging


class ShortNameFilter(logging.Filter):
    def filter(self, record):
        record.shortname = record.name.rsplit(".", 1)[-1]
        return True
