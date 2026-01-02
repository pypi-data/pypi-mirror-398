# SPDX-FileCopyrightText: 2025 cswimr <copyright@csw.im>
# SPDX-License-Identifier: MPL-2.0

"""A cog for all cogs using Tidegear to load. Used primarily to bootstrap translations."""

from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.i18n import Translator, cog_i18n

_ = Translator("TidegearCog", __file__)


@cog_i18n(_)
class TidegearCog(commands.Cog):
    """Common cog shared between all cogs that utilize Tidegear."""

    def __init__(self, bot: Red) -> None:
        self.bot: Red = bot
