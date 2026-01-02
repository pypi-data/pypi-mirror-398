# SPDX-FileCopyrightText: 2025 cswimr <copyright@csw.im>
# SPDX-License-Identifier: MPL-2.0

"""Module containing discord.py argument converters."""

from typing import TYPE_CHECKING

from redbot.core import commands
from redbot.core.i18n import Translator

_ = Translator("TidegearCog", __file__)


class _CogConverter:
    @classmethod
    def convert(cls, ctx: commands.Context, argument: str) -> commands.Cog:
        cog = ctx.bot.get_cog(argument)
        if not cog:
            msg = _("The {argument} cog is not loaded!").format(argument=argument)
            raise commands.BadArgument(msg)
        return cog


if TYPE_CHECKING:
    CogConverter = commands.Cog
    """This converter can be used within a command's parameter typehints to return a [`redbot.core.commands.Cog`][] object.
    **This converter does NOT return a Tidegear cog.**
    """
else:
    CogConverter = _CogConverter
