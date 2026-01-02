# SPDX-FileCopyrightText: 2025 cswimr <copyright@csw.im>
# SPDX-License-Identifier: MPL-2.0

"""Definitions for the configuration option models."""

import enum
import typing
from typing import Any, ClassVar, Generic, cast

import discord
import pydantic
from red_commons import logging
from redbot.core import config as red_config
from typing_extensions import override

from tidegear.config.exceptions import MalformedConfigError, ReadOnlyConfigError
from tidegear.config.types import JsonableType
from tidegear.pydantic import BaseModel
from tidegear.types import GuildChannel
from tidegear.utils import get_kwarg


class _Validator(BaseModel):
    json_data: pydantic.JsonValue


class ConfigScope(enum.StrEnum):
    """Configuration scopes for use when determining scope for a
        [`GlobalConfigOption`][tidegear.config.options.GlobalConfigOption] or a subclass.

    Checking inheritance for these classes isn't really recommended, as they all inherit
    from the same [`GlobalConfigOption`][tidegear.config.options.GlobalConfigOption] class.
    Instead, you can check the `.scope` of the class in question against this enum to determine its scope.
    """

    GLOBAL = "global"
    GUILD = "guild"
    CHANNEL = "channel"
    ROLE = "role"
    MEMBER = "member"
    USER = "user"
    CUSTOM = "custom"


class GlobalConfigOption(BaseModel, Generic[JsonableType]):
    """A typed representation of a configuration option scoped to the bot's global configuration.

    Changes to this type of configuration option will impact the entire bot,
    so should usually only be modifiable by the bot owner.

    You shouldn't be creating instances of this class manually;
    as [`BaseConfigSchema.init`][tidegear.config.schema.BaseConfigSchema]
    creates instances of this class during schema registration.
    """

    scope: ClassVar[ConfigScope] = ConfigScope.GLOBAL
    """The scope at which this class will register configuration options to through Red's Config module.

    Subclasses of `GlobalConfigOption` will have different scopes,
    allowing you to differentiate between them using the scope classvar.
    """

    model_config: pydantic.ConfigDict = pydantic.ConfigDict(**BaseModel.model_config | {"frozen": True})

    config: red_config.Config = pydantic.Field(exclude=True)
    """The Config class that will be used for operations within this configuration option."""
    key: str
    """The key under which this configuration option's value is stored in Red's config."""
    default: JsonableType
    """The default value for this configuration option.

    Warning:
        You should not use this field to determine the type of the configuration option.
        This is because doing `type(GlobalConfigOption.default)` will return the type of the default value,
        not the annotation of the configuration option itself.
        Use [`.type()`][tidegear.config.GlobalConfigOption.type] instead.
    """
    internal: bool = False
    """Whether or not this option should show up by default in configuration menus. (Does nothing as of writing.)"""
    read_only: bool = False
    """Whether or not this option should be marked as read-only.

    This is intended to prevent accidentally changing the value of the configuration option,
    as you must pass `force=True` to a [`.set()`][tidegear.config.options.GlobalConfigOption.set]
    method in order to set a configuration option that is set to read only.
    """
    help: str | None = None
    """Help message to show within configuration menus.

    If this attribute is not provided to a [`ConfigMeta`][tidegear.config.schema.ConfigMeta] instance,
    It will be automatically generated from an attribute-level docstring.
    If this docstring is also not provided, this will be set to None.
    """
    logger: logging.RedTraceLogger | None = pydantic.Field(default=None, exclude=True)

    @override
    def model_post_init(self, context: Any, /) -> None:
        self.type()

    # This is necessary instead of storing a `type[JsonableType]` field on the class itself,
    # because Pydantic doesn't support parameterized types (i.e. `list[int]`) within `type` annotations.
    @classmethod
    def type(cls) -> type[JsonableType]:
        """Return the concrete type of this configuration option.

        Raises:
            TypeError: If the configuration option has no generic type annotation.
                This will also be raised during schema registration,
                so you don't have to catch this exception during option usage.

        Returns:
            The concrete type of this configuration option.
        """
        annotation = cls.model_fields["default"].annotation
        if annotation is None or annotation is JsonableType:
            msg = "Unspecialized configuration options are not supported. Please add a generic type annotation."
            raise TypeError(msg)
        return cast(type[JsonableType], annotation)

    def _ensure_value_type(self, value: Any) -> red_config.Value | red_config.Group:
        if not isinstance(value, (red_config.Value, red_config.Group)):
            msg = (
                f"The Config attribute for {self.key!r} returned an object with the type {type(value)!r} "
                f"instead of the expected types of ({red_config.Value!r}, {red_config.Group!r})."
            )
            raise TypeError(msg)
        return value

    def _value(self) -> red_config.Value | red_config.Group:
        """Get the underlying [`Value`][redbot.core.config.Value] or [`Group`][redbot.core.config.Group] for this option.

        This function may accept different arguments within subclasses.

        Returns:
            The underlying `Value` for this configuration option.
        """
        value = getattr(self.config, self.key)
        return self._ensure_value_type(value)

    def _serialize(self, obj: Any, /) -> pydantic.JsonValue:
        """Validate a Python object against this option's declared type, then serialize it to a JSON-serializable object.

        Args:
            obj: The Python object to validate and serialize.

        Raises:
            TypeError: If the passed value is valid for this option's type but cannot be expressed as valid JSON data.

        Returns:
            A "serialized" Python object that can then be properly serialized to JSON through [`json.dumps`][] or the like.
                For instance, a Pydantic model would become a raw dictionary,
                containing only elements that can be serialized to JSON.
        """
        validated = self.validate_field("default", obj)
        if isinstance(validated, pydantic.BaseModel):
            serialized = validated.model_dump(mode="json")
        else:
            serialized = self.__pydantic_serializer__.to_python(validated, mode="json", warnings=False)

        try:
            _Validator.validate_field("json_data", serialized)
        except pydantic.ValidationError as err:
            msg = f"Input must be a data type that can be serialized to JSON. Got type {type(serialized)!r}."
            raise TypeError(msg) from err

        return serialized

    def register(self) -> None:
        """Register this config option with Red's Config.

        Raises:
            ValueError: When called on a ConfigOption subclass where the scope is set to `CUSTOM`.
                Use [`CustomConfigOption`][tidegear.config.CustomConfigOption] instead.
        """
        d = {self.key: self._serialize(self.default)}
        match self.scope:
            case ConfigScope.GLOBAL:
                self.config.register_global(**d)
            case ConfigScope.GUILD:
                self.config.register_guild(**d)
            case ConfigScope.CHANNEL:
                self.config.register_channel(**d)
            case ConfigScope.ROLE:
                self.config.register_role(**d)
            case ConfigScope.MEMBER:
                self.config.register_member(**d)
            case ConfigScope.USER:
                self.config.register_user(**d)
            case ConfigScope.CUSTOM:
                msg = "Please use the 'CustomConfigOption' class for registering and handling custom configuration scopes."
                raise ValueError(msg)

    async def __call__(self, *, acquire_lock: bool = True) -> JsonableType:
        """Get a value for this configuration option. Equivalent to [`get`][tidegear.config.options.GlobalConfigOption.get].

        Args:
            acquire_lock: Whether or not to acquire a lock on the configuration option for the duration of the read request.

        Returns:
            The retrieved configuration value.
        """
        return await self.get(acquire_lock=acquire_lock)

    async def get(self, *, acquire_lock: bool = True) -> JsonableType:
        """Get a value for this configuration option.

        Args:
            acquire_lock: Whether or not to acquire a lock on the configuration option for the duration of the read request.

        Returns:
            The retrieved configuration value.
        """
        return await self._get(self._value(), acquire_lock=acquire_lock)

    async def _get(self, c: red_config.Value | red_config.Group, *, acquire_lock: bool = True) -> JsonableType:
        raw = await c(acquire_lock=acquire_lock)
        try:
            return self.validate_field("default", raw)
        except pydantic.ValidationError as err:
            msg = (
                f"Configuration key {self.key!r} has a malformed or corrupted value saved, which is causing validation to fail. "
                "\nIf this error is originating from a cog you do not develop, "
                "and you have NOT modified the configuration file by hand, please report this to the cog author."
                "\nIf you edited the configuration file by hand, it may be in an invalid state. "
                "Try backing up the configuration file and deleting the original. "
                "If that resolves the issue, you should restore from the backup and "
                "attempt to revert the changes that resulted in the file being corrupted. If you choose to attempt this, "
                "the Pydantic validation error information included in this traceback will be helpful."
            )
            raise MalformedConfigError(msg) from err

    async def set(self, value: JsonableType, *, force: bool = False) -> None:
        """Set the configuration option to a specified value.

        Args:
            value: The value to set the configuration option to.
            force: Whether or not to forcefully update read-only configuration options. Don't use this unless you absolutely must.

        Raises:
            ReadOnlyConfigError: If the configuration option being set is read-only, and `force=False` (default).
        """  # noqa: DOC502
        return await self._set(self._value(), value, force=force)

    async def _set(self, c: red_config.Value | red_config.Group, value: JsonableType, *, force: bool = False) -> None:  # noqa: PLR6301
        if self.read_only and not force:
            msg = (
                f"{self.key!r} is read-only, and cannot be modified! "
                "This check can be overridden by passing 'force=True' to '.set()', "
                "but only do this if you really want to change this attribute."
            )
            raise ReadOnlyConfigError(msg)
        await c.set(value=self._serialize(value))

    async def clear(self) -> None:
        """Reset the value of this configuration option to its default."""
        await self._value().clear()


class GuildConfigOption(GlobalConfigOption, Generic[JsonableType]):
    """A typed representation of a configuration option scoped to the bot's guild configuration.

    Changes to this type of configuration option will impact the entirety of the guild in question,
    so should usually only be modifiable by the guild's administrators.

    You shouldn't be creating instances of this class manually;
    as [`BaseConfigSchema.init`][tidegear.config.schema.BaseConfigSchema]
    creates instances of this class during schema registration.
    """

    scope: ClassVar[ConfigScope] = ConfigScope.GUILD
    """The scope at which this class will register configuration options to through Red's Config module.

    Subclasses of `GlobalConfigOption` will have different scopes,
    allowing you to differentiate between them using the scope classvar.
    """

    @override
    def _value(self, guild: discord.Guild | int) -> red_config.Value | red_config.Group:  # pyright: ignore[reportIncompatibleMethodOverride]
        if isinstance(guild, discord.Guild):
            value = getattr(self.config.guild(guild), self.key)
        else:
            value = getattr(self.config.guild_from_id(guild), self.key)
        return self._ensure_value_type(value)

    @override
    async def __call__(self, guild: discord.Guild | int, *, acquire_lock: bool = True) -> JsonableType:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Get a value for this configuration option. Equivalent to [`get`][tidegear.config.options.GuildConfigOption.get].

        Args:
            guild: The guild to retrieve a configuration value for.
            acquire_lock: Whether or not to acquire a lock on the configuration option for the duration of the read request.

        Returns:
            The retrieved configuration value.
        """
        return await self.get(guild, acquire_lock=acquire_lock)

    @override
    async def get(self, guild: discord.Guild | int, *, acquire_lock: bool = True) -> JsonableType:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Get a value for this configuration option.

        Args:
            guild: The guild to retrieve a configuration value for.
            acquire_lock: Whether or not to acquire a lock on the configuration option for the duration of the read request.

        Returns:
            The retrieved configuration value.
        """
        return await self._get(self._value(guild), acquire_lock=acquire_lock)

    @override
    async def set(self, guild: discord.Guild | int, value: JsonableType, *, force: bool = False) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Set the configuration option to a specified value.

        Args:
            guild: The guild to set the configuration option for.
            value: The value to set the configuration option to.
            force: Whether or not to forcefully update read-only configuration options. Don't use this unless you absolutely must.

        Raises:
            ReadOnlyConfigError: If the configuration option being set is read-only, and `force=False` (default).
        """  # noqa: DOC502
        return await self._set(self._value(guild), value, force=force)

    @override
    async def clear(self, guild: discord.Guild | int) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Reset the value of this configuration option to its default.

        Args:
            guild: The guild to clear the configuration option for.
        """
        await self._value(guild).clear()


class ChannelConfigOption(GlobalConfigOption, Generic[JsonableType]):
    """A typed representation of a configuration option scoped to the bot's channel configuration.

    Changes to this type of configuration option will impact anyone who uses the channel in question,
    so should usually only be modifiable by individuals who have Manage Channels or similar in the channel.

    You shouldn't be creating instances of this class manually;
    as [`BaseConfigSchema.init`][tidegear.config.schema.BaseConfigSchema]
    creates instances of this class during schema registration.
    """

    scope: ClassVar[ConfigScope] = ConfigScope.CHANNEL
    """The scope at which this class will register configuration options to through Red's Config module.

    Subclasses of `GlobalConfigOption` will have different scopes,
    allowing you to differentiate between them using the scope classvar.
    """

    @override
    def _value(self, channel: GuildChannel | int) -> red_config.Value | red_config.Group:  # pyright: ignore[reportIncompatibleMethodOverride]
        if isinstance(channel, GuildChannel):
            value = getattr(self.config.channel(channel), self.key)
        else:
            value = getattr(self.config.channel_from_id(channel), self.key)
        return self._ensure_value_type(value)

    @override
    async def __call__(self, channel: GuildChannel | int, *, acquire_lock: bool = True) -> JsonableType:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Get a value for this configuration option. Equivalent to [`get`][tidegear.config.options.ChannelConfigOption.get].

        Args:
            channel: The channel to retrieve a configuration value for.
            acquire_lock: Whether or not to acquire a lock on the configuration option for the duration of the read request.

        Returns:
            The retrieved configuration value.
        """
        return await self.get(channel, acquire_lock=acquire_lock)

    @override
    async def get(self, channel: GuildChannel | int, *, acquire_lock: bool = True) -> JsonableType:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Get a value for this configuration option.

        Args:
            channel: The channel to retrieve a configuration value for.
            acquire_lock: Whether or not to acquire a lock on the configuration option for the duration of the read request.

        Returns:
            The retrieved configuration value.
        """
        return await self._get(self._value(channel), acquire_lock=acquire_lock)

    @override
    async def set(self, channel: GuildChannel | int, value: JsonableType, *, force: bool = False) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Set the configuration option to a specified value.

        Args:
            channel: The channel to set the configuration option for.
            value: The value to set the configuration option to.
            force: Whether or not to forcefully update read-only configuration options. Don't use this unless you absolutely must.

        Raises:
            ReadOnlyConfigError: If the configuration option being set is read-only, and `force=False` (default).
        """  # noqa: DOC502
        return await self._set(self._value(channel), value, force=force)

    @override
    async def clear(self, channel: GuildChannel | int) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Reset the value of this configuration option to its default.

        Args:
            channel: The channel to clear the configuration option for.
        """
        await self._value(channel).clear()


class RoleConfigOption(GlobalConfigOption, Generic[JsonableType]):
    """A typed representation of a configuration option scoped to the bot's role configuration.

    Changes to this type of configuration option will impact anyone who has the role in question,
    so should usually only be modifiable by individuals who have Manage Roles or similar.

    You shouldn't be creating instances of this class manually;
    as [`BaseConfigSchema.init`][tidegear.config.schema.BaseConfigSchema]
    creates instances of this class during schema registration.
    """

    scope: ClassVar[ConfigScope] = ConfigScope.ROLE
    """The scope at which this class will register configuration options to through Red's Config module.

    Subclasses of `GlobalConfigOption` will have different scopes,
    allowing you to differentiate between them using the scope classvar.
    """

    @override
    def _value(self, role: discord.Role | int) -> red_config.Value | red_config.Group:  # pyright: ignore[reportIncompatibleMethodOverride]
        if isinstance(role, discord.Role):
            value = getattr(self.config.role(role), self.key)
        else:
            value = getattr(self.config.role_from_id(role), self.key)
        return self._ensure_value_type(value)

    @override
    async def __call__(self, role: discord.Role | int, *, acquire_lock: bool = True) -> JsonableType:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Get a value for this configuration option. Equivalent to [`get`][tidegear.config.options.RoleConfigOption.get].

        Args:
            role: The role to retrieve a configuration value for.
            acquire_lock: Whether or not to acquire a lock on the configuration option for the duration of the read request.

        Returns:
            The retrieved configuration value.
        """
        return await self.get(role, acquire_lock=acquire_lock)

    @override
    async def get(self, role: discord.Role | int, *, acquire_lock: bool = True) -> JsonableType:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Get a value for this configuration option.

        Args:
            role: The role to retrieve a configuration value for.
            acquire_lock: Whether or not to acquire a lock on the configuration option for the duration of the read request.

        Returns:
            The retrieved configuration value.
        """
        return await self._get(self._value(role), acquire_lock=acquire_lock)

    @override
    async def set(self, role: discord.Role | int, value: JsonableType, *, force: bool = False) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Set the configuration option to a specified value.

        Args:
            role: The role to set the configuration option for.
            value: The value to set the configuration option to.
            force: Whether or not to forcefully update read-only configuration options. Don't use this unless you absolutely must.

        Raises:
            ReadOnlyConfigError: If the configuration option being set is read-only, and `force=False` (default).
        """  # noqa: DOC502
        return await self._set(self._value(role), value, force=force)

    @override
    async def clear(self, role: discord.Role | int) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Reset the value of this configuration option to its default.

        Args:
            role: The role to clear the configuration option for.
        """
        await self._value(role).clear()


class MemberConfigOption(GlobalConfigOption, Generic[JsonableType]):
    """A typed representation of a configuration option scoped to the bot's member configuration.

    This differs from [`UserConfigOption`][tidegear.config.options.UserConfigOption] in that an individual user can
    have different settings for this option depending on the guild they're currently interacting with the bot in.
    This has the side effect of meaning that this configuration option will/should have no effect outside of a guild context.

    You shouldn't be creating instances of this class manually;
    as [`BaseConfigSchema.init`][tidegear.config.schema.BaseConfigSchema]
    creates instances of this class during schema registration.
    """

    scope: ClassVar[ConfigScope] = ConfigScope.MEMBER
    """The scope at which this class will register configuration options to through Red's Config module.

    Subclasses of `GlobalConfigOption` will have different scopes,
    allowing you to differentiate between them using the scope classvar.
    """

    @override
    def _value(self, member: discord.Member | int, guild: discord.Guild | int | None) -> red_config.Value | red_config.Group:  # pyright: ignore[reportIncompatibleMethodOverride]
        if isinstance(member, int):
            if not guild:
                msg = "A 'discord.Guild' object or a Discord guild ID is required when fetching members via ID."
                raise ValueError(msg)
            if isinstance(guild, discord.Guild):
                guild = guild.id
            value = getattr(self.config.member_from_ids(guild_id=guild, member_id=member), self.key)
        else:
            value = getattr(self.config.member(member), self.key)
        return self._ensure_value_type(value)

    @typing.overload
    async def __call__(self, member: discord.Member, *, acquire_lock: bool = ...) -> JsonableType: ...
    @typing.overload
    async def __call__(self, member: int, *, guild: discord.Guild | int, acquire_lock: bool = ...) -> JsonableType: ...

    @override
    async def __call__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, member: discord.Member | int, *, guild: discord.Guild | int | None = None, acquire_lock: bool = True
    ) -> JsonableType:
        """Get a value for this configuration option. Equivalent to [`get`][tidegear.config.options.MemberConfigOption.get].

        Args:
            member: The member to retrieve a configuration value for.
            guild: The guild to resolve the member from if passing a member ID.
            acquire_lock: Whether or not to acquire a lock on the configuration option for the duration of the read request.

        Raises:
            ValueError: If an `int` is passed for `member`, and no corresponding `guild` is passed.

        Returns:
            The retrieved configuration value.
        """  # noqa: DOC502
        return await self._get(self._value(member, guild), acquire_lock=acquire_lock)

    @typing.overload
    async def get(self, member: discord.Member, *, acquire_lock: bool = ...) -> JsonableType: ...
    @typing.overload
    async def get(self, member: int, *, guild: discord.Guild | int, acquire_lock: bool = ...) -> JsonableType: ...

    @override
    async def get(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, member: discord.Member | int, *, guild: discord.Guild | int | None = None, acquire_lock: bool = True
    ) -> JsonableType:
        """Get a value for this configuration option.

        Args:
            member: The member to retrieve a configuration value for.
            guild: The guild to resolve the member from if passing a member ID.
            acquire_lock: Whether or not to acquire a lock on the configuration option for the duration of the read request.

        Raises:
            ValueError: If an `int` is passed for `member`, and no corresponding `guild` is passed.

        Returns:
            The retrieved configuration value.
        """  # noqa: DOC502
        return await self._get(self._value(member, guild), acquire_lock=acquire_lock)

    @typing.overload
    async def set(self, member: discord.Member, value: JsonableType, *, force: bool = ...) -> None: ...
    @typing.overload
    async def set(self, member: int, value: JsonableType, *, guild: discord.Guild | int, force: bool = ...) -> None: ...

    @override
    async def set(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, member: discord.Member | int, value: JsonableType, *, guild: discord.Guild | int | None = None, force: bool = False
    ) -> None:
        """Set the configuration option to a specified value.

        Args:
            member: The member to set the configuration option for.
            value: The value to set the configuration option to.
            guild: The guild to resolve the member from if passing a member ID.
            force: Whether or not to forcefully update read-only configuration options. Don't use this unless you absolutely must.

        Raises:
            ReadOnlyConfigError: If the configuration option being set is read-only, and `force=False` (default).
            ValueError: If an `int` is passed for `member`, and no corresponding `guild` is passed.
        """  # noqa: DOC502
        return await self._set(self._value(member, guild), value, force=force)

    @typing.overload
    async def clear(self, member: discord.Member) -> None: ...
    @typing.overload
    async def clear(self, member: int, guild: discord.Guild | int) -> None: ...

    @override
    async def clear(self, member: discord.Member | int, guild: discord.Guild | int | None = None) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Reset the value of this configuration option to its default.

        Args:
            member: The member to clear the configuration option for.
            guild: The guild to resolve the member from if passing a member ID.

        Raises:
            ValueError: If an `int` is passed for `member`, and no corresponding `guild` is passed.
        """  # noqa: DOC502
        await self._value(member, guild).clear()


class UserConfigOption(GlobalConfigOption, Generic[JsonableType]):
    """A typed representation of a configuration option scoped to the bot's user configuration.

    You shouldn't be creating instances of this class manually;
    as [`BaseConfigSchema.init`][tidegear.config.schema.BaseConfigSchema]
    creates instances of this class during schema registration.
    """

    scope: ClassVar[ConfigScope] = ConfigScope.USER
    """The scope at which this class will register configuration options to through Red's Config module.

    Subclasses of `GlobalConfigOption` will have different scopes,
    allowing you to differentiate between them using the scope classvar.
    """

    @override
    def _value(self, user: discord.abc.User | int) -> red_config.Value | red_config.Group:  # pyright: ignore[reportIncompatibleMethodOverride]
        if isinstance(user, discord.abc.User):
            value = getattr(self.config.user(user), self.key)
        else:
            value = getattr(self.config.user_from_id(user), self.key)
        return self._ensure_value_type(value)

    @override
    async def __call__(self, user: discord.abc.User | int, *, acquire_lock: bool = True) -> JsonableType:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Get a value for this configuration option. Equivalent to [`get`][tidegear.config.options.UserConfigOption.get].

        Args:
            user: The user to retrieve a configuration value for.
            acquire_lock: Whether or not to acquire a lock on the configuration option for the duration of the read request.

        Returns:
            The retrieved configuration value.
        """
        return await self.get(user, acquire_lock=acquire_lock)

    @override
    async def get(self, user: discord.abc.User | int, *, acquire_lock: bool = True) -> JsonableType:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Get a value for this configuration option.

        Args:
            user: The user to retrieve a configuration value for.
            acquire_lock: Whether or not to acquire a lock on the configuration option for the duration of the read request.

        Returns:
            The retrieved configuration value.
        """
        return await self._get(self._value(user), acquire_lock=acquire_lock)

    @override
    async def set(self, user: discord.abc.User | int, value: JsonableType, *, force: bool = False) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Set the configuration option to a specified value.

        Args:
            user: The user to set the configuration option for.
            value: The value to set the configuration option to.
            force: Whether or not to forcefully update read-only configuration options. Don't use this unless you absolutely must.

        Raises:
            ReadOnlyConfigError: If the configuration option being set is read-only, and `force=False` (default).
        """  # noqa: DOC502
        return await self._set(self._value(user), value, force=force)

    @override
    async def clear(self, user: discord.abc.User | int) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Reset the value of this configuration option to its default.

        Args:
            user: The user to clear the configuration option for.
        """
        await self._value(user).clear()


class CustomConfigGroup(BaseModel):
    """A metadata model that defines a "Group" for use with [`CustomConfigOption`][tidegear.config.options.CustomConfigOption]."""

    name: str
    """The name of the custom group. Corresponds to `group_identifier` in [`Config.custom`][redbot.core.config.Config.custom]."""
    identifiers: list[str]
    """A list of identifier names for this custom group.

    Danger:
        The order of this list does matter, and changing it is a breaking change that should result in your
        [`BaseConfigSchema.version`][tidegear.config.schema.BaseConfigSchema.version] being incremented.

        This is because the identifiers are passed to [`Config.custom`][redbot.core.config.Config.custom]
        in order of the identifier names in this list. So, changing `["abc", "xyz"]` to `["xyz", "abc"]` will
        make [`CustomConfigOption`][tidegear.config.options.CustomConfigOption]'s methods resolve to completely different data.

        Do note, however, that the order of keyword arguments *within
        [`CustomConfigOption`][tidegear.config.options.CustomConfigOption]'s methods* does not matter.
        So long as there is a keyword argument for each identifier in this list,
        changing the order of those keyword arguments will not result in accessing different data.

    These identifiers are used as keyword argument names in
    [`CustomConfigOption`][tidegear.config.options.CustomConfigOption] methods.

    For example, if you define:
    ```py
    CustomConfigGroup(name="Example", identifiers=["abc", "xyz"])
    ```
    Then:
    ```py
    await CustomConfigOption().get(abc="unique", xyz="123")
    ```
    becomes the required API shape.

    Unfortunately, this is difficult / impossible to represent in a way where type-checkers can validate keyword argument names.
    """


class CustomConfigOption(GlobalConfigOption, Generic[JsonableType]):
    """A typed representation of a configuration option scoped to a specific custom group.

    This differs from other configuration option types in that you must specify a
    [`CustomConfigGroup`][tidegear.config.options.CustomConfigGroup] in your type annotation when
    defining an option of this type on your [configuration schema][tidegear.config.schema.BaseConfigSchema].

    See the [Red-DiscordBot](https://docs.discord.red/en/stable/framework_config.html#custom-groups)
    documentation for more information on how this works internally.

    You shouldn't be creating instances of this class manually;
    as [`BaseConfigSchema.init`][tidegear.config.schema.BaseConfigSchema]
    creates instances of this class during schema registration.
    """

    scope: ClassVar[ConfigScope] = ConfigScope.CUSTOM
    """The scope at which this class will register configuration options to through Red's Config module.

    Subclasses of `GlobalConfigOption` will have different scopes,
    allowing you to differentiate between them using the scope classvar.
    """

    group: CustomConfigGroup
    """The group that this configuration option uses for registration and retrivial."""

    @override
    def register(self) -> None:
        """Register this config option with Red's Config."""
        self.config.init_custom(group_identifier=self.group.name, identifier_count=len(self.group.identifiers))
        self.config.register_custom(group_identifier=self.group.name, **{self.key: self._serialize(self.default)})

    @override
    def _value(self, **identifiers: str) -> red_config.Value | red_config.Group:
        identifier_values: list[str] = [get_kwarg(identifiers, i, expected_type=str) for i in self.group.identifiers]
        attr = self.config.custom(self.group.name, *identifier_values)
        value = getattr(attr, self.key)
        return self._ensure_value_type(value)

    @override
    async def __call__(self, *, acquire_lock: bool = True, **identifiers: str) -> JsonableType:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Get a value for this configuration option. Equivalent to [`get`][tidegear.config.options.CustomConfigOption.get].

        Args:
            acquire_lock: Whether or not to acquire a lock on the configuration option for the duration of the read request.
            **identifiers: The identifiers to get a value for.

        Returns:
            The retrieved configuration value.
        """
        return await self.get(acquire_lock=acquire_lock, **identifiers)

    @override
    async def get(self, *, acquire_lock: bool = True, **identifiers: str) -> JsonableType:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Get a value for this configuration option.

        Args:
            acquire_lock: Whether or not to acquire a lock on the configuration option for the duration of the read request.
            **identifiers: The identifiers to get a value for.

        Returns:
            The retrieved configuration value.
        """
        return await self._get(self._value(**identifiers), acquire_lock=acquire_lock)

    @override
    async def set(self, value: JsonableType, *, force: bool = False, **identifiers: str) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Set the configuration option to a specified value.

        Args:
            value: The value to set the configuration option to.
            force: Whether or not to forcefully update read-only configuration options. Don't use this unless you absolutely must.
            **identifiers: The identifiers to set a value for.

        Raises:
            ReadOnlyConfigError: If the configuration option being set is read-only, and `force=False` (default).
        """  # noqa: DOC502
        return await self._set(self._value(**identifiers), value, force=force)

    @override
    async def clear(self, **identifiers: str) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Reset the value of this configuration option to its default.

        Args:
            **identifiers: The identifiers to clear the value for.
        """
        await self._value(**identifiers).clear()
