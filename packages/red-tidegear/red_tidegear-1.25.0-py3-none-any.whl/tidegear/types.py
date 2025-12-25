# SPDX-FileCopyrightText: 2025 cswimr <copyright@csw.im>
# SPDX-License-Identifier: MPL-2.0

"""This module contains type aliases related to the Discord API or general cog development."""

import discord
from redbot.core.commands.context import GuildContext

GuildChannel = discord.abc.GuildChannel | discord.Thread
"""A superset of [`discord.abc.GuildChannel`][] that adds [`discord.Thread`][]."""

GuildMesseagableChannel = discord.TextChannel | discord.VoiceChannel | discord.StageChannel | discord.Thread
"""A subset of Discord guild channels that support sending messages through [`.send`][discord.abc.Messageable.send].

Specifically, this type covers:

- [`discord.TextChannel`][]
- [`discord.VoiceChannel`][]
- [`discord.StageChannel`][]
- [`discord.Thread`][]
"""

GuildMesseagable = GuildMesseagableChannel | GuildContext
"""Any messeagable target that is scoped to a guild and implements [`.send`][discord.abc.Messageable.send].
This includes [`GuildMesseagableChannel`][tidegear.types.GuildMesseagableChannel] and [`GuildContext`][redbot.core.commands.context.GuildContext].
"""
