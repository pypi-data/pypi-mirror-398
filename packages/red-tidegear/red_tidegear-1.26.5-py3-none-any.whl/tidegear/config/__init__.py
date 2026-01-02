# SPDX-FileCopyrightText: 2025 cswimr <copyright@csw.im>
# SPDX-License-Identifier: MPL-2.0

"""Type-safe, declarative configuration management for Red-DiscordBot / Tidegear cogs.

Warning:
    The `tidegear.config` module is an active work-in-progress, and is being actively iterated on.
    I (@cswimr) will attempt to avoid breakage, but I cannot provide any guarantees.
    I will not be marking breaking changes to this module as major/minor version changes until it is considered stabilized.

The `tidegear.config` module offers validation logic through Pydantic,
true intellisense, and support for subclasses of [`BaseModel`][pydantic.BaseModel],
all on top of the familiar and battle-tested [`redbot.core.config`][] module.

This module aims to have no assumptions about the cogs using its featureset. This means that you do not need to
be using Tidegear for the rest of your cog in order to take advantage of this specific module. This also allows
for the registration of arbitrary configuration schemas, like in the case of Tidegear Sentinel, which uses this
module for the internal Sentinel configuration that is shared between all Sentinel cogs. This is why
[`BaseConfigSchema`][tidegear.config.BaseConfigSchema] uses a [`str`][] `cog_name`
attribute instead of accepting instances of [`Cog`][tidegear.cog.Cog].

In the future, this module will also allow for automatic generation of configuration menus using Components V2.
This will aid in the reduction of what I like to call "config command sprawl", where the majority of the commands in
a given cog are just simple configuration setters. Focus on developing functionality,
not boilerplating your configuration options.

Example:
    ```py
    from typing import Annotated, ClassVar, reveal_type

    from redbot.core import commands
    from red_commons.logging import getLogger
    from tidegear.config import BaseConfigSchema, ConfigMeta, GlobalConfigOption, GuildConfigOption
    from typing_extensions import override


    class ExampleConfigSchema(BaseConfigSchema):
        version: ClassVar[int] = 1

        example_global_option: Annotated[GlobalConfigOption[str], ConfigMeta(default="example")]
        example_guild_option: Annotated[GuildConfigOption[int], ConfigMeta(default=100)]


    class ExampleCog(commands.Cog):
        config: ExampleConfigSchema
        # Consider using your Discord ID for this, instead of a random assortment of numbers.
        _config_identifier: int = 1234567890

        @override
        async def cog_load(self) -> None:
            self.config = await ExampleConfigSchema.init(
                cog_name=self.__cog_name__,
                identifier=self._config_identifier,
                logger=getLogger(f"red.ExampleRepo.{self.__cog_name__}"),
            )

        @commands.is_owner()
        @commands.command()
        async def global_config(self, ctx: commands.Context, *, value: str | None = None) -> None:
            if value:
                await self.config.example_global_option.set(value)  # Works

                await self.config.example_global_option.set([value])
                # ERROR: ValidationError: Incorrect type, expected `int` (got `list[int]`)

                await ctx.send(f"Set `{self.config.example_global_option.key}` to `{value}`")
            else:
                current_value = await self.config.example_global_option.get()
                # OR
                current_value = await self.config.example_global_option()
                # Both of these lines work and do the same thing.
                # The `__call__` interface is provided to be more familiar to Red Config users.

                reveal_type(current_value)  # str
                await ctx.send(
                    f"The current value of the `{self.config.example_global_option.key}` setting is `{current_value}`."
                )

        @commands.admin()
        @commands.guild_only()
        @commands.command()
        async def guild_config(self, ctx: commands.GuildContext, *, value: int | None = None) -> None:
            if value:
                await self.config.example_guild_option.set(ctx.guild, value)
                await ctx.send(f"Set `{self.config.example_guild_option.key}` to `{value}`")
            else:
                current_value = await self.config.example_guild_option.get(ctx.guild)
                reveal_type(current_value)  # int
                await ctx.send(f"The current value of the `{self.config.example_guild_option.key}` setting is `{current_value}`.")
    ```
"""

from tidegear.config.exceptions import ConfigMigrationError, MalformedConfigError, ReadOnlyConfigError, SchemaRegistrationError
from tidegear.config.options import (
    ChannelConfigOption,
    ConfigScope,
    CustomConfigGroup,
    CustomConfigOption,
    GlobalConfigOption,
    GuildConfigOption,
    MemberConfigOption,
    RoleConfigOption,
    UserConfigOption,
)
from tidegear.config.schema import BaseConfigSchema, ConfigMeta
from tidegear.config.types import Jsonable, JsonableType

__all__ = [
    "ConfigMeta",
    "BaseConfigSchema",
    "ConfigScope",
    "CustomConfigGroup",
    "CustomConfigOption",
    "GlobalConfigOption",
    "ChannelConfigOption",
    "GuildConfigOption",
    "Jsonable",
    "JsonableType",
    "MemberConfigOption",
    "RoleConfigOption",
    "UserConfigOption",
    "MalformedConfigError",
    "ReadOnlyConfigError",
    "ConfigMigrationError",
    "SchemaRegistrationError",
]
