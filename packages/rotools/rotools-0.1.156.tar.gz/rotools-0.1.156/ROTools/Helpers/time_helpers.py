from datetime import datetime, timezone

import humanize


def dt_to_unix(dt):
    return int(dt.timestamp())


def dt_to_text_delta(dt, with_ago=True):
    if with_ago:
        return humanize.naturaltime(datetime.now(timezone.utc) - dt)
    return humanize.naturaldelta(datetime.now(timezone.utc) - dt)
