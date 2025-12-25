from __future__ import annotations

import datetime

from latticeflow.go.cli.utils import constants


def _local_tz() -> datetime.tzinfo:
    """Returns the local timezone of the machine or UTC in case it could not be
    determined."""
    return (
        datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
        or datetime.timezone.utc
    )


def timestamp_to_localized_datetime(timestamp: int) -> datetime.datetime:
    """Returns the given POSIX timestamp as a ``datetime`` object having the local
    timezone."""
    return datetime.datetime.fromtimestamp(timestamp, _local_tz())


def datetime_to_str(time: datetime.datetime) -> str:
    """Returns the given ``datetime`` object as str."""
    return time.strftime(constants.DATETIME_FORMAT)
