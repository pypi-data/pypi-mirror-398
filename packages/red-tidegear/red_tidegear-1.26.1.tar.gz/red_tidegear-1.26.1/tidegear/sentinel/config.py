# SPDX-FileCopyrightText: 2025 cswimr <copyright@csw.im>
# SPDX-License-Identifier: MPL-2.0

"""Configuration schema for Sentinel."""

from typing import TYPE_CHECKING, Annotated, ClassVar, Self

import discord
from red_commons import logging
from typing_extensions import override

from tidegear.config import BaseConfigSchema, ConfigMeta, CustomConfigGroup, CustomConfigOption, GuildConfigOption, JsonableType
from tidegear.pydantic import HttpUrl

if TYPE_CHECKING:
    from tidegear.sentinel.moderation_type import ModerationType

_ModerationTypeGroup = CustomConfigGroup(name="types", identifiers=["guild_id", "moderation_type"])


class SentinelConfigSchema(BaseConfigSchema):
    """Sentinel's internal configuration.

    This is accessible within cogs utilizing Sentinel through [`self.sentinel_config`][tidegear.sentinel.cog.SentinelCog].
    """

    version: ClassVar[int] = 1
    _cog_name: ClassVar[str] = "TidegearSentinel"
    _identifier: ClassVar[int] = 294518358420750336

    default_reason: Annotated[GuildConfigOption[str], ConfigMeta(default="No reason provided.")]
    """The default reason to use for moderations when no reason is provided by the moderator."""
    show_moderator: Annotated[GuildConfigOption[bool], ConfigMeta(default=True)]
    """Whether or not to provide the name/ID of the moderator when sending a moderation case embed to a moderated user."""
    use_discord_permissions: Annotated[GuildConfigOption[bool], ConfigMeta(default=True)]
    """Whether or not Discord role permissions should be taken into account when determining if someone can moderate another user.

    When this is enabled, moderators must have the permissions required by the given moderation type to moderate a user.

    When this is disabled, these permission requirements are removed for the moderator.
    The bot must still have the required permissions.
    """
    respect_hierarchy: Annotated[GuildConfigOption[bool], ConfigMeta(default=True)]
    """Whether or not Discord role positions should be taken into account when determining if someone can moderate another user.

    When this is disabled, moderators can moderate anyone whose top role is beneath the bot's top role,
    assuming they pass the other required checks.
    """
    dm_users: Annotated[GuildConfigOption[bool], ConfigMeta(default=True)]
    """Whether or not to direct message users when they're moderated. Can be overridden by individual moderation invocations."""
    log_channel: Annotated[GuildConfigOption[int | None], ConfigMeta(default=None)]
    """The guild channel that should be used for logging moderations."""
    immune_roles: Annotated[GuildConfigOption[list[int]], ConfigMeta(default=[])]
    """A list of role IDs that should be immune from moderation actions in this guild."""
    auto_evidenceformat: Annotated[GuildConfigOption[bool], ConfigMeta(default=False)]
    """Whether or not to automatically send an ephemeral message
    to the moderator containing information about the moderation action.

    If the moderation command being used is not an Application Command,
    the message will be sent to the moderator's direct messages.
    """
    support_message: Annotated[GuildConfigOption[str | None], ConfigMeta(default=None)]
    """A custom message to include in the embed sent to users when they are moderated."""
    button_label: Annotated[GuildConfigOption[str | None], ConfigMeta(default=None)]
    """A label to use for a custom button included in moderation embeds."""
    button_url: Annotated[GuildConfigOption[HttpUrl | None], ConfigMeta(default=None)]
    """A link to attach to the custom button included in moderation embeds."""

    # Types
    type_default_reason: Annotated[CustomConfigOption[str | None], ConfigMeta(default=None), _ModerationTypeGroup]
    """A default reason to apply specifically for this moderation type.

    If set, this value overrides the global `default_reason` when a moderator does not provide one.
    """

    type_show_in_history: Annotated[
        CustomConfigOption[bool],
        ConfigMeta(default=True, help="Whether or not to show moderations of this type in history invocations by default."),
        _ModerationTypeGroup,
    ]
    """Whether or not to show moderations of this type in history invocations by default.

    Note that passing `True` to [`sentinel_history_menu`][tidegear.sentinel.cog.SentinelCog.sentinel_history_menu]'s
    `types` parameter will show moderations of any type, including those where this option is set to `False`.
    """

    type_show_moderator: Annotated[CustomConfigOption[bool | None], ConfigMeta(default=None), _ModerationTypeGroup]
    """Whether or not the moderator should be shown for this specific moderation type.

    If set, this value overrides the global `show_moderator` setting.
    """

    type_use_discord_permissions: Annotated[CustomConfigOption[bool | None], ConfigMeta(default=None), _ModerationTypeGroup]
    """Whether or not Discord role permissions should be considered for this moderation type.

    If set, this value overrides the global `use_discord_permissions` setting.
    """

    type_dm_users: Annotated[CustomConfigOption[bool | None], ConfigMeta(default=None), _ModerationTypeGroup]
    """Whether or not users should be directly messaged for this moderation type.

    If set, this value overrides the global `dm_users` setting.
    """

    type_support_message: Annotated[CustomConfigOption[str | None], ConfigMeta(default=None), _ModerationTypeGroup]
    """A custom message to include in moderation embeds for this specific moderation type.

    If set, this value overrides the global `support_message` setting.
    """

    type_button_label: Annotated[CustomConfigOption[str | None], ConfigMeta(default=None), _ModerationTypeGroup]
    """A label to use for a custom button included in moderation embeds for this moderation type.

    If set, this value overrides the global `button_label` setting.
    """

    type_button_url: Annotated[CustomConfigOption[HttpUrl | None], ConfigMeta(default=None), _ModerationTypeGroup]
    """A link to attach to the custom button for this moderation type.

    If set, this value overrides the global `button_url` setting.
    """

    @override
    @classmethod
    async def init(cls, *, logger: logging.RedTraceLogger | None = None) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        return await super().init(cls._cog_name, cls._identifier, logger=logger)

    async def get_type_config_with_fallback(
        self,
        config: GuildConfigOption[JsonableType],
        *,
        guild: discord.Guild | int,
        moderation_type: "type[ModerationType] | ModerationType | str",
    ) -> JsonableType:
        """Return the configuration value for a specific moderation type, falling back to the guild-level value when the type-specific option is None.

        Args:
            config: The [guild-scoped][tidegear.config.options.GuildConfigOption] configuration option you want to retrieve a value for.
                The [type-scoped][tidegear.config.CustomConfigOption] configuration option must be named `type_{config.key}`.
            guild: The guild you're looking up a configuration value for.
            moderation_type: The moderation type you're looking up a configuration value for.
                If this is a string, it must be the key of the moderation type.

        Raises:
            AttributeError: If the `type_{config.key}` attribute does not exist on the parent configuration schema.
            TypeError: If `type_{config.key}` does exist, but is either not a [`CustomConfigOption`][tidegear.config.CustomConfigOption],
                or does not have a matching annotation with `config`. A "matching annotation" is the generic annotation of `config`,
                with `| None` appended. Note that type aliases such as [`Optional[T]`][typing.Optional] or [`Union[T, None]`][typing.Union]
                will not be treated as equal here, because the comparison is structural rather than semantic.
            ValueError: If `type_{config.key}` does exist, but does not have the correct group.

        Returns:
            The retrieved value, typed accordingly to `config`'s generic type.
        """  # noqa: E501
        type_attr_name = f"type_{config.key}"
        type_config = getattr(self, type_attr_name, None)
        if not type_config:
            msg = f"This configuration schema does not have a configuration option named {type_attr_name!r}."
            raise AttributeError(msg)
        if not isinstance(type_config, CustomConfigOption):
            msg = f"The {type_attr_name!r} attribute exists on this configuration schema, but is not a CustomConfigOption."
            raise TypeError(msg)
        if type_config.group != _ModerationTypeGroup:
            msg = (
                f"The {type_attr_name!r} attribute exists on this configuration schema "
                "and is a CustomConfigOption, but is not part of the correct custom group."
            )
            raise ValueError(msg)
        if type_config.__pydantic_fields__["default"].annotation != config.__pydantic_fields__["default"].annotation | None:  # pyright: ignore[reportOptionalOperand]
            msg = (
                f"The {type_attr_name!r} attribute exists on this configuration schema, "
                f"but does not have matching annotations with {config.key!r}."
            )
            raise TypeError(msg)

        if isinstance(guild, discord.Guild):
            guild_id = str(guild.id)
        elif isinstance(guild, int):
            guild_id = str(guild)

        if not isinstance(moderation_type, str):
            moderation_type = moderation_type.key

        type_value = await type_config.get(guild_id=guild_id, moderation_type=moderation_type)
        if type_value is not None:
            return type_value

        return await config.get(guild)
