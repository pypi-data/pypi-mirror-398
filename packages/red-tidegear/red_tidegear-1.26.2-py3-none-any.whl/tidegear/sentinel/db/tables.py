# SPDX-FileCopyrightText: 2025 cswimr <copyright@csw.im>
# SPDX-License-Identifier: MPL-2.0
"""Sentinel database table models."""

from abc import abstractmethod
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Literal, Never, Self, overload

import discord
import orjson
import rich.repr
from class_registry.base import RegistryKeyError
from piccolo.columns import Column
from piccolo.columns.column_types import JSON, Boolean, ForeignKey, Integer, Serial, Text, Timestamptz, Varchar
from piccolo.columns.defaults.timestamptz import TimestamptzNow
from piccolo.table import Table as BaseTable
from redbot.core.bot import Red
from typing_extensions import override

from tidegear.exceptions import NotFoundError
from tidegear.sentinel.exceptions import NotReadyError, UnsetError, UpsertError
from tidegear.sentinel.moderation_type import ModerationType, moderation_type_registry
from tidegear.types import GuildChannel

if TYPE_CHECKING:
    from tidegear.sentinel.cog import SentinelCog


class Table(BaseTable):
    """Subclass of Piccolo's Table class that allows for easier pretty printing of table rows."""

    @override
    def __str__(self) -> str:
        return self.__repr__()

    @override
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.to_dict()})"

    def __rich_repr__(self) -> rich.repr.Result:  # noqa: D105, PLW3201
        for column, value in self.to_dict().items():
            yield column, value

    __rich_repr__.angular = True  # pyright: ignore[reportFunctionMemberAccess]

    def is_null(self) -> bool:
        """Check if the current row is null, or empty.
        Helps with weirdness related to the Piccolo [`all_related()`][piccolo.table.Table.all_related] function.

        Returns:
            Whether or not all entries within the current row are null.
        """
        for value in self.to_dict().values():
            if value is not None:
                return False
        return True

    @overload
    def json(
        self,
        *,
        columns: list[Column] | None = None,
        string: Literal[False] = False,
        encoding: str = ...,
        indent: bool = ...,
        options: int = ...,
    ) -> bytes: ...

    @overload
    def json(
        self,
        *,
        columns: list[Column] | None = None,
        string: Literal[True],
        encoding: str = ...,
        indent: bool = ...,
        options: int = ...,
    ) -> str: ...

    def json(
        self,
        *,
        columns: list[Column] | None = None,
        string: bool = False,
        encoding: str = "utf-8",
        indent: bool = False,
        options: int = 0,
    ) -> bytes | str:
        """Get a JSON representation of a table object.

        Utilizes a custom serializer that supports the following types, in addition to those supported
        by the [`orjson`](https://github.com/ijl/orjson?tab=readme-ov-file#serialize) library.

        - [`Table`][tidegear.sentinel.db.tables.Table]

        Args:
            columns: The columns to include in the output. Only passed columns will be included, does nothing if not provided.
            string: Whether or not to return a string. Avoids a manual decode step.
            encoding: The encoding to use to decode the bytes returned by `orjson.dumps()`.
            indent: Whether or not to indent the output JSON. Don't use in performance-sensitive environments.
            options: Additional [options](https://github.com/ijl/orjson?tab=readme-ov-file#option) to pass into `orjson.dumps()`.

        Returns:
            (bytes): When `string` is `False,` the resulting JSON in bytes. Use [`.decode`][bytes.decode] to get a usable string.
            (str): When `string` is `True,` the resulting JSON in a string.
        """
        if indent:
            options |= orjson.OPT_INDENT_2

        if columns is not None:
            table_dictionary = self.to_dict(*columns)
        else:
            table_dictionary = self.to_dict()

        dump = orjson.dumps(table_dictionary, default=self._json_serializer, option=options)

        if string:
            return dump.decode(encoding)
        return dump

    @classmethod
    def _json_serializer(cls, obj: object) -> object:
        if isinstance(obj, Table):
            return cls._clean_foreign_keys(obj.to_dict())
        if isinstance(obj, Decimal):
            return float(obj)
        msg = f"Type {type(obj)} is not serializable!"
        raise TypeError(msg)

    @classmethod
    def _clean_foreign_keys(cls, obj: dict) -> dict:
        cleaned = {}
        for k, v in obj.items():
            if isinstance(v, dict):
                nested = cls._clean_foreign_keys(v)
                if all(value is None for value in nested.values()):
                    cleaned[k] = None
                else:
                    cleaned[k] = nested
            else:
                cleaned[k] = v
        return cleaned


class AbstractPartial:
    """An abstract class for Partials, detailing methods that should always be implemented within a Partial.

    Methods like `upsert()` or `fetch()` aren't included here,
    because they will have unique function signatures depending on the Partial being implemented.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the partial's last known name according to the internal database."""
        ...

    @property
    @abstractmethod
    def mention(self) -> str:
        """Return a string that, when posted within a Discord message, will be rendered as a mention of that object.
        May return the object's name instead if the object does not support mentions, e.g. guilds.
        """
        ...

    @property
    @abstractmethod
    def discord_object(self) -> discord.Object:
        """Return the partial's Discord ID, wrapped in a [`discord.Object`][] of the appropriate type."""
        ...

    @property
    @abstractmethod
    def discord_id(self) -> int:
        """Return the partial's Discord ID according to the internal database."""
        ...

    @abstractmethod
    def in_guild(self, guild: discord.Guild) -> bool:
        """Return whether or not the partial is a member of a given [`discord.Guild`][]."""
        ...


class PartialGuild(Table, AbstractPartial):
    """A model representing a guild stored within the internal database.

    Attributes: Columns:
        id: The internal ID of the guild within the database. This is NOT the guild's Discord ID.
        guild_id: The Discord ID of the guild.
            Please consider using [`.discord_id`][tidegear.sentinel.AbstractPartial.discord_id] instead of this.
        last_known_name: The name of the guild, as of the last time the guild was upserted.
        updated_at: The last time the guild was upserted.
    """

    id: Serial = Serial(index=True, primary_key=True)
    guild_id: Integer = Integer(unique=True, index=True)
    last_known_name: Varchar = Varchar(default="Unknown Guild", length=100)
    updated_at: Timestamptz = Timestamptz(auto_update=TimestamptzNow().python)

    @property
    @override
    def name(self) -> str:
        return self.last_known_name

    @property
    @override
    def mention(self) -> str:
        return self.last_known_name

    @property
    @override
    def discord_object(self) -> discord.Object:
        return discord.Object(id=self.guild_id, type=discord.Guild)

    @property
    @override
    def discord_id(self) -> int:
        return self.guild_id

    @override
    def in_guild(self, guild: discord.Guild) -> bool:
        return guild.id == self.discord_id

    @overload
    async def fetch(self, bot: Red, *, fetch: Literal[True] = ..., upsert: bool = ...) -> discord.Guild: ...

    @overload
    async def fetch(self, bot: Red, *, fetch: Literal[False] = False, upsert: bool = ...) -> discord.Guild | None: ...

    async def fetch(self, bot: Red, *, fetch: bool = False, upsert: bool = True) -> discord.Guild | None:
        """Retrieve a Guild object for this PartialGuild.

        Only use this if you need more information than is stored within the database.

        Args:
            bot: The bot object to use to retrieve the guild.
            fetch: Whether or not to attempt to fetch the guild from Discord's API if the guild is not in the internal cache.
                Avoid using this unless absolutely necessary,
                as this endpoint is ratelimited and introduces additional runtime cost.
            upsert: Whether or not to automatically upsert the retrieved Guild object into the database.
                This introduces a minimal runtime cost if you're already
                fetching from the Discord API, and should usually be done.

        Returns:
            The retrieved guild object, or None if `fetch` is `False` and the guild is not in the bot's internal cache.
        """
        guild = bot.get_guild(self.guild_id)
        if fetch and not guild:
            guild = await bot.fetch_guild(self.guild_id)
        if upsert and guild:
            await self.upsert(guild)
        return guild

    @classmethod
    async def upsert(cls, guild: discord.Guild) -> Self:
        """Insert or update a row in the database based on metadata from a Guild object.

        Args:
            guild: The guild object to upsert.

        Raises:
            UpsertError: If upserting fails for some reason.

        Returns:
            (PartialGuild): The resulting PartialGuild object.
        """
        query = cls.objects().where(cls.guild_id == guild.id).first()
        if fetched_guild := await query:
            await fetched_guild.update_self(values={cls.last_known_name: guild.name})
            return fetched_guild

        await cls.insert(cls(_data={cls.guild_id: guild.id, cls.last_known_name: guild.name}))
        if result := await query:
            return result
        msg = "Upsert operation failed!"
        raise UpsertError(msg)


class PartialUser(Table, AbstractPartial):
    """A model representing a user stored within the internal database.

    Attributes: Columns:
        id: The internal ID of the user within the database. This is NOT the user's Discord ID.
        user_id: The Discord ID of the user.
            Please consider using [`.discord_id`][tidegear.sentinel.AbstractPartial.discord_id] instead of this.
        last_known_name: The name of the user, as of the last time the guild was upserted.
        discriminator: The user's discriminator, will usually be either `None` or `0`.
        updated_at: The last time the user was upserted.
    """

    id: Serial = Serial(index=True, primary_key=True)
    user_id: Integer = Integer(unique=True, index=True)
    last_known_name: Varchar = Varchar(default="Unknown User", length=32)
    discriminator: Integer = Integer(null=True)
    updated_at: Timestamptz = Timestamptz(auto_update=TimestamptzNow().python)

    @property
    @override
    def name(self) -> str:
        if self.discriminator and self.discriminator != 0:
            return f"{self.last_known_name}#{self.discriminator}"
        return self.last_known_name

    @property
    @override
    def mention(self) -> str:
        return f"<@{self.user_id}>"

    @property
    @override
    def discord_object(self) -> discord.Object:
        return discord.Object(id=self.user_id, type=discord.User)

    @property
    @override
    def discord_id(self) -> int:
        return self.discord_object.id

    @override
    def in_guild(self, guild: discord.Guild) -> bool:
        return bool(guild.get_member(self.discord_id))

    @overload
    async def fetch(self, fetcher: Red, *, fetch: Literal[True] = ..., upsert: bool = ...) -> discord.User: ...
    @overload
    async def fetch(self, fetcher: Red, *, fetch: Literal[False] = False, upsert: bool = ...) -> discord.User | None: ...
    @overload
    async def fetch(self, fetcher: discord.Guild, *, fetch: Literal[True] = ..., upsert: bool = ...) -> discord.Member: ...
    @overload
    async def fetch(
        self, fetcher: discord.Guild, *, fetch: Literal[False] = False, upsert: bool = ...
    ) -> discord.Member | None: ...

    async def fetch(
        self, fetcher: Red | discord.Guild, *, fetch: bool = False, upsert: bool = True
    ) -> discord.User | discord.Member | None:
        """Retrieve a User or Member object for this PartialUser.

        Only use this if you need more information than is stored within the database.

        Args:
            fetcher: The object to use to retrieve the User or Member.
            fetch: Whether or not to attempt to fetch the user from Discord's API if the user is not in the internal cache.
                Avoid using this unless absolutely necessary,
                as this endpoint is ratelimited and introduces additional runtime cost.
            upsert: Whether or not to automatically upsert the retrieved User / Member object into the database.
                This introduces a minimal runtime cost if you're already
                fetching from the Discord API, and should usually be done.

        Raises:
            TypeError: Raised if `fetcher` is not a supported type.

        Returns:
            The retrieved User / Member object, or None if `fetch` is `False` and the user is not in the bot's internal cache.
        """
        if isinstance(fetcher, Red):
            user = fetcher.get_user(self.user_id)
            if fetch and not user:
                user = await fetcher.fetch_user(self.user_id)
        elif isinstance(fetcher, discord.Guild):
            user = fetcher.get_member(self.user_id)
            if fetch and not user:
                user = await fetcher.fetch_member(self.user_id)
        else:
            msg = f"Unsupported fetcher type: {type(fetcher).__name__}"
            raise TypeError(msg)

        if upsert and user:
            await self.upsert(user)
        return user

    @classmethod
    async def upsert(cls, user: discord.abc.User) -> Self:
        """Insert or update a row in the database based on metadata from a User object.

        Args:
            user: The User object to upsert.

        Raises:
            UpsertError: If upserting fails for some reason.

        Returns:
            (PartialUser): The resulting PartialUser object.
        """
        query = cls.objects().where(cls.user_id == user.id).first()
        if fetched_user := await query:
            await fetched_user.update_self(values={cls.last_known_name: user.name, cls.discriminator: int(user.discriminator)})
            return fetched_user

        await cls.insert(
            cls(_data={cls.user_id: user.id, cls.last_known_name: user.name, cls.discriminator: int(user.discriminator)})
        )
        if result := await query:
            return result
        msg = "Upsert operation failed!"
        raise UpsertError(msg)


class PartialChannel(Table, AbstractPartial):
    """A model representing a channel stored within the internal database.

    Attributes: Columns:
        id: The internal ID of the channel within the database. This is NOT the channel's Discord ID.
        guild_id: The internal ID of the guild this channel is parented to within the database.
            This is NOT the guild's Discord ID.
        channel_id: The Discord ID of the channel.
            Please consider using [`.discord_id`][tidegear.sentinel.AbstractPartial.discord_id] instead of this.
        last_known_name: The name of the channel, as of the last time the channel was upserted.
        updated_at: The last time the channel was upserted.
    """

    id: Serial = Serial(index=True, primary_key=True)
    guild_id: ForeignKey[PartialGuild] = ForeignKey(references=PartialGuild, null=False)
    channel_id: Integer = Integer(index=True)
    last_known_name: Varchar = Varchar(default="Unknown Channel", length=100)
    updated_at: Timestamptz = Timestamptz(auto_update=TimestamptzNow().python)

    @property
    @override
    def name(self) -> str:
        return f"#{self.last_known_name}"

    @property
    @override
    def mention(self) -> str:
        return f"<#{self.channel_id}>"

    @property
    @override
    def discord_object(self) -> discord.Object:
        return discord.Object(id=self.channel_id, type=discord.abc.GuildChannel)

    @property
    @override
    def discord_id(self) -> int:
        return self.discord_object.id

    @override
    def in_guild(self, guild: discord.Guild) -> bool:
        return bool(guild.get_channel_or_thread(self.discord_id))

    @overload
    async def fetch(self, bot: Red, *, fetch: Literal[True] = ..., upsert: bool = ...) -> GuildChannel: ...

    @overload
    async def fetch(self, bot: Red, *, fetch: Literal[False] = False, upsert: bool = ...) -> GuildChannel | None: ...

    async def fetch(self, bot: Red, *, fetch: bool = False, upsert: bool = True) -> GuildChannel | None:
        """Retrieve a GuildChannel or Thread object for this PartialChannel.

        Only use this if you need more information than is stored within the database.

        Args:
            bot: The bot object to use to retrieve the channel.
            fetch: Whether or not to attempt to fetch the channel from Discord's API if the channel is not in the internal cache.
                Avoid using this unless absolutely necessary,
                as this endpoint is ratelimited and introduces additional runtime cost.
            upsert: Whether or not to automatically upsert the retrieved GuildChannel / Thread object into the database.
                This introduces a minimal runtime cost if you're already
                fetching from the Discord API, and should usually be done.

        Returns:
            The retrieved channel object, or None if `fetch` is `False`
            and the guild or channel is not in the bot's internal cache.
        """
        partial_guild = await self.guild()
        if not (guild := await partial_guild.fetch(bot, fetch=fetch)):
            return None

        channel = guild.get_channel_or_thread(self.channel_id)
        if fetch and not channel:
            channel = await guild.fetch_channel(self.channel_id)

        if upsert and channel:
            await self.upsert(channel)
        return channel

    async def guild(self, /, *, cache: bool = True) -> PartialGuild:
        """Retrieve the [`PartialGuild`][tidegear.sentinel.PartialGuild] that this channel belongs to.

        Args:
            cache: Whether or not to try an internal cache before querying the database.
                This will have no effect if you haven't ran this method yet on this PartialChannel instance.

        Raises:
            NotFoundError: If the guild tied to this channel no longer exists in the database.
                This should be reported as a bug if it occurs,
                as there's a foreign key constraint that should prevent this on the table itself.

        Returns:
            The guild object tied to this channel.
        """
        if cache and "_guild_obj" in self.__dict__:
            return self._guild_obj

        if isinstance(self.guild_id, PartialGuild):  # support both initialized PartialGuild objects and raw ints
            guild = self.guild_id
        elif not (
            guild := await PartialGuild.objects(PartialGuild.all_related()).where(PartialGuild.id == self.guild_id).first()
        ):
            msg = f"No guild exists in the database with id {self.guild_id}!"
            raise NotFoundError(msg)

        self._guild_obj = guild
        return self._guild_obj

    @classmethod
    async def upsert(cls, channel: GuildChannel) -> Self:
        """Insert or update a row in the database based on metadata from a GuildChannel or Thread object.

        Args:
            channel: The channel object to upsert.

        Raises:
            UpsertError: If upserting fails for some reason.

        Returns:
            (PartialChannel): The resulting PartialChannel object.
        """
        guild = await PartialGuild.upsert(guild=channel.guild)

        query = cls.objects(cls.all_related()).where(cls.channel_id == channel.id, cls.guild_id.id == guild.id).first()
        if fetched_channel := await query:
            await fetched_channel.update_self(values={cls.last_known_name: channel.name})
            fetched_channel._guild_obj = guild  # noqa: SLF001
            return fetched_channel

        await cls.insert(cls(_data={cls.guild_id: guild.id, cls.channel_id: channel.id, cls.last_known_name: channel.name}))

        if result := await query:
            result._guild_obj = guild  # noqa: SLF001
            return result
        msg = "Upsert operation failed!"
        raise UpsertError(msg)


class PartialRole(Table, AbstractPartial):
    """A model representing a role stored within the internal database.

    Attributes: Columns:
        id: The internal ID of the role within the database. This is NOT the role's Discord ID.
        guild_id: The internal ID of the guild this role is parented to within the database. This is NOT the guild's Discord ID.
        role_id: The Discord ID of the role.
            Please consider using [`.discord_id`][tidegear.sentinel.AbstractPartial.discord_id] instead of this.
        last_known_name: The name of the role, as of the last time the role was upserted.
        updated_at: The last time the role was upserted.
    """

    id: Serial = Serial(index=True, primary_key=True)
    guild_id: ForeignKey[PartialGuild] = ForeignKey(references=PartialGuild, null=False)
    role_id: Integer = Integer(index=True)
    last_known_name: Varchar = Varchar(default="Unknown Role", length=100)
    updated_at: Timestamptz = Timestamptz(auto_update=TimestamptzNow().python)

    @property
    @override
    def name(self) -> str:
        return self.last_known_name

    @property
    @override
    def mention(self) -> str:
        return f"<@&{self.role_id}>"

    @property
    @override
    def discord_object(self) -> discord.Object:
        return discord.Object(id=self.role_id, type=discord.Role)

    @property
    @override
    def discord_id(self) -> int:
        return self.discord_object.id

    @override
    def in_guild(self, guild: discord.Guild) -> bool:
        return bool(guild.get_role(self.discord_id))

    @overload
    async def fetch(self, bot: Red, *, fetch: Literal[True] = ..., upsert: bool = ...) -> discord.Role: ...

    @overload
    async def fetch(self, bot: Red, *, fetch: Literal[False] = False, upsert: bool = ...) -> discord.Role | None: ...

    async def fetch(self, bot: Red, *, fetch: bool = False, upsert: bool = True) -> discord.Role | None:
        """Retrieve a Role object for this PartialRole.

        Only use this if you need more information than is stored within the database.

        Args:
            bot: The bot object to use to retrieve the role.
            fetch: Whether or not to attempt to fetch the role from Discord's API if the role is not in the internal cache.
                Avoid using this unless absolutely necessary,
                as this endpoint is ratelimited and introduces additional runtime cost.
            upsert: Whether or not to automatically upsert the retrieved role object into the database.
                This introduces a minimal runtime cost if you're already
                fetching from the Discord API, and should usually be done.

        Returns:
            The retrieved role object, or None if `fetch` is `False` and the guild or role is not in the bot's internal cache.
        """
        partial_guild = await self.guild()
        if not (guild := await partial_guild.fetch(bot, fetch=fetch)):
            return None

        role = guild.get_role(self.role_id)
        if fetch and not role:
            role = await guild.fetch_role(self.role_id)

        if upsert and role:
            await self.upsert(role)
        return role

    async def guild(self, /, *, cache: bool = True) -> PartialGuild:
        """Retrieve the [`PartialGuild`][tidegear.sentinel.PartialGuild] that this role belongs to.

        Args:
            cache: Whether or not to try an internal cache before querying the database.
                This will have no effect if you haven't ran this method yet on this PartialRole instance.

        Raises:
            NotFoundError: If the guild tied to this role no longer exists in the database.
                This should be reported as a bug if it occurs,
                as there's a foreign key constraint that should prevent this on the table itself.

        Returns:
            The guild object tied to this role.
        """
        if cache and "_guild_obj" in self.__dict__:
            return self._guild_obj

        if isinstance(self.guild_id, PartialGuild):  # support both initialized PartialGuild objects and raw ints
            guild = self.guild_id
        elif not (
            guild := await PartialGuild.objects(PartialGuild.all_related()).where(PartialGuild.id == self.guild_id).first()
        ):
            msg = f"No guild exists in the database with id {self.guild_id}!"
            raise NotFoundError(msg)

        self._guild_obj = guild
        return self._guild_obj

    @classmethod
    async def upsert(cls, role: discord.Role) -> Self:
        """Insert or update a row in the database based on metadata from a Role object.

        Args:
            role: The role object to upsert.

        Raises:
            UpsertError: If upserting fails for some reason.

        Returns:
            (PartialRole): The resulting PartialRole object.
        """
        guild = await PartialGuild.upsert(guild=role.guild)

        query = cls.objects(cls.all_related()).where(cls.role_id == role.id, cls.guild_id.guild_id == role.guild.id).first()
        if fetched_role := await query:
            await fetched_role.update_self(values={cls.last_known_name: role.name})
            fetched_role._guild_obj = guild  # noqa: SLF001
            return fetched_role

        await cls.insert(cls(_data={cls.guild_id: guild.id, cls.role_id: role.id, cls.last_known_name: role.name}))

        if result := await query:
            result._guild_obj = guild  # noqa: SLF001
            return result
        msg = "Upsert operation failed!"
        raise UpsertError(msg)


PartialTargetable = PartialChannel | PartialRole | PartialUser
"""Partial tables that implement [`AbstractPartial`][tidegear.sentinel.AbstractPartial]
and may be set as targets within [`Moderation`][tidegear.sentinel.Moderation] rows."""


class Change(Table):
    """A database model representing a change to a moderation case.

    Attributes: Columns:
        id: The change's internal ID within the database.
        moderation_id: The moderation ID within the database of the moderation case this change is parented to.
            Use [`.moderation`][tidegear.sentinel.Change.moderation] instead
            if you want the actual moderation, and not just the moderation ID.
    """

    class Type(StrEnum):
        """Enum containing the possible types a Change may be."""

        ORIGINAL = "original"
        """The original moderation details.

        This will only ever be the first change in a moderation that has been modified from its original state.
        """
        RESOLVE = "resolve"
        """Added whenever the moderation has a resolve handler ran on it."""
        EDIT = "edit"
        """Added any other time the moderation is edited."""

    id: Serial = Serial(index=True, primary_key=True)
    moderation_id: ForeignKey["Moderation"] = ForeignKey(references="Moderation", null=False)
    type: Varchar = Varchar(choices=Type, null=False)
    timestamp: Timestamptz = Timestamptz(default=datetime.now, null=False)
    moderator_id: ForeignKey[PartialUser] = ForeignKey(references=PartialUser, null=False)
    reason: Text = Text(default=None, null=True)
    end_timestamp: Timestamptz = Timestamptz(default=None, null=True)

    @property
    def duration(self) -> timedelta | None:
        """Retrieve the timedelta between the change's timestamp and end timestamp.

        Returns:
            The difference (timedelta) between the end timestamp and the timestamp.
        """
        if self.timestamp and self.end_timestamp:
            return self.end_timestamp - self.timestamp
        return None

    async def moderation(self, /, *, cache: bool = True) -> "Moderation":
        """Retrieve the [`Moderation`][tidegear.sentinel.Moderation] that this change belongs to.

        Args:
            cache: Whether or not to try an internal cache before querying the database.
                This will have no effect if you haven't ran this method yet on this Change instance.

        Raises:
            NotFoundError: If the [`Moderation`][tidegear.sentinel.Moderation]
                tied to this change no longer exists in the database.
                This should be reported as a bug if it occurs,
                as there's a foreign key constraint that should prevent this on the table itself.

        Returns:
            The moderation tied to this change.
        """
        if cache and "_moderation_obj" in self.__dict__:
            return self._moderation_obj

        if isinstance(self.moderation_id, Moderation):  # support both initialized Moderation objects and raw ints
            mod = self.moderation_id
        elif not (mod := await Moderation.objects().where(Moderation.id == self.moderation_id).first()):
            msg = f"Moderation with id {self.moderation_id} does not exist in the database!"
            raise NotFoundError(msg)

        self._moderation_obj = mod
        return mod

    async def moderator(self, /, *, cache: bool = True) -> PartialUser:
        """Retrieve the [`PartialUser`][tidegear.sentinel.PartialUser] that this change was made by.

        Args:
            cache: Whether or not to try an internal cache before querying the database.
                This will have no effect if you haven't ran this method yet on this Change instance.

        Raises:
            NotFoundError: If the [`PartialUser`][tidegear.sentinel.PartialUser]
                tied to this change no longer exists in the database.
                This should be reported as a bug if it occurs,
                as there's a foreign key constraint that should prevent this on the table itself.
            UnsetError: If the change has no moderator set.


        Returns:
            The user who made this change.
        """  # noqa: DOC502
        if cache and "_moderator_obj" in self.__dict__:
            return self._moderator_obj

        def unset() -> Never:
            msg = f"Change {self.id:,} does not have a moderator set"
            raise UnsetError(msg)

        def not_found() -> Never:
            msg = f"Could not find a PartialUser in the database with id {self.moderator_id}"
            raise NotFoundError(msg)

        if self.moderator_id is None:
            unset()
        elif isinstance(self.moderator_id, PartialUser):  # support both initialized PartialUser objects and raw ints
            if self.moderator_id.is_null():
                unset()
            user = self.moderator_id
        elif not (
            user := await PartialUser.objects(PartialUser.all_related()).where(PartialUser.id == self.moderator_id).first()
        ):
            not_found()

        self._moderator_obj = user
        return user


class Moderation(Table):
    """A database model representing a moderation case.

    Attributes: Columns:
        id: The internal ID of the moderation case within the database.
        guild_id: The internal ID of the guild this moderation case originates from within the database.
            **This is not a Discord Guild ID!**
            Use [`.guild()`][tidegear.sentinel.Moderation.guild] to get an
            actual [`PartialGuild`][tidegear.sentinel.PartialGuild] object.
        timestamp: A timezone-aware datetime at which this moderation occurred.
        type_key: The moderation type this moderation uses.
            Use [`.type`][tidegear.sentinel.Moderation.type] to get an
            actual [`ModerationType`][tidegear.sentinel.ModerationType] object.
        target_user_id: The internal ID of the user this moderation case targets within the database.
            **This is not a Discord User ID!**
            Use [`.target()`][tidegear.sentinel.Moderation.target] to get an
            actual [`PartialUser`][tidegear.sentinel.PartialUser] object.
        target_channel_id: The internal ID of the channel this moderation case targets within the database.
            **This is not a Discord Channel ID!**
            Use [`.target()`][tidegear.sentinel.Moderation.target] to get an
            actual [`PartialChannel`][tidegear.sentinel.PartialChannel] object.
        target_role_id: The internal ID of the role this moderation case targets within the database.
            **This is not a Discord Role ID!**
            Use [`.target()`][tidegear.sentinel.Moderation.target] to get an
            actual [`PartialRole`][tidegear.sentinel.PartialChannel] object.
        moderator_id: The internal ID of the user this moderation case was created by within the database.
            **This is not a Discord User ID!**
            Use [`.moderator()`][tidegear.sentinel.Moderation.moderator] to get an
            actual [`PartialUser`][tidegear.sentinel.PartialUser] object.
        end_timestamp: A timezone-aware datetime at which this moderation should expire.
        expired: A boolean for if this moderation has expired yet.
        reason: The reason associated with this moderation.
        resolved: A boolean for if this moderation has been resolved.
        resolver_id: The internal ID of the user this moderation case was resolved by within the database.
            **This is not a Discord User ID!**
            Use [`.resolver()`][tidegear.sentinel.Moderation.resolver] to get an
            actual [`PartialUser`][tidegear.sentinel.PartialUser] object.
        resolve_reason: The reason associated with this moderation being resolved, if it has been.
        metadata: A dictionary of extraneous metadata that will be saved within the database in a JSON column.
            Consider using [`.meta`][tidegear.sentinel.Moderation.meta] if you just want to read this data and not write it.
    """

    id: Serial = Serial(index=True, primary_key=True)
    guild_id: ForeignKey[PartialGuild] = ForeignKey(references=PartialGuild, null=False, index=True)
    timestamp: Timestamptz = Timestamptz(default=datetime.now, null=False, index=True)
    type_key: Varchar = Varchar(default=None, null=False, db_column_name="type")
    target_user_id: ForeignKey[PartialUser] = ForeignKey(references=PartialUser, null=True, index=True)
    target_channel_id: ForeignKey[PartialChannel] = ForeignKey(references=PartialChannel, null=True, index=True)
    target_role_id: ForeignKey[PartialRole] = ForeignKey(references=PartialRole, null=True, index=True)
    moderator_id: ForeignKey[PartialUser] = ForeignKey(references=PartialUser, null=False, index=True)
    end_timestamp: Timestamptz = Timestamptz(default=None, null=True, index=True)
    expired: Boolean = Boolean(default=False, null=False)
    reason: Text = Text(default=None, null=True)
    resolved: Boolean = Boolean(default=False, null=False)
    resolver_id: ForeignKey[PartialUser] = ForeignKey(references=PartialUser, null=True, index=True)
    resolve_reason: Text = Text(default=None, null=True)
    metadata: JSON = JSON(default="{}", null=False)

    @property
    def duration(self) -> timedelta | None:
        """Retrieve the timedelta between the moderation's timestamp and end timestamp.

        Warning:
            This property does not check if the moderation's type supports expiry.
            Instead, use [`.type.can_expire`][tidegear.sentinel.ModerationType.can_expire] for that.

        Returns:
            The difference (timedelta) between the end timestamp and the timestamp.
        """
        if self.end_timestamp:
            return self.end_timestamp - self.timestamp
        return None

    @property
    def type(self) -> ModerationType:
        """Retrieve the moderation's case type. This gives you access to all of the type's handler methods.

        Raises:
            RegistryKeyError: If the case type does not exist in the [type registry][tidegear.sentinel.moderation_type_registry].

        Returns:
            The moderation's case type.
        """
        try:
            return moderation_type_registry.get(key=self.type_key)
        except RegistryKeyError as err:
            msg = f"Moderation type with key '{self.type_key}' does not exist in the moderation type registry!"
            raise RegistryKeyError(msg) from err

    @property
    def meta(self) -> dict[str, Any]:
        """Retrieve the moderation's metadata as a Python dictionary."""
        data: dict[str, Any] = orjson.loads(self.metadata)
        return data

    async def changes(self, /, *, cache: bool = True) -> list[Change]:
        """Retrieve a list of [`Changes`][tidegear.sentinel.Change] that target this moderation.

        Args:
            cache: Whether or not to try an internal cache before querying the database.
                This will have no effect if you haven't ran this method yet on this Moderation instance.

        Returns:
            A list of changes targeting this moderation.
        """
        if cache and "_changes" in self.__dict__:
            return self._changes

        changes = await Change.objects(Change.all_related()).where(Change.moderation_id == self.id)

        self._changes = changes
        return changes

    async def guild(self, /, *, cache: bool = True) -> PartialGuild:
        """Retrieve the [`PartialGuild`][tidegear.sentinel.PartialGuild] that this moderation belongs to.

        Args:
            cache: Whether or not to try an internal cache before querying the database.
                This will have no effect if you haven't ran this method yet on this Moderation instance.

        Raises:
            NotFoundError: If the [`PartialGuild`][tidegear.sentinel.PartialGuild]
                tied to this moderation no longer exists in the database.
                This should be reported as a bug if it occurs,
                as there's a foreign key constraint that should prevent this on the table itself.
            UnsetError: If the moderation has no guild set.
                This indicates a bug in the moderation handler for whatever moderation type this is.

        Returns:
            The PartialGuild that this moderation belongs to.
        """  # noqa: DOC502
        if cache and "_guild_obj" in self.__dict__:
            return self._guild_obj

        def unset() -> Never:
            msg = f"Moderation {self.id:,} does not have a guild set"
            raise UnsetError(msg)

        def not_found() -> Never:
            msg = f"Could not find a PartialGuild in the database with id {self.guild_id}"
            raise NotFoundError(msg)

        if self.guild_id is None:
            unset()
        elif isinstance(self.guild_id, PartialGuild):  # support both initialized PartialGuild objects and raw ints
            if self.guild_id.is_null():
                unset()
            guild = self.guild_id
        elif not (
            guild := await PartialGuild.objects(PartialGuild.all_related()).where(PartialGuild.id == self.guild_id).first()
        ):
            not_found()

        self._guild_obj = guild
        return guild

    async def moderator(self, /, *, cache: bool = True) -> PartialUser:
        """Retrieve the [`PartialUser`][tidegear.sentinel.PartialUser] who is credited with this moderation.

        Args:
            cache: Whether or not to try an internal cache before querying the database.
                This will have no effect if you haven't ran this method yet on this Moderation instance.

        Raises:
            NotFoundError: If the [`PartialUser`][tidegear.sentinel.PartialUser]
                tied to this moderation no longer exists in the database.
                This should be reported as a bug if it occurs,
                as there's a foreign key constraint that should prevent this on the table itself.
            UnsetError: If the moderation has no moderator set.
                This indicates a bug in the moderation handler for whatever moderation type this is.

        Returns:
            The PartialUser who is credited with this moderation.
        """  # noqa: DOC502
        if cache and "_moderator_obj" in self.__dict__:
            return self._moderator_obj

        def unset() -> Never:
            msg = f"Moderation {self.id:,} does not have a moderator set"
            raise UnsetError(msg)

        def not_found() -> Never:
            msg = f"Could not find a PartialUser in the database with id {self.moderator_id}"
            raise NotFoundError(msg)

        if self.moderator_id is None:
            unset()
        elif isinstance(self.moderator_id, PartialUser):  # support both initialized PartialUser objects and raw ints
            if self.moderator_id.is_null():
                unset()
            user = self.moderator_id
        elif not (
            user := await PartialUser.objects(PartialUser.all_related()).where(PartialUser.id == self.moderator_id).first()
        ):
            not_found()

        self._moderator_obj = user
        return user

    async def target(self, /, *, cache: bool = True) -> PartialTargetable:
        """Retrieve the target of this moderation.

        Args:
            cache: Whether or not to try an internal cache before querying the database.
                This will have no effect if you haven't ran this method yet on this Moderation instance.

        Raises:
            NotFoundError: If the target tied to this moderation no longer exists in the database.
                This should be reported as a bug if it occurs,
                as there's a foreign key constraint that should prevent this on the table itself.
            UnsetError: If `target_user`, `target_channel`, and `target_role` are none set on the moderation object.

        Returns:
            A partial object tied to the object that was targeted by this moderation.
        """
        if cache and "_target_obj" in self.__dict__:
            return self._target_obj

        result: PartialTargetable | None = None

        if self.target_user_id is not None:
            if isinstance(self.target_user_id, PartialUser):  # support both initialized PartialUser objects and raw ints
                if not self.target_user_id.is_null():
                    result = self.target_user_id
            elif not (
                result := await PartialUser.objects(PartialUser.all_related())
                .where(PartialUser.id == self.target_user_id)
                .first()
            ):
                msg = f"Could not find a PartialUser in the database with id {self.target_user_id}"
                raise NotFoundError(msg)

        if not result and self.target_channel_id is not None:
            if isinstance(self.target_channel_id, PartialChannel):  # support both initialized PartialChannel objects and raw ints
                if not self.target_channel_id.is_null():
                    result = self.target_channel_id
            elif not (
                result := await PartialChannel.objects(PartialChannel.all_related())
                .where(PartialChannel.id == self.target_channel_id)
                .first()
            ):
                msg = f"Could not find a PartialChannel in the database with id {self.target_channel_id}"
                raise NotFoundError(msg)

        if not result and self.target_role_id is not None:
            if isinstance(self.target_role_id, PartialRole):  # support both initialized PartialRole objects and raw ints
                if not self.target_role_id.is_null():
                    result = self.target_role_id
            elif not (
                result := await PartialRole.objects(PartialRole.all_related())
                .where(PartialRole.id == self.target_role_id)
                .first()
            ):
                msg = f"Could not find a PartialRole in the database with id {self.target_role_id}"
                raise NotFoundError(msg)

        if not result:
            msg = f"Moderation {self.id:,} has no target set!"
            raise UnsetError(msg)

        self._target_obj = result
        return result

    async def resolver(self, /, *, cache: bool = True) -> PartialUser:
        """Retrieve the [`PartialUser`][tidegear.sentinel.PartialUser] who is credited with resolving this moderation.

        Args:
            cache: Whether or not to try an internal cache before querying the database.
                This will have no effect if you haven't ran this method yet on this Moderation instance.

        Raises:
            NotFoundError: If the [`PartialUser`][tidegear.sentinel.PartialUser]
                tied to this moderation no longer exists in the database.
                This should be reported as a bug if it occurs,
                as there's a foreign key constraint that should prevent this on the table itself.
            UnsetError: If the moderation has no resolver set.

        Returns:
            The PartialUser who is credited with resolving this moderation.
        """  # noqa: DOC502
        if cache and "_resolver_obj" in self.__dict__:
            return self._resolver_obj

        def unset() -> Never:
            msg = f"Moderation {self.id:,} does not have a resolver set"
            raise UnsetError(msg)

        def not_found() -> Never:
            msg = f"Could not find a PartialUser in the database with id {self.resolver_id}"
            raise NotFoundError(msg)

        if self.resolver_id is None:
            unset()
        elif isinstance(self.resolver_id, PartialUser):  # support both initialized PartialUser objects and raw ints
            if self.resolver_id.is_null():
                unset()
            user = self.resolver_id
        elif not (user := await PartialUser.objects(PartialUser.all_related()).where(PartialUser.id == self.resolver_id).first()):
            not_found()

        self._resolver_obj = user
        return user

    async def expire(self, cog: "SentinelCog") -> Self:
        """Mark a moderation as expired. This will run the moderation type's expiration handler.

        Raises:
            ValueError: If the moderation is already expired.
            NotImplementedError: If the moderation type does not support expiry.
            NotReadyError: If the moderation isn't yet ready to expire.

        Returns:
            The expired moderation.
        """
        if self.expired:
            msg = f"Moderation {self.id:,} is already expired!"
            raise ValueError(msg)

        if self.type.can_expire and self.end_timestamp:
            if datetime.now(tz=UTC) >= self.end_timestamp:
                await self.type.expiry_handler(cog, moderation=self)
                await self.update_self({Moderation.expired: True})
                return self
            msg = f"Moderation {self.id:,} is not ready to expire yet!"
            raise NotReadyError(msg)
        msg = f"Moderation of type {self.type.key} is not expirable or does not have a duration!"
        raise NotImplementedError(msg)

    @classmethod
    async def from_id(cls, moderation_id: int) -> Self:
        """Retrieve a moderation case by ID.

        Args:
            moderation_id: The ID of the moderation case to look up.

        Raises:
            NotFoundError: If the database does not contain a moderation case matching the given ID.

        Returns:
            The moderation that matches the given ID.
        """
        moderation = await cls.objects(cls.all_related()).where(cls.id == moderation_id).first()
        if not moderation:
            msg = f"Could not find moderation within the database with an ID of {moderation_id}."
            raise NotFoundError(msg)
        return moderation

    @classmethod
    async def delete_for_guild(cls, guild: discord.Guild | PartialGuild) -> list[Self]:
        """Delete all Moderation cases for a specific guild.

        Args:
            guild: The guild to delete cases for.

        Returns:
            (list[Moderation]): The deleted cases.
        """
        if isinstance(guild, discord.Guild):
            guild = await PartialGuild.upsert(guild)
        raw_moderations = await cls.delete().where(cls.guild_id == guild.id).returning(*cls.all_columns())
        return [cls(**moderation) for moderation in raw_moderations]

    @classmethod
    async def next_case_number(cls) -> int:
        """Return the case number of the next moderation to be inserted into the database."""
        return await cls.count() + 1


TABLES: list[type[BaseTable]] = [PartialGuild, PartialChannel, PartialRole, PartialUser, Change, Moderation]
