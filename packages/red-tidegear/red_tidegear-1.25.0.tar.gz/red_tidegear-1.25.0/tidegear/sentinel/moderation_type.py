# SPDX-FileCopyrightText: 2025 cswimr <copyright@csw.im>
# SPDX-License-Identifier: MPL-2.0

"""Defines the base class for Sentinel moderation types."""

import inspect
from dataclasses import dataclass
from types import CoroutineType
from typing import TYPE_CHECKING, Any, Awaitable, Callable

import discord
import orjson
from class_registry.base import RegistryKeyError
from class_registry.registry import ClassRegistry
from discord.utils import MISSING
from redbot.core import commands
from redbot.core.bot import Red
from typing_extensions import override

from tidegear import chat_formatting as cf
from tidegear.exceptions import ArgumentTypeError
from tidegear.types import GuildChannel
from tidegear.utils import class_overrides_attribute

if TYPE_CHECKING:
    from tidegear.sentinel.cog import SentinelCog, Targetable
    from tidegear.sentinel.db.tables import Moderation


def _str(value: Any, bot: Red) -> str:
    return str(value)


@dataclass
class ModerationMetadataEntry:
    """Dataclass representing a metadata entry within a moderation type.

    Attributes:
        key: The key the metadata is stored under within the database.
        human_name: A name to show to end users.
        show_in_history: Whether or not this metadata should be shown within
            the output of [`sentinel_history_menu`][tidegear.sentinel.SentinelCog.sentinel_history_menu].
        func: A function that converts the metadata value from within the database (where it can be anything) to a string for display.
            Can be synchronous or asynchronous.
    """

    key: str
    human_name: str
    show_in_history: bool = False
    func: Callable[[Any, Red], str | Awaitable[str]] = _str

    async def _call_func(self, value: Any, bot: Red) -> str:
        result = self.func(value, bot)
        if inspect.isawaitable(result):
            return await result
        return result

    def update_moderation(self, value: object, moderation: "Moderation") -> "Moderation":
        """Update a moderation's metadata key. Does not save the moderation to the database, you must do that manually.

        Args:
            value: The value to update the moderation's metadata key with.
            moderation: The moderation to update.

        Returns:
            The updated moderation.
        """
        meta = moderation.meta
        meta[self.key] = value
        moderation.metadata = orjson.dumps(meta).decode("utf-8")
        return moderation

    async def fetch_from_moderation(self, moderation: "Moderation", bot: Red) -> str | None:
        """Fetch the value of a moderation's metadata key.

        Args:
            moderation: The moderation to fetch metadata from.
            bot: A bot object to pass into the metadata function.

        Returns:
            The fetched metadata value, or `None` if the metadata key is unset on the moderation's metadata column.
        """
        meta = moderation.meta
        if (value := meta.get(self.key, None)) is not None:
            return await self._call_func(value, bot)
        return None


class ModerationType:
    r"""This is a base class for Sentinel moderation types.

    Example:
        ```python
        from discord import Member, Permissions, User
        from redbot.core import commands
        from typing_extensions import override

        from tidegear import chat_formatting as cf
        from tidegear.sentinel import SentinelCog, Moderation, PartialGuild, PartialUser, ModerationType


        class Warn(ModerationType):
            key = "warn"
            string = "warn"
            verb = "warned"
            permissions = Permissions(moderate_members=True)

            @override
            @classmethod
            async def user_target_handler(cls, ctx: commands.GuildContext, target: User | Member, reason: str) -> Moderation:
                partial_target = await PartialUser.upsert(user=target)
                partial_moderator = await PartialUser.upsert(user=ctx.author)
                partial_guild = await PartialGuild.upsert(guild=ctx.guild)
                moderation = Moderation(
                    _data={
                        Moderation.guild_id: partial_guild.id,
                        Moderation.type_key: cls.key,
                        Moderation.target_user_id: partial_target.id,
                        Moderation.moderator_id: partial_moderator.id,
                        Moderation.reason: reason,
                    }
                )
                await moderation.save()
                await ctx.send(
                    content=(
                        f"{target.mention} has {cls.embed_desc}{cls.verb}! (Case: {cf.inline(f'#{moderation.id:,}')})"
                        f"\n{cf.bold(text='Reason:')} {cf.inline(text=reason)}"
                    )
                )
                return moderation

            @override
            @classmethod
            async def resolve_handler(cls, cog: SentinelCog, moderation: Moderation) -> None:
                return
        ```

    Attributes:
        key: The key to use for this type. This should be unique, as this is how the type is registered internally.
            Changing this key will break existing cases with this type.
            Defaults to `type`.
        string: The string to display for this type. Defaults to `type`.
        verb: The verb to use for this type. Defaults to `typed`.
        embed_desc: The string to use for embed descriptions. Defaults to `been `.
        removes_from_guild: Whether this type's handler removes the target from the guild,
            or if the moderation is expected to occur whenever the user is not in the guild.
            This does not actually remove the target from the guild; the handler method is responsible for that.
            **Moderation types that remove users from guilds are responsible for contacting users using the
            [`sentinel_contact_target`][tidegear.sentinel.SentinelCog.sentinel_contact_target] method *before* removing them from the guild.**
            Defaults to `False`.
        permissions: The Discord permissions required for this type's moderation handler to function.
            Defaults to [`Permissions.none`][discord.Permissions.none].
        history_metadata: A mapping of metadata keys to make visible in the
            output of [`sentinel_history_menu`][tidegear.sentinel.SentinelCog.sentinel_history_menu].
            Values will be passed through the given function before being output in history,
            to allow for storing raw values and then formatting them later. Defaults to [`dict`][].
    """

    key: str = "type"
    string: str = "type"
    verb: str = "typed"
    embed_desc: str = "been "
    removes_from_guild: bool = False
    permissions: discord.Permissions = discord.Permissions.none()
    metadata: list[ModerationMetadataEntry] = []

    @property
    def can_edit_duration(self) -> bool:
        """Check whether or not this type overrides the `edit_duration_handler` method.

        Returns:
            If this type supports editing the duration of moderations.
        """
        return class_overrides_attribute(child=type(self), parent=ModerationType, attribute="duration_edit_handler")

    @property
    def can_expire(self) -> bool:
        """Check whether or not this type overrides the `expiry_handler` method.

        Returns:
            If this type supports moderation expiry.
        """
        return class_overrides_attribute(child=type(self), parent=ModerationType, attribute="expiry_handler")

    @property
    def can_target_channels(self) -> bool:
        """Check whether or not this type overrides the `channel_target_handler` method.
        Consider using [`.handler`][tidegear.sentinel.ModerationType.handler] instead
        if you just want to retrieve the correct handler for a [`Targetable`][tidegear.sentinel.Targetable] object.

        Returns:
            If this type supports targeting channels.
        """
        return class_overrides_attribute(child=type(self), parent=ModerationType, attribute="channel_target_handler")

    @property
    def can_target_members(self) -> bool:
        """Check whether or not this type overrides the `member_target_handler` method.
        Consider using [`.handler`][tidegear.sentinel.ModerationType.handler] instead
        if you just want to retrieve the correct handler for a [`Targetable`][tidegear.sentinel.Targetable] object.

        Returns:
            If this type supports targeting members.
        """
        return class_overrides_attribute(child=type(self), parent=ModerationType, attribute="member_target_handler")

    @property
    def can_target_roles(self) -> bool:
        """Check whether or not this type overrides the `role_target_handler` method.
        Consider using [`.handler`][tidegear.sentinel.ModerationType.handler] instead
        if you just want to retrieve the correct handler for a [`Targetable`][tidegear.sentinel.Targetable] object.

        Returns:
            If this type supports targeting roles.
        """
        return class_overrides_attribute(child=type(self), parent=ModerationType, attribute="role_target_handler")

    @property
    def can_target_users(self) -> bool:
        """Check whether or not this type overrides the `user_target_handler` method.
        Consider using [`.handler`][tidegear.sentinel.ModerationType.handler] instead
        if you just want to retrieve the correct handler for a [`Targetable`][tidegear.sentinel.Targetable] object.

        Returns:
            If this type supports targeting users.
        """
        return class_overrides_attribute(child=type(self), parent=ModerationType, attribute="user_target_handler")

    @property
    def is_resolvable(self) -> bool:
        """Check whether or not this type overrides the `resolve_handler` method.

        Returns:
            If this type supports being resolved.
        """
        return class_overrides_attribute(child=type(self), parent=ModerationType, attribute="resolve_handler")

    @property
    def name(self) -> str:
        """Returns the string to display for this type. This is an alias for the `string` attribute."""
        return self.string

    @override
    def __str__(self) -> str:
        """Return the value of `self.string`."""
        return self.string

    @override
    def __repr__(self) -> str:
        attrs = [
            ("key", self.key),
            ("removes_from_guild", self.removes_from_guild),
        ]
        joined = " ".join(f"{key}={value!r}" for key, value in attrs)
        return f"<{self.__class__.__name__} {joined}>"

    def handler(self, target: "Targetable") -> "Callable[..., CoroutineType[Any, Any, Moderation]]":
        """Returns the proper handler method for the given target type.

        Example:
            ```python
            # assuming `ctx` is a `commands.Context` object,
            # this runs the `user_target_handler` for the `Warn` type if it is defined.
            await Warn().handler(target=ctx.author)(ctx=ctx, target=target)
            ```

        Args:
            target: The target you'd like to retrieve the handler for.

        Raises:
            ArgumentTypeError: Raised if the type does not support targeting the target type given,
                or if the target type given does not match this method's typehints.

        Returns:
            The resulting handler method.
        """
        if isinstance(target, (discord.Member, discord.User)):
            if isinstance(target, discord.Member) and self.can_target_members:
                return self.member_target_handler
            if not self.can_target_users:
                if isinstance(target, discord.User) and self.can_target_members:
                    msg = f"Moderation type {self.__class__.__name__} only supports targeting members of the current guild!"
                else:
                    msg = f"Moderation type {self.__class__.__name__} does not support targeting users!"
                raise ArgumentTypeError(msg)
            return self.user_target_handler

        if isinstance(target, GuildChannel):
            if not self.can_target_channels:
                msg = f"Moderation type {self.__class__.__name__} does not support targeting channels!"
                raise ArgumentTypeError(msg)
            return self.channel_target_handler

        if isinstance(target, discord.Role):
            if not self.can_target_roles:
                msg = f"Moderation type {self.__class__.__name__} does not support targeting roles!"
                raise ArgumentTypeError(msg)
            return self.role_target_handler

        msg = f"Type {type(target).__name__} is an invalid target type!"
        raise ArgumentTypeError(msg)

    @classmethod
    async def convert(cls, ctx: commands.Context, argument: str) -> "type[ModerationType]":
        """A discord.py [`commands.Converter`][discord.ext.commands.Converter] for fetching moderation types.

        Example:
            ```python
            from redbot.core import commands
            from tidegear.sentinel import ModerationType


            @commands.command()
            async def example(self, ctx: commands.Context, moderation_type: ModerationType) -> None:
                await ctx.send(content=ModerationType.key)
            ```

        Args:
            ctx: The context of the command the converter is being used by.
            argument: The key of the moderation type to search for.

        Raises:
            commands.BadArgument: If no moderation type exists in the registry with the given key.

        Returns:
            The fetched moderation type.
        """
        try:
            return moderation_type_registry.get_class(argument)
        except RegistryKeyError as e:
            msg = f"Couldn't find a moderation type with the key {cf.inline(str(argument))}!"
            raise commands.BadArgument(msg) from e

    @classmethod
    async def member_target_handler(
        cls, *, cog: "SentinelCog", ctx: commands.GuildContext, target: discord.Member, silent: bool = MISSING, reason: str, **kwargs: Any
    ) -> "Moderation":
        """This method should be overridden by any child classes that can target members but **not** users,
        and should retain the same starting keyword arguments.
        If your child class can target people outside of the current guild,
        consider using [`.user_target_handler`][tidegear.sentinel.ModerationType.user_target_handler] instead.

        Args:
            cog: A cog instance of a Sentinel cog.
            ctx: The context of the command.
            target: The target of the moderation.
            silent: Whether or not to direct message the user.
                This will be ignored if the type has [`removes_from_guild`][tidegear.sentinel.ModerationType] set to `False`.
            reason: The reason for this moderation.
            **kwargs (dict[str, Any]): Any additional keyword arguments;
                will be passed in by the [`sentinel_moderate`][tidegear.sentinel.SentinelCog.sentinel_moderate] function
                and can be accessed using [`get_kwarg`][tidegear.utils.get_kwarg].

        Returns:
            The resulting moderation.
        """
        raise NotImplementedError

    @classmethod
    async def user_target_handler(
        cls,
        *,
        cog: "SentinelCog",
        ctx: commands.GuildContext,
        target: discord.Member | discord.User,
        silent: bool = MISSING,
        reason: str,
        **kwargs: Any,
    ) -> "Moderation":
        """This method should be overridden by any child classes that can target users, but should retain the same starting keyword arguments.

        Args:
            cog: A cog instance of a Sentinel cog.
            ctx: The context of the command.
            target: The target of the moderation.
            silent: Whether or not to direct message the user.
                This will be ignored if the type has [`removes_from_guild`][tidegear.sentinel.ModerationType] set to `False`.
            reason: The reason for this moderation.
            **kwargs (dict[str, Any]): Any additional keyword arguments;
                will be passed in by the [`sentinel_moderate`][tidegear.sentinel.SentinelCog.sentinel_moderate] function
                and can be accessed using [`get_kwarg`][tidegear.utils.get_kwarg].

        Returns:
            The resulting moderation.
        """
        raise NotImplementedError

    @classmethod
    async def channel_target_handler(
        cls, *, cog: "SentinelCog", ctx: commands.GuildContext, target: GuildChannel, reason: str, **kwargs: Any
    ) -> "Moderation":
        """This method should be overridden by any child classes that can target channels or threads,
            but should retain the same starting keyword arguments.

        Args:
            cog: A cog instance of a Sentinel cog.
            ctx: The context of the command.
            target: The target of the moderation.
            reason: The reason for this moderation.
            **kwargs (dict[str, Any]): Any additional keyword arguments;
                will be passed in by the [`sentinel_moderate`][tidegear.sentinel.SentinelCog.sentinel_moderate] function
                and can be accessed using [`get_kwarg`][tidegear.utils.get_kwarg].

        Returns:
            The resulting moderation.
        """
        raise NotImplementedError

    @classmethod
    async def role_target_handler(
        cls, *, cog: "SentinelCog", ctx: commands.GuildContext, target: discord.Role, reason: str, **kwargs: Any
    ) -> "Moderation":
        """This method should be overridden by any child classes that can target role, but should retain the same keyword arguments.

        Args:
            cog: A cog instance of a Sentinel cog.
            ctx: The context of the command.
            target: The target of the moderation.
            reason: The reason for this moderation.
            **kwargs (dict[str, Any]): Any additional keyword arguments;
                will be passed in by the [`sentinel_moderate`][tidegear.sentinel.SentinelCog.sentinel_moderate] function
                and can be accessed using [`get_kwarg`][tidegear.utils.get_kwarg].

        Returns:
            The resulting moderation.
        """
        raise NotImplementedError

    @classmethod
    async def resolve_handler(cls, cog: "SentinelCog", moderation: "Moderation") -> None:
        """This method should be overridden by any resolvable child classes, but should retain the same keyword arguments.
            If your moderation type should not be resolvable, do not override this.
            This handler should be called after the moderation is marked as resolved within the database.

        Args:
            cog: A cog instance of a Sentinel cog.
            moderation: The moderation being resolved.
        """
        raise NotImplementedError

    @classmethod
    async def expiry_handler(cls, cog: "SentinelCog", moderation: "Moderation") -> None:
        """This method should be overridden by any expirable child classes, but should retain the same keyword arguments.
            If your moderation type should not expire, do not override this.

        Args:
            cog: A cog instance of a Sentinel cog.
            moderation: The moderation that is expiring.
        """
        raise NotImplementedError

    @classmethod
    async def duration_edit_handler(cls, ctx: commands.GuildContext, old_moderation: "Moderation", new_moderation: "Moderation") -> None:
        """This method should be overridden by any child classes with editable durations, but should retain the same keyword arguments.
            If your moderation type's duration should not be editable, do not override this.

        Args:
            ctx: The context that triggered the duration edit.
            old_moderation: The old moderation, from before the `/edit` command was invoked.
            new_moderation: The current state of the moderation.
        """
        raise NotImplementedError


moderation_type_registry: ClassRegistry[ModerationType] = ClassRegistry(attr_name="key", unique=True)
""""""
