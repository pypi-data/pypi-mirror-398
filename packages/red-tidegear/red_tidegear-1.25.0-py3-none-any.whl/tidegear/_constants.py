# SPDX-FileCopyrightText: 2025 cswimr <copyright@csw.im>
# SPDX-License-Identifier: MPL-2.0

"""This module contains constants related to the Discord API or general cog development."""

from typing import Never, final

import discord
from redbot.core.commands.context import TICK


@final
class Constants:
    """A "class" that holds common constants useful for cog development.

    Example:
        ```py
        from tidegear import constants

        print(constants.MAX_MESSAGE_CHARACTERS)  # 2000
        ```
    """

    @classmethod
    def __new__(cls, *args, **kwargs) -> Never:
        msg = f"{cls.__name__} is not meant to be instantiated!"
        raise TypeError(msg)

    MAX_MESSAGE_CHARACTERS: int = 2000
    """The maximum amount of characters Discord will allow you to post in a single message when using the `content` field."""

    MAX_EMBEDS_PER_MESSAGE: int = 10
    """The maximum number of embeds allowed per message."""

    MAX_EMBED_CHARACTERS: int = 6000
    """The maximum combined amount of characters Discord will allow across all embeds in a single message."""

    MAX_EMBED_TITLE_CHARACTERS: int = 256
    """The maximum amount of characters one embed's title field can have."""

    MAX_EMBED_DESCRIPTION_CHARACTERS: int = 4096
    """The maximum amount of characters one embed's description field can have."""

    MAX_EMBED_FIELDS: int = 25
    """The maximum number of fields one embed can have."""

    MAX_FIELD_TITLE_CHARACTERS: int = 256
    """The maximum amount of characters one embed field's title can have."""

    MAX_FIELD_VALUE_CHARACTERS: int = 1024
    """The maximum amount of characters one embed field's value can have."""

    MAX_EMBED_AUTHOR_CHARACTERS: int = 256
    """The maximum amount of characters one embed's author name field can have."""

    MAX_EMBED_FOOTER_CHARACTERS: int = 2048
    """The maximum amount of characters one embed's footer text field can have."""

    MAX_COMPONENTS: int = 40
    """The maximum amount of components Discord will allow you to send in a message, including nested components."""

    MAX_COMPONENTS_CHARACTERS: int = 4000
    """The maximum amount of characters Discord will allow you to send within all text fields in a message utilizing Components V2."""

    MAX_STICKERS_PER_MESSAGE: int = 3
    """The maximum number of stickers allowed per message."""

    MAX_ATTACHMENTS_PER_MESSAGE: int = 10
    """The maximum number of attachments allowed per message."""

    MAX_ATTACHMENT_SIZE_NON_NITRO: int = 10 * 1024 * 1024  # 10 MB
    """The maximum file size (in bytes) for attachments without Nitro."""

    MAX_ATTACHMENT_SIZE_NITRO: int = 500 * 1024 * 1024  # 500 MB
    """The maximum file size (in bytes) for attachments with Nitro."""

    MAX_ATTACHMENT_SIZE_NITRO_BASIC: int = 50 * 1024 * 1024  # 50 MB
    """The maximum file size (in bytes) for attachments with Nitro Basic, or when a server is at Boost Level 2."""

    MAX_ATTACHMENT_SIZE_BOOST_3: int = 100 * 1024 * 1024  # 100 MB
    """The maximum file size (in bytes) for attachments when a server is at Boost Level 3."""

    ALLOWED_EMOJI_EXTENSIONS: set[str] = {"PNG", "WEBP", "JPEG", "JPG", "GIF", "AVIF"}
    """The file extensions accepted by Discord for use in custom emojis."""

    MAX_EMOJI_NAME_CHARACTERS: int = 32
    """The maximum number of characters allowed in a custom emoji name."""

    MAX_EMOJI_FILESIZE: int = 256 * 1024  # 256 KB
    """The maximum file size (in bytes) for a custom emoji."""

    TRUE: discord.PartialEmoji = discord.PartialEmoji.from_str(TICK)
    """The emoji used for [`ctx.tick()`][redbot.core.commands.Context.tick] calls, and for truthy values in [`tidegear.utils.get_bool_emoji`][].
    Corresponds to `redbot.core.commands.context.Tick`.
    """

    FALSE: discord.PartialEmoji = discord.PartialEmoji.from_str("\N{NO ENTRY SIGN}")
    """The emoji used for falsy values in [`tidegear.utils.get_bool_emoji`][] and for [`tidegear.chat_formatting.error`][]."""

    NONE: discord.PartialEmoji = discord.PartialEmoji.from_str("\N{BLACK QUESTION MARK ORNAMENT}\N{VARIATION SELECTOR-16}")
    """The emoji used for NoneType values in [`tidegear.utils.get_bool_emoji`][] and for [`tidegear.chat_formatting.question`][]."""

    INFO: discord.PartialEmoji = discord.PartialEmoji.from_str("\N{INFORMATION SOURCE}\N{VARIATION SELECTOR-16}")
    """The emoji used for [`tidegear.chat_formatting.info`][]"""

    WARNING: discord.PartialEmoji = discord.PartialEmoji.from_str("\N{WARNING SIGN}\N{VARIATION SELECTOR-16}")
    """The emoji used for [`tidegear.chat_formatting.warning`][]."""
