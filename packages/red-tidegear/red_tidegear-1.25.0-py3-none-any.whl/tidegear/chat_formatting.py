# SPDX-FileCopyrightText: 2025 cswimr <copyright@csw.im>
# SPDX-License-Identifier: MPL-2.0

# ruff:  noqa: PLC0415

"""Wrapper around [`redbot.core.utils.chat_formatting`][] and [`humanize`](https://humanize.readthedocs.io/en/stable)
that overrides a couple functions to use Tidegear constants.
Both of those modules are star imported into this one, with [`chat_formatting`][redbot.core.utils.chat_formatting] taking priority.
"""

from datetime import datetime
from enum import StrEnum

import humanize
from humanize import *  # noqa: F403  # pyright: ignore[reportWildcardImportFromLibrary]
from redbot.core.utils.chat_formatting import *  # noqa: F403  # pyright: ignore[reportWildcardImportFromLibrary]

from tidegear import constants

humanize_timedelta = humanize.precisedelta
"""Replaces [`chat_formatting.humanize_timedelta`][redbot.core.utils.chat_formatting.humanize_timedelta] with [`humanize.precisedelta`][]."""


class TimestampStyle(StrEnum):
    """Discord timestamp format options."""

    SHORT_TIME = "t"
    """`4:45 PM`"""
    LONG_TIME = "T"
    """`4:45:33 PM`"""
    SHORT_DATE = "d"
    """`7/5/25`"""
    LONG_DATE = "D"
    """`July 5th, 2025`"""
    SHORT_DATE_AND_TIME = "f"
    """`July 5th, 2025 at 4:45 PM`"""
    LONG_DATE_AND_TIME = "F"
    """`Saturday, July 5th, 2025 at 4:45 PM`"""
    RELATIVE = "R"
    """`3 minutes ago`"""


def format_datetime(dt: datetime, style: TimestampStyle = TimestampStyle.SHORT_DATE_AND_TIME) -> str:
    """Format a datetime into a Discord-compatible timestamp string.

    Similar to [`discord.utils.format_dt`][], but uses an enum to provide better code readability.

    Example:
        ```python
        from discord.utils import utcnow
        from tidegear import chat_formatting as cf

        datetime = utcnow()
        print(cf.format_datetime(dt=datetime, style=cf.TimestampStyle.LONG_DATE_AND_TIME))
        ```

    Args:
        dt: The datetime to convert into a Discord timestamp.
        style: The timestamp style to apply.

    Returns:
        A string like `<t:1618924800:f>` that Discord will render according to the given style.
    """
    return f"<t:{int(dt.timestamp())}:{style}>"


def success(text: str) -> str:
    """Wrap a string in a success emoji.

    Args:
        text: The text to wrap.

    Returns:
        The wrapped text, prefixed with the [success constant][tidegear._constants.Constants.TRUE].
    """
    return f"{constants.TRUE} {text}"


def error(text: str) -> str:
    """Wrap a string in an error emoji.

    Args:
        text: The text to wrap.

    Returns:
        The wrapped text, prefixed with the [error constant][tidegear._constants.Constants.FALSE].
    """
    return f"{constants.FALSE} {text}"


def warning(text: str) -> str:
    """Wrap a string in a warning emoji.

    Args:
        text: The text to wrap.

    Returns:
        The wrapped text, prefixed with the [warning constant][tidegear._constants.Constants.WARNING].
    """
    return f"{constants.WARNING} {text}"


def question(text: str) -> str:
    """Wrap a string in a question emoji.

    Args:
        text: The text to wrap.

    Returns:
        The wrapped text, prefixed with the [question constant][tidegear._constants.Constants.NONE].
    """
    return f"{constants.NONE} {text}"


def info(text: str) -> str:
    """Wrap a string in an information emoji.

    Args:
        text: The text to wrap.

    Returns:
        The wrapped text, prefixed with the [info constant][tidegear._constants.Constants.INFO].
    """
    return f"{constants.INFO} {text}"
