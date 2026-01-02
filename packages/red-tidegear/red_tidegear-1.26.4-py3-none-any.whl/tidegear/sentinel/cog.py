# SPDX-FileCopyrightText: 2025 cswimr <copyright@csw.im>
# SPDX-License-Identifier: MPL-2.0

"""Cog class for cogs using the Sentinel moderation system."""

import inspect
import logging as py_logging
import pathlib
from collections import defaultdict
from datetime import date, datetime, timedelta
from types import UnionType
from typing import Any, Callable, Literal, Mapping

import discord
import discord.ext.tasks
from class_registry.base import RegistryKeyError
from class_registry.registry import ClassRegistry
from discord.utils import MISSING, utcnow
from piccolo.columns import Or, Where
from piccolo.engine.sqlite import SQLiteEngine
from red_commons import logging
from redbot.core import app_commands, commands
from redbot.core.bot import Red
from redbot.core.config import Group
from redbot.core.data_manager import cog_data_path
from redbot.core.i18n import Translator, set_contextual_locales_from_guild
from redbot.core.utils.views import _ACCEPTABLE_PAGE_TYPES, SimpleMenu
from redbot_orm.sqlite import register_cog
from typing_extensions import override

from tidegear import Cog
from tidegear import chat_formatting as cf
from tidegear.exceptions import ArgumentTypeError, ConfigurationError, ContextError, NotFoundError, UnmetPermissionsError
from tidegear.pydantic import truncate_string
from tidegear.sentinel.config import SentinelConfigSchema, _ModerationTypeGroup
from tidegear.sentinel.db import TABLES, Moderation, PartialChannel, PartialGuild, PartialRole, PartialTargetable, PartialUser
from tidegear.sentinel.exceptions import HandlerError, LoggedHandlerError, NotReadyError, UnsetError
from tidegear.sentinel.moderation_type import ModerationType, moderation_type_registry
from tidegear.types import GuildChannel, GuildMesseagableChannel
from tidegear.utils import class_overrides_attribute, get_asset_as_file, send_error, set_env, title

Targetable = GuildChannel | discord.User | discord.Member | discord.Role
"""Valid types for the target argument in the [`sentinel_moderate`][tidegear.sentinel.SentinelCog.sentinel_moderate] function."""

_ = Translator("TidegearCog", __file__)


class SentinelCog(Cog):
    """The base cog class for cogs that utilize the Sentinel moderation system.

    Keep in mind that you **must** have a `meta.json` file in your cog's
    [data folder][redbot.core.data_manager.bundled_data_path] in order to use this cog class.

    Warning:
        Subclasses of this class should not have method names that start with `sentinel`, `tidegear_`, or `red_`.
        They also should not have dunder methods whose names begin with `__sentinel`, `__tidegear`, or `__red`.
        Methods with these names are reserved for future functionality within Sentinel, Tidegear, or Red, respectively.

    Args:
        bot: The bot object passed to the cog during loading.

    Attributes:
        moderation_type_registry: The registry for moderation types that you can access
            to retrieve [`ModerationType`][tidegear.sentinel.ModerationType] objects.
        moderation_types: A list of your cog's moderation types. You should be overriding this in `__init__()`.
        db: The database engine.
        sentinel_config: The global Sentinel configuration.
    """

    _sentinel_expiry_loop: discord.ext.tasks.Loop | None = None

    def __init__(self, bot: Red) -> None:
        super().__init__(bot)
        self.moderation_type_registry: ClassRegistry[ModerationType] = moderation_type_registry
        self.db: SQLiteEngine = MISSING
        self._sentinel_data_path: pathlib.Path = cog_data_path(raw_name="TidegearSentinel")
        self.sentinel_config: SentinelConfigSchema = MISSING
        self._sentinel_logger: logging.RedTraceLogger = self.logger.getChild("sentinel")
        self.tidegear_setup_file_logger(self._sentinel_logger, self._sentinel_data_path / "logs", "TidegearSentinel")

        # If we don't override aiosqlite's logging level, it will spam the console with dozens of debug messages per query.
        # This is unnecessary because the information that aiosqlite logs is not particularly useful to the bot owner.
        # This is a subpar solution though as it overrides it for any other cogs that are using aiosqlite too.
        # If there's a better solution that you're aware of, please let me know in Discord or in a CoastalCommits issue.
        if self.logger.level >= logging.VERBOSE or self.logger.level == py_logging.NOTSET:
            py_logging.getLogger("aiosqlite").setLevel(py_logging.INFO)
        elif self.logger.level < logging.VERBOSE:
            py_logging.getLogger("aiosqlite").setLevel(self.logger.level)

    @override
    async def cog_load(self) -> None:
        """Run asynchronous code during the cog loading process.

        Subclasses may override this if they want special asynchronous loading behaviour.
        The `__init__` special method does not allow asynchronous code to run
        inside it, thus this is helpful for setting up code that needs to be asynchronous.

        Danger:
            Please ensure that you call `await super().cog_load()` within your overridden method,
            as this method sets up the configuration schema, database engine, and moderation type registry for Sentinel cogs.

        """
        await super().cog_load()
        self.sentinel_config = await SentinelConfigSchema.init(logger=self._sentinel_logger)

        self._sentinel_logger.verbose(
            "Using the following path to store the Sentinel SQLite database: %s", self._sentinel_data_path
        )
        trace = True if self._sentinel_logger.level <= py_logging.DEBUG else False
        with set_env(key="PICCOLO_CONF", value="tidegear.sentinel.db.piccolo_conf", logger=self._sentinel_logger):
            self.db = await register_cog(
                cog_instance=self._sentinel_data_path,
                tables=TABLES,
                trace=trace,
            )

        for moderation_type in self.sentinel_moderation_types:
            if moderation_type.key in self.moderation_type_registry:
                conflict = self.moderation_type_registry[moderation_type.key]
                cls = conflict.__class__
                mod_name = cls.__module__
                file_path = inspect.getfile(cls)
                self._sentinel_logger.error(
                    (
                        "Cannot add moderation type with duplicate key '%s'! "
                        "Conflicting type: '%s' (class name: '%s', module: '%s', file: '%s')"
                    ),
                    moderation_type.key,
                    conflict.key,
                    cls.__qualname__,
                    mod_name,
                    file_path,
                )
                continue
            self.moderation_type_registry.register(key=moderation_type.key)(moderation_type)
            self._sentinel_logger.verbose("Registered moderation type with key '%s'", moderation_type.key)

        for old, new in self.sentinel_moderation_type_migrations.items():
            await Moderation.update({Moderation.type_key: new.key}).where(Moderation.type_key == old)

            for guild in await self.get_enabled_guilds():
                # `tidegear.config` has no concept of Groups, so we use normal Red Config methods to do this operation
                old_config = self._get_sentinel_type_config(guild=guild, moderation_type=old)
                new_config = self._get_sentinel_type_config(guild=guild, moderation_type=new)
                await new_config.set(await old_config.all())
                await old_config.clear()

        self._sentinel_monitor_expiry_loop.start()

    @override
    async def cog_unload(self) -> None:
        """Run asynchronous code during the cog unloading process.

        Danger:
            Please ensure that you call `await super().cog_unload()` within your overridden method,
            as this method cleans up the Sentinel expiry loop and moderation type registry, and must be ran.
        """
        for moderation_type in self.sentinel_moderation_types:
            if moderation_type.key not in self.moderation_type_registry:
                self._sentinel_logger.warning(
                    "Moderation type with key '%s' does not exist in the type registry, skipping unregistration.",
                    moderation_type.key,
                )
                continue
            self.moderation_type_registry.unregister(key=moderation_type.key)
            self._sentinel_logger.trace("Unregistered moderation type with key '%s'", moderation_type.key)

        if SentinelCog._sentinel_expiry_loop and SentinelCog._sentinel_expiry_loop.is_running:
            SentinelCog._sentinel_expiry_loop.cancel()
            self._sentinel_logger.debug("Cancelled expiry loop!")

        self.tidegear_close_logger(self._sentinel_logger)
        await super().cog_unload()

    @override
    async def red_delete_data_for_user(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        *,
        requester: Literal["discord_deleted_user", "owner", "user", "user_strict"],
        user_id: int,
    ) -> None:
        async def anonymize_user(user_id: int, /, *, deleted: bool) -> None:
            for user in await PartialUser.objects().where(PartialUser.user_id == user_id):
                await user.update_self(
                    values={
                        PartialUser.last_known_name: "Deleted User" if deleted else PartialUser.last_known_name.default,
                        PartialUser.discriminator: PartialUser.discriminator.default,
                    }
                )

        match requester:
            case "discord_deleted_user":
                await self.sentinel_config.config.user_from_id(user_id).clear()
                await anonymize_user(user_id, deleted=True)
            case "owner" | "user_strict":
                await self.sentinel_config.config.user_from_id(user_id).clear()
                await anonymize_user(user_id, deleted=False)
            case "user":
                await self.sentinel_config.config.user_from_id(user_id).clear()
            case _:
                self._sentinel_logger.warning("Invalid requester passed to red_delete_data_for_user: %s", requester)

    @property
    def sentinel_moderation_types(self) -> list[type[ModerationType]]:
        """Return a set of moderation types that are added by this cog.

        If you are adding any custom moderation types, you **must** override this method to return your new moderation types.
        If you do not do this, then your types will never be added to the type registry.

        Example:
            ```python
            from sentinel.tidegear import ModerationType
            from .types import Warn, Mute, Tempban, Ban


            @property
            def moderation_types(self) -> list[type[ModerationType]]:
                return [Warn, Mute, Tempban, Ban]  # Do not create instances of these classes! Just provide their types.
            ```
        """
        return []

    @property
    def sentinel_moderation_type_migrations(self) -> Mapping[str, type[ModerationType]]:
        """Return a mapping of moderation type keys that should be replaced within the database to new ModerationTypes.

        Migrations will occur on cog load.
        Please take care to not migrate the types of other cogs utilizing Sentinel unless you expressly want to.

        Example:
            ```python
            from sentinel.tidegear import ModerationType
            from .types import Warn


            @property
            def moderation_type_migrations(self) -> Mapping[str, type[ModerationType]]:
                return {"warning": Warn}
            ```
        """
        return {}

    @property
    def adds_moderation_types(self) -> bool:
        """Check whether or not a cog class overrides the
        [`sentinel_moderation_types`][tidegear.sentinel.SentinelCog.sentinel_moderation_types] property.
        """
        return class_overrides_attribute(child=type(self), parent=SentinelCog, attribute="sentinel_moderation_types")

    @property
    def sentinel_cogs(self) -> Mapping[str, "SentinelCog"]:
        """Get a mapping of all cogs that are currently loaded that are subclasses of SentinelCog.

        Tip:
            This includes the cog instance executing this method!

        Returns:
            A mapping of cog names to SentinelCog instances.
        """
        return {name: cog for name, cog in self.bot.cogs.items() if isinstance(cog, SentinelCog)}

    def _get_sentinel_type_config(
        self, *, guild: discord.Guild | int, moderation_type: ModerationType | type[ModerationType] | str, safe: bool = True
    ) -> Group:
        """Retrieve a [`Group`][redbot.core.config.Group] that contains configuration for a specific moderation type.

        Args:
            guild: The Guild to fetch configuration for.
            moderation_type: The moderation type to fetch configuration for.
            safe: Whether to use a config instance with/without force registration.

        Returns:
            The fetched configuration group. Consumed the same way as a `custom()` call.
        """
        if isinstance(guild, discord.Guild):
            guild_id = guild.id
        else:
            guild_id = guild

        if isinstance(moderation_type, str):
            key = moderation_type
        else:
            key = moderation_type.key

        if safe:
            return self.sentinel_config.config.custom(_ModerationTypeGroup.name, str(guild_id), key)
        return self.sentinel_config.unsafe_config.custom(_ModerationTypeGroup.name, str(guild_id), key)  # noqa: SLF001

    async def sentinel_log_channel(self, guild: discord.Guild) -> GuildMesseagableChannel | None:
        """Retrieve the moderation logging channel for a guild.

        Args:
            guild: The guild to fetch the logging channel for.

        Raises:
            ConfigurationError: If

        Returns:
            The fetched channel.
        """
        channel_id = await self.sentinel_config.log_channel.get(guild)
        if channel_id is None:
            return None

        try:
            channel = await self.get_or_fetch_channel(guild, channel_id)
            if not isinstance(channel, GuildMesseagableChannel):
                msg = (
                    f"Channel {channel.name} ({channel.id}) in guild {guild.name} {(guild.id)} does not support sending messages,"
                    " and cannot be used as the Sentinel logging channel."
                )
                raise ConfigurationError(msg)
            self._sentinel_logger.trace("channel: %s, channel type: %s", channel, type(channel))
            return channel
        except discord.NotFound:
            return None

    async def sentinel_moderate(
        self,
        ctx: commands.GuildContext | discord.Interaction,
        target: Targetable,
        moderation_type: ModerationType | str,
        silent: bool = MISSING,
        reason: str | None = None,
        **kwargs: Any,
    ) -> None | Moderation:
        """Moderate a user.

        Checks if the target can be moderated, then calls the handler method of the moderation type specified.

        Info: Event Dispatch
            This method, upon success, will dispatch an event you can listen to with the ID `sentinel_moderation`.
            Here is an example of an event listener that consumes this event.

            ```py
            from tidegear.sentinel import Moderation, SentinelCog


            class ExampleCog(SentinelCog):
                @SentinelCog.listener("sentinel_moderation")
                async def on_sentinel_moderation(self, moderation: Moderation):
                    self.logger.debug(moderation)
            ```

        Args:
            ctx: The context of the command.
                If this is a [`discord.Interaction`][] object, it will be converted to a
                [`commands.GuildContext`][redbot.core.commands.GuildContext] object.
                Additionally, if the interaction originated from a context menu,
                the [`ctx.author`][discord.ext.commands.Context.author] attribute
                will be overridden to [`interaction.user`][discord.Interaction.user].
            target: The target user or channel to moderate.
            moderation_type: The moderation type (handler) to use.
            silent: Whether or not to message the target.
            reason: The reason to give this moderation. Defaults to guild configuration when not provided.
            **kwargs: Any additional keyword arguments to pass to the handler method.

        Returns:
            The resulting Moderation, or `None` if an error was encountered.
        """
        if isinstance(moderation_type, str):
            moderation_type = moderation_type_registry[moderation_type.lower()]

        await set_contextual_locales_from_guild(self.bot, ctx.guild)

        if not ctx.guild:
            await send_error(ctx, content=_("Cannot moderate users outside of a guild!"))
            return None

        if isinstance(ctx, discord.Interaction):
            interaction = ctx
            ctx = await commands.GuildContext.from_interaction(interaction)
            if isinstance(interaction.command, app_commands.ContextMenu):
                if not isinstance(interaction.user, discord.Member):
                    await send_error(ctx, content=_("Are you real?"))
                    return None
                ctx.author = interaction.user  # pyright: ignore[reportAttributeAccessIssue]

        try:
            await self.sentinel_check_moddable(target=target, ctx=ctx, moderation_type=moderation_type)
        except (UnmetPermissionsError, ContextError) as err:
            await err.send(ctx)
            return None

        try:
            moderation_handler = moderation_type.handler(target=target)
        except ArgumentTypeError as err:
            await err.send(ctx)
            return None

        if silent == MISSING:
            silent = await self.sentinel_config.get_type_config_with_fallback(
                self.sentinel_config.dm_users, guild=ctx.guild, moderation_type=moderation_type
            )

        if not reason:
            reason = await self.sentinel_config.get_type_config_with_fallback(
                self.sentinel_config.default_reason, guild=ctx.guild, moderation_type=moderation_type
            )

        try:
            if isinstance(target, (discord.User, discord.Member)):
                kwargs["silent"] = silent if moderation_type.removes_from_guild else True

            moderation = await moderation_handler(cog=self, ctx=ctx, target=target, reason=reason, **kwargs)
        except HandlerError as err:
            await err.send(ctx)
            return None
        except LoggedHandlerError as err:
            await err.send(ctx)
            self._sentinel_logger.exception("Encountered exception within moderation handler %s", moderation_handler.__qualname__)
            return None
        except Exception:
            await send_error(ctx, content=_("Internal error encountered, report this to the bot owner!"))
            self._sentinel_logger.exception("Encountered exception within moderation handler %s", moderation_handler.__qualname__)
            return None

        if not moderation_type.removes_from_guild and not silent:
            try:
                await self.sentinel_contact_target(moderation)
            except (ConfigurationError, TypeError) as err:
                self._sentinel_logger.warning("Unable to contact target '%s'!", target.id, exc_info=err)
            except discord.Forbidden:
                pass

        try:
            await self.sentinel_send_log(moderation)
        except ConfigurationError:
            pass

        self._sentinel_logger.verbose("Moderation success: %s", moderation)
        self.bot.dispatch("sentinel_moderation", moderation)
        return moderation

    def sentinel_check_permissions(
        self,
        user: discord.Member | discord.abc.User | PartialUser,
        required_permissions: discord.Permissions,
        guild: discord.Guild,
        channel: GuildChannel | None = None,
    ) -> None:
        """Check if a user has a specific permission (or a list of permissions) in a channel.

        Users with the `Administrator` permission will always pass this check.
        An exception will always be raised if the permissions check fails.

        Args:
            user: The user to check the permissions of.
            required_permissions: The permissions to check for.
            guild: The guild to use to retrieve the `user` if it isn't already a [`discord.Member`][] object.
            channel: The guild channel or thread to perform the check in.
                If this is provided, this method will use the
                [`GuildChannel.permissions_for`][discord.abc.GuildChannel.permissions_for] method,
                which is much more accurate than the [`Member.guild_permissions`][discord.Member.guild_permissions]
                attribute that is used when `channel` isn't provided.

        Raises:
            ArgumentTypeError: Raised if `user` does not match this method's typehints.
            UnmetPermissionsError: Raised if the permissions check fails. These error messages are safe to send to end users.
        """
        if isinstance(user, discord.Member):
            member = user
        elif isinstance(user, discord.abc.User):
            member = guild.get_member(user.id)
        elif isinstance(user, PartialUser):
            member = guild.get_member(user.discord_id)
        else:
            msg = "Unsupported type!"
            raise ArgumentTypeError(msg)

        resolved_permissions = None

        if channel and member:
            resolved_permissions = channel.permissions_for(member)

        elif member:
            resolved_permissions = member.guild_permissions

        if not member or not resolved_permissions:
            msg = _("Could not check permissions for {mention}!").format(mention=user.mention)
            raise UnmetPermissionsError(msg)

        if resolved_permissions.administrator:
            return

        if not resolved_permissions >= required_permissions:
            missing = [name for name, wanted in required_permissions if wanted and not getattr(resolved_permissions, name)]
            self._sentinel_logger.trace(
                (
                    "Permissions check failed for user with id '%s' in channel '%s' (guild '%s')\n"
                    "Resolved permissions: %s\nRequired permissions: %s\nMissing: %s"
                ),
                member.id,
                channel.id if channel else None,
                guild.id,
                cf.format_perms_list(resolved_permissions),
                cf.format_perms_list(required_permissions),
                missing,
            )

            perms_list = cf.humanize_list([cf.inline(perm) for perm in missing])
            who = "I" if self.me.id == member.id else "You"
            within_channel = f" within the {channel.mention} channel" if channel else ""
            part = f"permissions{within_channel}, which are" if len(missing) > 1 else f"permission{within_channel}, which is"

            msg = f"{who} do not have the {perms_list} {part} required for this action."
            # this would be really hard to translate probably, not going to do it for now
            raise UnmetPermissionsError(msg)

    async def sentinel_check_moddable(
        self,
        ctx: commands.GuildContext,
        target: Targetable,
        moderation_type: ModerationType,
    ) -> None:
        """Check if the `ctx.author` can moderate the target.

        Abstract: Order of Operations:
            - Ensure that the passed context object originates from a guild and that the bot is a member of the guild.
            - Check the bot's permissions against [`moderation_type.permissions`][tidegear.sentinel.ModerationType].
            - If `use_discord_permissions` is `True` in the Sentinel guild configuration,
                check the `ctx.author`'s permissions against [`moderation_type.permissions`][tidegear.sentinel.ModerationType].
            - If the target is a guild member:
                - Ensure that the `ctx.author` is not attempting to moderate themselves.
                - If the `ctx.author` does not have the `Administrator` permission, ensure that the target is not a bot.
                - Ensure that the target does not have the `Administrator` permission.
                - Ensure that the target does not have a role higher than or equal to the bot's top role.
                - If `respect_hierarchy` is `True` in the Sentinel guild configuration,
                    ensure the target does not have a role higher than or equal to the `ctx.author`'s top role.
                - If the `ctx.author` does not have the `Administrator` permission, ensure that the target
                    does not have any of the roles set as immune roles within the Sentinel guild configuration.

        Args:
            ctx: The context where the moderation is taking place.
            target: The target of the moderation.
            moderation_type: The type of the moderation you're wanting to perform.
                Used for checking Red's configuration and confirming that the
                `ctx.author` and the bot have all of the required permissions.

        Raises:
            ContextError: Raised when the bot user is not in the guild that the passed context originates from.
            UnmetPermissionsError: Raised if the target cannot be moderated by the `ctx.author`.
                These error messages are safe to send to end users.
        """
        if not (me := ctx.guild.get_member(ctx.me.id)):
            msg = "The bot user is not in the guild that the passed Context originates from!"
            raise ContextError(msg)

        is_channel = isinstance(target, GuildChannel)

        self.sentinel_check_permissions(
            user=me,
            required_permissions=moderation_type.permissions,
            guild=ctx.guild,
            channel=target if is_channel else ctx.channel,
        )

        use_discord_permissions = await self.sentinel_config.get_type_config_with_fallback(
            self.sentinel_config.use_discord_permissions, guild=ctx.guild, moderation_type=moderation_type
        )
        if use_discord_permissions is True:
            self.sentinel_check_permissions(
                user=ctx.author,
                required_permissions=moderation_type.permissions,
                guild=ctx.guild,
                channel=target if is_channel else ctx.channel,
            )

        if isinstance(target, discord.Member) and isinstance(ctx.author, discord.Member):
            is_moderator_admin = ctx.author.guild_permissions.administrator

            if ctx.author.id == target.id:
                msg = _("You cannot moderate yourself!")
                raise UnmetPermissionsError(msg)

            if not is_moderator_admin and target.bot:
                msg = _("You cannot moderate bots!")
                raise UnmetPermissionsError(msg)

            if target.guild_permissions.administrator:
                msg = _("You cannot moderate members with the Administrator permission!")
                raise UnmetPermissionsError(msg)

            if me.top_role <= target.top_role:
                msg = _("You cannot moderate members with a role higher than the bot!")
                raise UnmetPermissionsError(msg)

            if ctx.author.top_role <= target.top_role and await self.sentinel_config.respect_hierarchy.get(target.guild) is True:
                msg = _("You cannot moderate members with a higher role than you!")
                raise UnmetPermissionsError(msg)

            if not is_moderator_admin:
                immune_roles = await self.sentinel_config.immune_roles.get(target.guild)
                matching = [role.mention for role in target.roles if role.id in immune_roles]

                if matching:
                    formatted = cf.humanize_list(matching, style="or")
                    plural = "s" if len(matching) > 1 else ""
                    part = "they are" if len(matching) > 1 else "it is an"
                    msg = f"You cannot moderate members with the {formatted} role{plural}, because {part} immune role{plural}!"
                    raise UnmetPermissionsError(msg)

    async def sentinel_contact_target(
        self,
        moderation: Moderation,
        *,
        response: discord.Message | None = None,
        case: bool = True,
    ) -> discord.Message:
        """Contact the target user of a moderation with details regarding their case.

        Additionally to the exceptions in the `Raises:` section below,
        this method can raise all exceptions that [`discord.User.send`][] can.

        Args:
            moderation: The moderation to generate details from.
            response: The response message.
            case: Whether the message is for a moderation case.

        Raises:
            TypeError: Raised when the moderation's target is not a [`PartialUser`][tidegear.sentinel.db.PartialUser].
            ConfigurationError: Raised when the Sentinel configuration disallows sending messages to targeted users.

        Returns:
            The sent message object.
        """
        target = await moderation.target()
        if not isinstance(target, PartialUser):
            msg = f"Cannot message {type(target)}s!"
            raise TypeError(msg)

        moderator = await moderation.moderator()
        guild = await (await moderation.guild()).fetch(bot=self.bot)
        target = await target.fetch(fetcher=self.bot, fetch=True)

        if channel := next((ch for ch in guild.channels if isinstance(ch, GuildMesseagableChannel)), None):
            color = await self.bot.get_embed_color(location=channel)
        else:
            color = discord.Color.red()

        dm_users = await self.sentinel_config.get_type_config_with_fallback(
            self.sentinel_config.dm_users, guild=guild, moderation_type=moderation.type
        )
        if not dm_users:
            msg = "Contacting moderation targets is disabled!"
            raise ConfigurationError(msg)

        if response is not None and not moderation.type.removes_from_guild:
            guild_name = f"[{guild.name}]({response.jump_url})"
        else:
            guild_name = guild.name

        if moderation.duration:
            embed_duration = f" for {cf.humanize_timedelta(moderation.duration)}"
        else:
            embed_duration = ""

        embed = discord.Embed(
            title=str.title(moderation.type.verb),
            color=color,
            description=f"You have {moderation.type.embed_desc}{moderation.type.verb}{embed_duration} in {guild_name}.",
            timestamp=moderation.timestamp,
        )

        if guild.icon:
            embed.set_author(name=guild.name, icon_url=guild.icon.url)
        else:
            embed.set_author(name=guild.name)

        kwargs: dict[str, Any] = {}

        if case:
            embed.set_footer(
                text=f"Case #{moderation.id:,}",
                icon_url="attachment://arrow.png",
            )

            kwargs["file"] = get_asset_as_file(filename="arrow.png", description="Arrow")

        show_moderator = await self.sentinel_config.get_type_config_with_fallback(
            self.sentinel_config.show_moderator, guild=guild, moderation_type=moderation.type
        )
        if show_moderator and moderator is not None:
            embed.add_field(name="Moderator", value=f"`{moderator.name} ({moderator.user_id})`", inline=False)

        if moderation.reason:
            embed.add_field(name="Reason", value=f"`{moderation.reason}`", inline=False)

        if support_message := await self.sentinel_config.get_type_config_with_fallback(
            self.sentinel_config.support_message, guild=guild, moderation_type=moderation.type
        ):
            embed.add_field(name="Support", value=support_message, inline=False)

        button_label = await self.sentinel_config.get_type_config_with_fallback(
            self.sentinel_config.button_label, guild=guild, moderation_type=moderation.type
        )
        button_url = await self.sentinel_config.get_type_config_with_fallback(
            self.sentinel_config.button_url, guild=guild, moderation_type=moderation.type
        )
        if button_label and button_url:
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label=button_label, url=str(button_url)))
            kwargs["view"] = view

        return await target.send(embed=embed, **kwargs)

    async def sentinel_send_log(self, moderation: Moderation) -> discord.Message:
        """Send a moderation log to a guild's configured moderation channel.

        Args:
            moderation: The moderation to create a log for.

        Raises:
            ConfigurationError: If the moderation's guild has no logging channel configured.

        Returns:
            The resulting logging message.
        """
        guild = await (await moderation.guild()).fetch(self.bot)
        if not (log_channel := await self.sentinel_log_channel(guild)) or not isinstance(log_channel, GuildMesseagableChannel):
            msg = _("Logging is disabled!")
            raise ConfigurationError(msg)
        embed = await self.sentinel_case_embed(moderation, color=await self.bot.get_embed_color(location=log_channel))
        return await log_channel.send(embed=embed)

    async def sentinel_case_embed(self, moderation: Moderation, color: discord.Color | None = None) -> discord.Embed:
        """Create a case embed from a Moderation object.

        Args:
            moderation: The moderation object.
            color: The color to use for the embed. Defaults to `Color.red()`.

        Returns:
            The resulting embed containing information from the moderation.
        """
        target = await moderation.target()
        moderator = await moderation.moderator()
        guild = await (await moderation.guild()).fetch(self.bot)

        await set_contextual_locales_from_guild(self.bot, guild)

        try:
            if isinstance(target, PartialChannel):
                target = await PartialChannel.upsert(channel=await self.get_or_fetch_channel(guild, channel_id=target.channel_id))
            elif isinstance(target, PartialUser):
                target = await PartialUser.upsert(user=await self.get_or_fetch_user(user_id=target.user_id))
            moderator = await PartialUser.upsert(user=await self.get_or_fetch_user(user_id=moderator.user_id))
        except Exception:
            pass

        moderation_type = moderation.type_key
        try:
            moderation_type = moderation.type.name
        except RegistryKeyError:
            pass

        embed = discord.Embed(
            title=_("📕 Case #{id}").format(id=cf.humanize_number(moderation.id)),
            color=color or discord.Color.red(),
        )

        embed_description_lines: list[str] = [
            _("**Type:** {title}").format(title=title(moderation_type)),
            _("**Target:** {target} (`{id}`)").format(
                target=target.mention if target.in_guild(guild) else cf.inline(text=target.name), id=target.discord_id
            ),
            _("**Moderator**: {moderator} (`{id}`)").format(
                moderator=moderator.mention if moderator.in_guild(guild) else cf.inline(text=moderator.name),
                id=moderator.discord_id,
            ),
            _("**Timestamp:** {date} | {relative}").format(
                date=cf.format_datetime(dt=moderation.timestamp, style=cf.TimestampStyle.SHORT_DATE_AND_TIME),
                relative=cf.format_datetime(dt=moderation.timestamp, style=cf.TimestampStyle.RELATIVE),
            ),
        ]

        if moderation.end_timestamp:
            duration_embed = (
                (
                    f"{cf.humanize_timedelta(moderation.duration)} "
                    f"| {cf.format_datetime(dt=moderation.end_timestamp, style=cf.TimestampStyle.RELATIVE)}"
                )
                if not moderation.expired
                else cf.humanize_timedelta(moderation.duration)
            )
            embed_description_lines.extend([
                _("**Duration:** {string}").format(string=duration_embed),
                _("**Expired:** True") if moderation.expired else _("**Expired:** False"),
            ])

        if value := moderation.meta.get("imported_timestamp"):
            timestamp = datetime.fromisoformat(value)
            embed_description_lines.append(
                _("**Imported Timestamp:** {timestamp}").format(timestamp=cf.format_datetime(dt=timestamp))
            )

        try:
            moderation_type = moderation.type
            embed_description_lines.extend([
                # Can't really be translated on our side unfortunately
                f"**{title(metadata.human_name)}:** {value}"
                for metadata in moderation_type.metadata
                if (value := await metadata.fetch_from_moderation(moderation, self.bot))
            ])
        except RegistryKeyError:
            pass

        embed.description = "\n".join(embed_description_lines)

        if moderation.reason:
            embed.add_field(name=_("Reason"), value=cf.box(truncate_string(moderation.reason, 1010)), inline=False)

        if moderation.resolved:
            try:
                resolver = await moderation.resolver()
                if embed.title:
                    embed.title += _(" Resolved")
                embed.add_field(
                    name=_("Resolve Reason"),
                    value=_("Resolved by {mention} ({id}) for:\n{reason}").format(
                        mention=resolver.mention,
                        id=resolver.discord_id,
                        reason=cf.box(truncate_string(moderation.resolve_reason, 900)),
                    ),
                    inline=False,
                )
            except NotFoundError:
                pass
        return embed

    async def sentinel_changes_menu(self, moderation: Moderation, color: discord.Color | None = None) -> SimpleMenu:
        """Create a menu containing all of the historical changes to a Moderation.

        Args:
            moderation: The moderation to list the changes of.
            color: The color of the resulting embeds within the menu.

        Returns:
            The created SimpleMenu, which you can then start with [`.start`][redbot.core.utils.views.SimpleMenu.start].
        """
        changes = await moderation.changes()
        guild = await (await moderation.guild()).fetch(self.bot)

        await set_contextual_locales_from_guild(self.bot, guild)

        pages: list[_ACCEPTABLE_PAGE_TYPES] = []
        if not changes:
            pages.append(_("No changes have been made to this case!"))
            return SimpleMenu(pages)

        fields_per_embed = 10
        for i in range(0, len(changes), fields_per_embed):
            embed = discord.Embed(
                title=_("📕 Case #{id} Changes").format(id=cf.humanize_number(moderation.id)),
                color=color or discord.Color.blue(),
            )
            embed.set_footer(
                text=_("Page {current}/{total}").format(
                    current=i // fields_per_embed + 1, total=len(changes) // fields_per_embed + 1
                )
            )

            for change in changes[i : i + fields_per_embed]:
                moderator = await change.moderator()

                change_str_list: list[str] = [
                    _("**Moderator**: {moderator} (`{id}`)").format(
                        moderator=moderator.mention if moderator.in_guild(guild) else cf.inline(text=moderator.name),
                        id=moderator.discord_id,
                    ),
                ]

                if change.reason:
                    change_str_list.append(
                        _("**Reason:** {reason}").format(reason=truncate_string(string=change.reason, max_length=200))
                    )

                if change.duration:
                    change_str_list.append(
                        _("**Duration**: {timedelta}").format(timedelta=cf.humanize_timedelta(change.duration))
                    )

                if change.end_timestamp:
                    change_str_list.append(
                        _("**End Timestamp:** {timestamp} | {relative}").format(
                            timestamp=cf.format_datetime(dt=change.end_timestamp, style=cf.TimestampStyle.SHORT_DATE_AND_TIME),
                            relative=cf.format_datetime(dt=change.end_timestamp, style=cf.TimestampStyle.RELATIVE),
                        )
                    )

                change_str_list.append(
                    _("**Timestamp:** {timestamp} | {relative}").format(
                        timestamp=cf.format_datetime(dt=change.timestamp, style=cf.TimestampStyle.SHORT_DATE_AND_TIME),
                        relative=cf.format_datetime(dt=change.timestamp, style=cf.TimestampStyle.RELATIVE),
                    )
                )

                embed.add_field(
                    name=change.type.title(),
                    value="\n".join(change_str_list),
                    inline=False,
                )
            pages.append(embed)

        return SimpleMenu(pages)

    async def sentinel_history_menu(
        self,
        ctx: commands.GuildContext,
        *,
        targets: list[Targetable | PartialTargetable] | None = None,
        moderators: list[discord.abc.User | PartialUser] | None = None,
        on: date | None = None,
        before: datetime | None = None,
        after: datetime | None = None,
        expired: bool = MISSING,
        resolved: bool = MISSING,
        types: Literal[True] | list[ModerationType | type[ModerationType]] | None = None,
        pagesize: int = 6,
        inline: bool = True,
    ) -> SimpleMenu:
        """Create a SimpleMenu containing all cases within the database that match a given criteria.

        Args:
            ctx: Runtime context used to get various information.
            targets: The targets to filter moderations by.
            moderators: The moderators to filter moderations by.
            on: A specific date to filter moderations by. Only moderations that occurred on this date will be returned.
                Overrides `before` and `after`.
            before: A datetime to filter moderations by. Only moderations that occurred before this datetime will be returned.
            after: A datetime to filter moderations by. Only moderations that occurred after this datetime will be returned.
            expired: A boolean value that filters moderations by whether or not they are expired. `MISSING` prevents filtering.
            resolved: A boolean value that filters moderations by whether or not they are resolved. `MISSING` prevents filtering.
            types: A list of types to filter by. Only moderations that match one of the types provided will be returned.
                If `True` is passed instead of a list, all moderation types will be returned.
                If `None` is passed, moderations will be filtered based on the guild's type configurations.
                As a side effect of this behavior, moderation types that are not currently in the registry
                (e.g. from unloaded cogs) will **not** be included unless you pass `True` to this function.
            pagesize: How many moderations to list on each menu page. Must be a number between and including 1 to 18.
            inline: Whether or not to use inline fields on the menu pages.
                I would recommend making sure `pagesize` is a multiple of 3 if you pass `True`.

        Raises:
            ValueError: If `pagesize` is lower than 1 or higher than 18.
            ContextError: If the context passed through `ctx` does not have an attached guild.

        Returns:
            The created SimpleMenu, which you can then start with [`.start`][redbot.core.utils.views.SimpleMenu.start].
        """
        if not ctx.guild:
            msg = "Cannot be used outside of a guild!"
            raise ContextError(msg)

        max_pagesize = 18
        min_pagesize = 1

        if pagesize > max_pagesize:
            msg = f"'pagesize`' cannot be higher than {max_pagesize}!"
            raise ValueError(msg)

        if pagesize < min_pagesize:
            msg = f"'pagesize' cannot be lower than {min_pagesize}!"
            raise ValueError(msg)

        await set_contextual_locales_from_guild(self.bot, ctx.guild)

        query_construction_before = utcnow()

        guild = await PartialGuild.upsert(ctx.guild)
        where: list[Where | Or] = [Moderation.guild_id == guild.id]

        user_targets: list[PartialUser] = []
        channel_targets: list[PartialChannel] = []
        role_targets: list[PartialRole] = []

        type_map: dict[type | UnionType, tuple[list[Any], Callable[[Any], Any] | None]] = {
            PartialUser: (user_targets, None),
            PartialChannel: (channel_targets, None),
            PartialRole: (role_targets, None),
            discord.abc.User: (user_targets, PartialUser.upsert),
            GuildChannel: (channel_targets, PartialChannel.upsert),  # pyright: ignore[reportAssignmentType]
            discord.Role: (role_targets, PartialRole.upsert),
        }

        for t in targets or []:
            for target_type, (collection, upsert_fn) in type_map.items():
                if isinstance(t, target_type):
                    if upsert_fn is None:
                        collection.append(t)
                    else:
                        collection.append(await upsert_fn(t))
                    break  # don’t check further types once matched

        clauses = []
        if user_targets:
            clauses.append(Moderation.target_user_id.id.is_in([u.id for u in user_targets]))
        if channel_targets:
            clauses.append(Moderation.target_channel_id.id.is_in([c.id for c in channel_targets]))
        if role_targets:
            clauses.append(Moderation.target_role_id.id.is_in([r.id for r in role_targets]))

        if clauses:
            condition = clauses[0]
            for clause in clauses[1:]:
                condition |= clause
            where.append(condition)

        partial_moderators: list[PartialUser] = []
        for m in moderators or []:
            if isinstance(m, discord.abc.User):
                partial_moderators.append(await PartialUser.upsert(user=m))
            else:
                partial_moderators.append(m)

        if partial_moderators:
            where.append(Moderation.moderator_id.is_in([moderator.id for moderator in partial_moderators]))

        raw_types: list[str]
        if isinstance(types, list):
            raw_types = [moderation_type.key for moderation_type in types]
            where.append(Moderation.type_key.is_in(raw_types))
        elif types is not True:
            raw_types = []
            for moderation_type in self.moderation_type_registry.classes():
                if (
                    await self.sentinel_config.type_show_in_history.get(
                        guild=str(guild.discord_id), moderation_type=moderation_type.key
                    )
                    is True
                ):
                    raw_types.append(moderation_type.key)
            where.append(Moderation.type_key.is_in(raw_types))

        if on:
            where.append(Moderation.timestamp == on)
        elif before or after:
            if before:
                where.append(Moderation.timestamp < before)
            if after:
                where.append(Moderation.timestamp > after)

        if expired is True:
            where.append(Moderation.expired.eq(True))
        elif expired is False:
            where.append(Moderation.expired.eq(False))

        if resolved is True:
            where.append(Moderation.resolved.eq(True))
        elif resolved is False:
            where.append(Moderation.resolved.eq(False))

        query_construction_after = utcnow()
        query_construction_delta = query_construction_after - query_construction_before
        query_construction_ms = round(number=query_construction_delta.total_seconds() * 1_000, ndigits=3)

        query_before = utcnow()
        query = Moderation.objects(Moderation.all_related()).where(*where).order_by(Moderation.id, ascending=False)
        if not (moderations := await query):
            return SimpleMenu(
                pages=[cf.error(text=_("No infractions found matching the given query!"))], delete_after_timeout=True
            )

        query_after = utcnow()
        query_delta = query_after - query_before
        query_ms = round(number=query_delta.total_seconds() * 1_000, ndigits=3)

        count = len(moderations)
        pages: list[_ACCEPTABLE_PAGE_TYPES] = []

        total_pages = (count + pagesize - 1) // pagesize
        embed_color = await ctx.embed_color()
        timestamp = utcnow()
        icon_url = None
        if ctx.guild.icon:
            icon_url = ctx.guild.icon.url
        elif self.me.avatar:
            icon_url = self.me.avatar.url

        moderation_deltas: dict[int, timedelta] = {}

        for i in range(0, count, pagesize):
            moderation_before = utcnow()
            embed = discord.Embed(color=embed_color)
            embed.set_author(name=_("Infraction History"), icon_url=icon_url)
            embed.set_footer(
                text=_("Page {current}/{total} | {result_count} Results").format(
                    current=cf.humanize_number(i // pagesize + 1),
                    total=cf.humanize_number(total_pages),
                    result_count=cf.humanize_number(count),
                )
            )
            embed.timestamp = timestamp

            for moderation in moderations[i : i + pagesize]:
                try:
                    target = await moderation.target()
                except UnsetError:
                    self._sentinel_logger.exception("Moderation %i does not have a target!", moderation.id)
                    continue
                except NotFoundError:
                    self._sentinel_logger.exception("Could not find target for moderation %i!", moderation.id)
                    continue

                try:
                    moderator = await moderation.moderator()
                except UnsetError:
                    self._sentinel_logger.exception("Moderation %i does not have a moderator!", moderation.id)
                    continue
                except NotFoundError:
                    self._sentinel_logger.exception("Could not find moderator for moderation %i!", moderation.id)
                    continue

                field_strings: list[str] = [
                    _("**Target:** {target} (`{id}`)").format(
                        target=target.mention if target.in_guild(ctx.guild) else cf.inline(text=target.name), id=target.discord_id
                    ),
                    _("**Moderator**: {moderator} (`{id}`)").format(
                        moderator=moderator.mention if moderator.in_guild(ctx.guild) else cf.inline(text=moderator.name),
                        id=moderator.discord_id,
                    ),
                    _("**Reason:** {reason}").format(
                        reason=cf.inline(
                            text=truncate_string(string=moderation.reason or _("No reason provided."), max_length=140)
                        )
                    ),
                    _("**Timestamp:** {timestamp} | {relative}").format(
                        timestamp=cf.format_datetime(dt=moderation.timestamp, style=cf.TimestampStyle.LONG_DATE_AND_TIME),
                        relative=cf.format_datetime(dt=moderation.timestamp, style=cf.TimestampStyle.RELATIVE),
                    ),
                ]

                if moderation.duration:
                    if moderation.expired:
                        _value = _("**Duration:** {timedelta} | Expired").format(
                            timedelta=cf.humanize_timedelta(value=moderation.duration)
                        )
                    elif moderation.end_timestamp:
                        _value = _("**Duration:** {timedelta} | {end_timestamp}").format(
                            timedelta=cf.humanize_timedelta(value=moderation.duration),
                            end_timestamp=cf.format_datetime(dt=moderation.end_timestamp, style=cf.TimestampStyle.RELATIVE),
                        )
                    else:
                        _value = _("**Duration:** {timedelta}").format(timedelta=cf.humanize_timedelta(value=moderation.duration))
                    field_strings.append(_value)

                if moderation.resolved:
                    field_strings.extend([
                        _("**Resolved:** True"),
                        _("**Resolve Reason:** `{reason}`").format(
                            reason=truncate_string(string=moderation.resolve_reason or "No reason provided.", max_length=140)
                        ),
                    ])

                try:
                    moderation_type = moderation.type
                except RegistryKeyError:
                    moderation_type = None

                if moderation_type:
                    field_strings.extend([
                        f"**{title(meta.human_name)}:** {meta_value}"
                        for meta in [meta for meta in moderation_type.metadata if meta.show_in_history]
                        if (meta_value := await meta.fetch_from_moderation(moderation, self.bot))
                    ])

                embed.add_field(
                    name=_("Case {id} ({type})").format(id=cf.humanize_number(moderation.id), type=title(moderation.type_key)),
                    value="\n".join(field_strings),
                    inline=inline,
                )

                moderation_after = utcnow()
                moderation_deltas[moderation.id] = moderation_after - moderation_before
            pages.append(embed)

        total_moderation_time = sum(moderation_deltas.values(), timedelta(0))
        moderation_ms = total_moderation_time.total_seconds() * 1_000
        total_ms = query_construction_ms + query_ms + moderation_ms
        moderation_average = (total_moderation_time / len(moderation_deltas)).total_seconds() * 1_000
        moderation_highest_key, moderation_highest_value = max(
            moderation_deltas.items(),
            key=lambda kv: kv[1],
            default=(0, timedelta(0)),
        )
        moderation_highest_ms = moderation_highest_value.total_seconds() * 1_000

        self._sentinel_logger.trace(
            f"History query completed in {total_ms:,.3f} ms with {len(moderations):,} moderations retrieved! "
            f"Query construction time: '{query_construction_ms:,.3f} ms' "
            f"Query time: '{query_ms:,.3f} ms' "
            f"Moderation iteration time: '{moderation_ms:,.3f} ms' "
            f"Longest moderation iteration: 'Moderation {moderation_highest_key:,} with {moderation_highest_ms:,.3f} ms' "
            f"Avg. time per moderation: '{moderation_average:,.3f} ms'"
        )

        return SimpleMenu(pages=pages, timeout=240, use_select_menu=True)

    @discord.ext.tasks.loop(minutes=1)
    async def _sentinel_monitor_expiry_loop(self) -> None:
        await self.bot.wait_until_red_ready()
        loop = SentinelCog._sentinel_expiry_loop
        if loop is None or not loop.is_running():
            SentinelCog._sentinel_expiry_loop = self._sentinel_expiry_handler
            try:
                SentinelCog._sentinel_expiry_loop.start()
                self._sentinel_logger.debug("Took over expiry loop!")
            except RuntimeError:  # Race condition?
                pass

    @discord.ext.tasks.loop(minutes=1)
    async def _sentinel_expiry_handler(self) -> None:
        await self.bot.wait_until_red_ready()
        current_time = utcnow()
        global_num = 0
        global_err_num = 0

        guilds = [
            await PartialGuild.upsert(guild) for guild in self.bot.guilds if not await self.bot.cog_disabled_in_guild(self, guild)
        ]
        moderations = (
            await Moderation.objects()
            .where(
                Moderation.end_timestamp.is_not_null(),
                Moderation.end_timestamp <= utcnow(),
                Moderation.expired.eq(False),
                Moderation.guild_id.is_in([guild.id for guild in guilds]),
            )
            .order_by(Moderation.guild_id)
        )
        expirable_moderations: dict[int, list[Moderation]] = defaultdict(list)
        for moderation in moderations:
            try:
                if moderation.type.can_expire:
                    expirable_moderations[moderation.guild_id].append(moderation)
            except ValueError:  # noqa: PERF203
                pass
            except RegistryKeyError:
                self._sentinel_logger.warning(
                    "Attempted to expire a moderation with an invalid moderation type: %s", moderation.type_key
                )
                global_err_num += 1

        for guild in guilds:
            time_per_guild = utcnow()
            num = 0
            err_num = 0

            for moderation in expirable_moderations[guild.id]:
                try:
                    await moderation.expire(self)
                    num += 1
                except NotReadyError:  # noqa: PERF203
                    pass
                except ValueError as err:
                    self._sentinel_logger.exception(err)
                    err_num += 1
                except NotImplementedError as err:
                    self._sentinel_logger.trace(
                        "Attempted to expire a moderation with a non-expirable moderation type!", exc_info=err
                    )
                    err_num += 1

            per_guild_completion_time = utcnow() - time_per_guild
            self._sentinel_logger.trace(
                "Completed expiry loop for guild '%s' (%s) in %sms with %s successful cases and %s errors.",
                guild.name,
                guild.guild_id,
                round(number=per_guild_completion_time.total_seconds() * 1000, ndigits=3),
                num,
                err_num,
            )
            global_num += num
            global_err_num += err_num

        completion_time = utcnow() - current_time
        self._sentinel_logger.debug(
            "Completed expiry loop for %s guilds in %sms with %s successful cases and %s errors.",
            len(guilds),
            round(number=completion_time.total_seconds() * 1000, ndigits=3),
            global_num,
            global_err_num,
        )
