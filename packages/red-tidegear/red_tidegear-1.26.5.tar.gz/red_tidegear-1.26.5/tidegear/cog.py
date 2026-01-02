# SPDX-FileCopyrightText: 2025 cswimr <copyright@csw.im>
# SPDX-License-Identifier: MPL-2.0

"""This module contains a subclass of [`commands.Cog`][redbot.core.commands.Cog].
Cogs using this library should inherit from the [`tidegear.Cog`][] class within this module.
"""

import asyncio
import hashlib
import logging as py_logging
import re
import string
import time
from datetime import datetime, timedelta
from pathlib import Path
from sys import version
from types import SimpleNamespace
from typing import Any

import aiohttp
import discord
import humanize
import orjson
import pypiwrap
from aiohttp import (
    ClientSession,
    TraceConfig,
    TraceRequestEndParams,
    TraceRequestExceptionParams,
    TraceRequestRedirectParams,
    TraceRequestStartParams,
)
from aiohttp.typedefs import StrOrURL
from discord.utils import MISSING, utcnow
from pydantic_extra_types.semantic_version import SemanticVersion
from pypiwrap.objects.pypi import Project
from red_commons.logging import RedTraceLogger, getLogger
from redbot import __version__ as red_version
from redbot.core import app_commands, commands, data_manager
from redbot.core.bot import Red
from redbot.core.i18n import Translator, set_contextual_locales_from_guild
from redbot.logging import RotatingFileHandler
from typing_extensions import override
from yarl import URL

import tidegear.aiohttp
from tidegear import chat_formatting as cf
from tidegear import constants
from tidegear.exceptions import TidegearError
from tidegear.metadata import CogMetadata
from tidegear.tidegear import TidegearCog
from tidegear.types import GuildChannel
from tidegear.utils import random_string, send_error
from tidegear.version import meta

_ = Translator("TidegearCog", __file__)


class Cog(commands.Cog):  # noqa: PLR0904
    """The base Cog class that cogs using Tidegear should inherit from.

    This class contains a couple of useful utility methods.
    Keep in mind that you **must** have a `meta.json` file in your cog's
    [data folder][redbot.core.data_manager.bundled_data_path] in order to use this cog class.

    Warning:
        Subclasses of this class should not have method names that start with `tidegear_` or `red_`.
        They also should not have dunder methods whose names begin with `__tidegear` or `__red`.
        Methods with these names are reserved for future functionality within Tidegear or Red, respectively.

    Example:
        ```python
        from redbot.core.bot import Red
        from redbot.core import commands
        import tidegear

        class MyCog(tidegear.Cog):
        \"\"\"My first Tidegear cog.\"\"\"

            def __init__(self, bot: Red) -> None:
                super().__init__(bot)

            @commands.command()
            async def hello(self, ctx: commands.Context) -> None:
                await ctx.send(f"Hello from {self.metadata.name}!")
        ```

    Args:
        bot: The bot object passed to the cog during loading.

    Attributes:
        application_emojis: The application emojis you've provided to upload with the cog. Uploads happen during cog loading.
        bot: The bot object passed to the cog during loading.
        bundled_data_path: The cog's bundled data path.
            This is retrieved from [`redbot.core.data_manager.bundled_data_path`][] at cog initialization time.
            You should **never** write to this directory from your code,
            as this directory points to the `data` directory within your own cog's source code.
        logger: A logger automatically populated with the name of your cog repository and the cog's actual classname.
        me: A user object representing the bot user.
        metadata: A Python object representing the contents of your cog's `meta.json` file.
        session: A session that may be used for making HTTP requests.
            Opened during cog loading and closed automatically during cog unloading.
        runtime_data_path: The cog's runtime data path.
            This is retrieved from [`redbot.core.data_manager.cog_data_path`][] at cog initialization time.
            You can safely write to this directory from your code without issue.

    Raises:
        FileNotFoundError: Raised if this class is loaded as a cog without a`meta.json` file
            being present in the cog's [data folder][redbot.core.data_manager.bundled_data_path].
    """

    def __init__(self, bot: Red) -> None:
        super().__init__()
        self.bot: Red = bot
        # this is fine because Red itself will fail if the client isn't logged in way before this cog would be loaded
        self.me: discord.ClientUser = self.bot.user  # pyright: ignore[reportAttributeAccessIssue]

        self.bundled_data_path: Path = data_manager.bundled_data_path(self)
        self.runtime_data_path: Path = data_manager.cog_data_path(self)
        self._tidegear_data_path: Path = data_manager.cog_data_path(raw_name="Tidegear")

        meta_path = self.bundled_data_path / "meta.json"
        if not meta_path.exists():
            msg = f"There is no metadata file located at {meta_path}!"
            raise FileNotFoundError(msg)
        self.metadata: CogMetadata = CogMetadata.from_json(self.__cog_name__, meta_path)

        self.logger: RedTraceLogger = getLogger(f"red.{self.metadata.repository.name}.{self.metadata.name}")
        self._tidegear_logger: RedTraceLogger = self.logger.getChild("tidegear")
        # purposefully don't add a file handler to the rest logger, it'll inherit the cog one
        self._rest_logger: RedTraceLogger = self.logger.getChild("rest")

        self.tidegear_setup_file_logger(self._tidegear_logger, self._tidegear_data_path / "logs", "Tidegear")
        self.tidegear_setup_file_logger(self.logger, self.runtime_data_path / "logs", self.metadata.name)

        self.session: aiohttp.ClientSession = MISSING  # set in cog_load

        self._pypi_project: Project | None = None
        self._pypi_project_last_fetched: datetime | None = None

        self._application_emoji_path = self.bundled_data_path / "emojis"
        self._application_emoji_prefix: str = self.__cog_name__.lower()
        self.application_emojis: dict[str, discord.Emoji] = {}

    @override
    async def cog_load(self) -> None:
        """Run asynchronous code during the cog loading process.

        Subclasses may override this if they want special asynchronous loading behaviour.
        The `__init__` special method does not allow asynchronous code to run
        inside it, thus this is helpful for setting up code that needs to be asynchronous.

        Danger:
            Please ensure that you call `await super().cog_load()` within your overridden method,
            as this method is implemented within Tidegear's Cog class and is expected to be ran.
        """
        if not self.bot.get_cog("TidegearCog"):
            await self.bot.add_cog(TidegearCog(self.bot))
            self.logger.debug("Loaded TidegearCog.")

        self.session = ClientSession(
            base_url=await self.tidegear_session_base_url(),
            headers=await self.tidegear_session_headers(),
            trace_configs=[self.tidegear_session_trace_config()],
            json_serialize=self.tidegear_session_json_serializer,
            response_class=tidegear.aiohttp.ClientResponse,
        )
        self._rest_logger.verbose("Opened aiohttp session.")

        if self.provides_application_emojis:
            self._tidegear_logger.trace("Application emojis are provided by this cog. Uploading emojis to Discord.")
            await self.add_application_emojis()

    @override
    async def cog_unload(self) -> None:
        """Run asynchronous code during the cog unloading process.

        Danger:
            Please ensure that you call `await super().cog_unload()` within your overridden method,
            as this method is implemented within Tidegear's Cog class and is expected to be ran.
        """
        if self.session and not self.session.closed:
            await self.session.close()
            self._rest_logger.verbose("Closed aiohttp session.")

        self.tidegear_close_logger(self.logger)
        self.tidegear_close_logger(self._tidegear_logger)

    def _tidegear_pypi_version(self) -> SemanticVersion:
        ttl = timedelta(hours=6)

        if self._pypi_project_last_fetched and self._pypi_project:
            if self._pypi_project_last_fetched + ttl <= utcnow():
                return SemanticVersion.validate_from_str(self._pypi_project.version)

        with pypiwrap.PyPIClient() as pypi:
            self._pypi_project = pypi.get_project("red-tidegear")
            self._pypi_project_last_fetched = utcnow()
            return SemanticVersion.validate_from_str(self._pypi_project.version)

    async def tidegear_session_headers(self) -> dict[str, str]:
        """Get a dictionary of HTTP request headers. Includes a user agent by default.

        Danger:
            This method is called by [`cog_load`][tidegear.Cog.cog_load] when creating an [`aiohttp.ClientSession`][].
            This means that whatever this method returns will be sent as HTTP headers
            on any HTTP request made with the pre-configured ClientSession.

        Returns:
            The default headers for this cog's [`session`][aiohttp.ClientSession].
        """
        return {"User-Agent": self.tidegear_user_agent()}

    def tidegear_user_agent(self) -> str:
        """Get the user agent for HTTP requests made by this cog.

        Contains the bot's hashed user ID, the cog's name and version, the Tidegear version,
        the Red-DiscordBot version, and the Python version w/ compilation details.

        Returns:
            The cog's user agent.
        """
        hashed_id = hashlib.sha512(str(self.me.id).encode(), usedforsecurity=False).hexdigest()[:10]
        return (
            f"BotHashedId/{hashed_id} {self.metadata.name}/{self.metadata.version} "
            f"Tidegear/{meta.version} Red-DiscordBot/{red_version} Python/{version}"
        )

    async def tidegear_session_base_url(self) -> StrOrURL | None:  # noqa: PLR6301
        """Get the base URl for HTTP requests using this cog's ClientSession.

        This will always return None if it is not overridden.

        Returns:
            The base URL to use, or None if no base URL is necessary.
        """
        return None

    def tidegear_session_json_serializer(self, value: Any) -> str:  # noqa: PLR6301
        """JSON Serializer for use in the cog's ClientSession.

        This exists so that we can use orjson instead of json, which provides a performance improvement in theory.

        Args:
            value: The value to be serialized.

        Returns:
            The serialized value.
        """
        return orjson.dumps(value).decode("utf-8")

    def tidegear_session_trace_config(self) -> TraceConfig:
        """Create a [TraceConfig][aiohttp.TraceConfig] and add the built-in Tidegear trace handlers to it.

        Returns:
            The configured TraceConfig instance, for use with [aiohttp.ClientSession][].
        """
        trace_config = TraceConfig()
        trace_config.on_request_start.append(self._tidegear_session_on_request_start)
        trace_config.on_request_redirect.append(self._tidegear_session_on_request_redirect)
        trace_config.on_request_end.append(self._tidegear_session_on_request_end)
        trace_config.on_request_exception.append(self._tidegear_session_on_request_exception)
        return trace_config

    @staticmethod
    def _tidegear_trace_get_duration(end_time: float, trace_config_ctx: SimpleNamespace) -> str:
        start_time = getattr(trace_config_ctx, "start_time", None)
        if isinstance(start_time, float):
            return f"request took approximately {end_time - start_time:.4f}s"
        return "failed to get request duration"

    @staticmethod
    def _tidegear_trace_get_urls(end_url: URL, trace_config_ctx: SimpleNamespace) -> str:
        urls = getattr(trace_config_ctx, "urls", [])
        if not isinstance(urls, list) or len(urls) <= 1:
            return f"'{end_url}'"

        redirect_chain = [f"'{url}'" for url in urls[:-1]]

        full_chain = redirect_chain + [f"'{end_url}'"]

        return " >> ".join(full_chain)

    @staticmethod
    async def _tidegear_session_on_request_start(
        session: ClientSession, trace_config_ctx: SimpleNamespace, params: TraceRequestStartParams
    ) -> None:
        trace_config_ctx.start_time = time.monotonic()
        trace_config_ctx.urls = [params.url]

    @staticmethod
    async def _tidegear_session_on_request_redirect(
        session: ClientSession, trace_config_ctx: SimpleNamespace, params: TraceRequestRedirectParams
    ) -> None:
        redirect_target = params.response.headers.get("Location", None)
        if redirect_target:
            redirect_target = URL(redirect_target)
            urls = getattr(trace_config_ctx, "urls", None)
            if not isinstance(urls, list):
                trace_config_ctx.urls = [params.url, redirect_target]
                return
            urls.append(redirect_target)
            trace_config_ctx.urls = urls

    async def _tidegear_session_on_request_end(
        self, session: ClientSession, trace_config_ctx: SimpleNamespace, params: TraceRequestEndParams
    ) -> None:
        end_time = time.monotonic()
        url = self._tidegear_trace_get_urls(params.url, trace_config_ctx)
        self._rest_logger.trace(
            "%s %s -> %s (%s)",
            params.method,
            url,
            params.response.status,
            self._tidegear_trace_get_duration(end_time, trace_config_ctx),
        )

    async def _tidegear_session_on_request_exception(
        self, session: ClientSession, trace_config_ctx: SimpleNamespace, params: TraceRequestExceptionParams
    ) -> None:
        end_time = time.monotonic()
        url = self._tidegear_trace_get_urls(params.url, trace_config_ctx)
        self._rest_logger.error(
            "%s request to %s encountered an exception (%s)",
            params.method,
            url,
            self._tidegear_trace_get_duration(end_time, trace_config_ctx),
            exc_info=params.exception,
        )

    def tidegear_setup_file_logger(
        self, logger: RedTraceLogger, directory: Path, stem: str, *, max_bytes: int = 1_000_000, backup_count: int = 5
    ) -> None:
        """Add a `RotatingFileHandler` to the given logger, pointing to a file in the specified directory.

        The created handler will inherit the logging level of the passed logger.

        If a handler with the same `stem` and `directory` already exists on the logger, this function does nothing.

        Warning:
            Tidegear (and Sentinel) automatically calls this method on the bundled `self.logger`
            and the internal loggers (`_tidegear_logger` and `_sentinel_logger`).
            The [`cog_load`][tidegear.Cog.cog_load] and  [`cog_unload`][tidegear.Cog.cog_unload] methods
            automatically handle handler creation and cleanup for you, for the built-in loggers specifically.

            Please make sure you clean up the added handler yourself if you use this method!
            You can do so using [`tidegear_close_logger`][tidegear.Cog.tidegear_close_logger].

        Args:
            logger: The logger to attach the handler to.
            directory: The directory where the log file should be stored. Will be created if it doesn't exist.
            stem: The base filename (without extension) for the log file.
            max_bytes: The maximum size in bytes of the log file before it is rotated.
            backup_count: The number of rotated log files to keep.
        """
        for h in logger.handlers:
            if (
                isinstance(h, RotatingFileHandler)
                and getattr(h, "stem", None) == stem
                and Path(getattr(h, "directory", "")) == directory
            ):
                return

        directory.mkdir(parents=True, exist_ok=True)

        handler = RotatingFileHandler(
            stem=stem, directory=directory, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        formatter = py_logging.Formatter("[{asctime}] {levelname} [{name}] {message}", datefmt="%Y-%m-%d %H:%M:%S", style="{")
        handler.setFormatter(formatter)
        handler.setLevel(logger.getEffectiveLevel())

        logger.addHandler(handler)
        self._tidegear_logger.trace("Added RotatingFileHandler to logger %s, pointing to %s.log", logger, directory / stem)

    def tidegear_close_logger(self, logger: RedTraceLogger) -> None:
        """Close any currently open `RotatingFileHandler`s for the given logger.

        Args:
            logger: The logger to close handlers from.
        """
        for handler in logger.handlers.copy():
            if isinstance(handler, RotatingFileHandler):
                self._tidegear_logger.trace("Removing %s handler from logger %s", handler, logger)
                handler.close()
                logger.removeHandler(handler)

    @override
    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Format the help string based on values in context.

        The steps are (currently, roughly) the following:

        - Get the cog class's localized help text.
        - Substitute `[p]` for [`ctx.clean_prefix`][discord.ext.commands.Context.clean_prefix].
        - Substitute `[botname]` for [`ctx.me.display_name`][discord.abc.User.display_name].
        - Add cog metadata from `self.metadata`.

        More steps may be added at a later time.

        Args:
            ctx: The context to substitute values for.

        Returns:
            The resulting help text.
        """
        from tidegear import chat_formatting as cf  # noqa: PLC0415

        base = (super().format_help_for_context(ctx) or "").rstrip("\n") + "\n"

        parts: list[str] = [base]

        parts.append(
            _("**Cog Version:** [{version}]({url})").format(version=self.metadata.version, url=self.metadata.repository.url)
        )

        author_label = _("**Authors:**") if len(self.metadata.authors) >= 2 else _("**Author:**")  # noqa: PLR2004
        parts.append(f"{author_label} {cf.humanize_list([author.markdown for author in self.metadata.authors])}")

        if self.metadata.documentation is not None:
            parts.append(_("**Documentation:** {url}").format(url=self.metadata.documentation))

        tidegear_version = _("**Tidegear Version:** {link}").format(link=meta.markdown)
        if meta.version < self._tidegear_pypi_version():
            tidegear_version += _("\n{i} New version available: {version}").format(
                i=constants.INFO, version=self._tidegear_pypi_version()
            )
        parts.append(tidegear_version)

        return "\n".join(parts)

    @override
    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Simple command error handler to make error messages utilize [`send_error()`][tidegear.utils.send_error]."""
        await set_contextual_locales_from_guild(self.bot, ctx.guild)

        if (nested_error := getattr(error, "original", None)) and isinstance(nested_error, Exception):
            return await self.cog_command_error(ctx, nested_error)
        if isinstance(
            error, (commands.MissingRequiredArgument, commands.MissingRequiredAttachment, commands.MissingRequiredFlag)
        ):
            await self.bot.send_help_for(ctx, help_for=ctx.command)
            return None
        if isinstance(error, (commands.BadArgument, commands.CommandOnCooldown, commands.MaxConcurrencyReached)):
            await send_error(ctx, content=str(error))
            return None
        if isinstance(error, TidegearError) and error.send_to_end_user is True:
            await error.send(ctx)
            return None
        exc_id = random_string(length=10, characters=string.ascii_lowercase + string.digits)
        await send_error(
            ctx,
            content=_("Encountered an internal error, please report this to the bot owner! Exception ID: `{exc_id}`").format(
                exc_id=exc_id
            ),
        )
        self.logger.error(
            "Uncaught exception in command '%s'! Exception ID: '%s'", ctx.command.qualified_name, exc_id, exc_info=error
        )
        return None

    @override
    async def cog_app_command_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """Simple application command error handler to make error messages utilize [`send_error()`][tidegear.utils.send_error]."""
        await set_contextual_locales_from_guild(self.bot, interaction.guild)

        if (nested_error := getattr(error, "original", None)) and isinstance(nested_error, Exception):
            return await self.cog_app_command_error(interaction, nested_error)
        if isinstance(
            error,
            (app_commands.AppCommandError, commands.BadArgument, commands.CommandOnCooldown, commands.MaxConcurrencyReached),
        ):
            await send_error(interaction, content=str(error))
            return None
        if isinstance(error, TidegearError) and error.send_to_end_user is True:
            await error.send(interaction)
            return None
        exc_id = random_string(length=10, characters=string.ascii_lowercase + string.digits)
        await send_error(
            interaction,
            content=_("Encountered an internal error, please report this to the bot owner! Exception ID: `{exc_id}`").format(
                exc_id=exc_id
            ),
        )
        if interaction.command:
            self.logger.error(
                "Uncaught exception in application command '%s'! Exception ID: '%s'",
                interaction.command.name,
                exc_id,
                exc_info=error,
            )
        else:
            self.logger.error(
                "Uncaught exception in the callback for interaction %d! Exception ID: '%s'",
                interaction.id,
                exc_id,
                exc_info=error,
            )
        return None

    @property
    def provides_application_emojis(self) -> bool:
        """Check whether or not this cog ships with application emojis.

        Returns:
            Whether or not this cog ships with application emojis.
                If this is `True`, Tidegear will automatically upload the provided emojis to Discord upon cog load.
        """
        if not self._application_emoji_path.exists():
            return False
        if not self._application_emoji_path.is_dir():
            return False
        if sum((1 for f in self._application_emoji_path.iterdir() if f.is_file()), start=0) != 0:
            return True
        return False

    def _get_emoji_name(self, name: str) -> str:
        return (self._application_emoji_prefix + "_" + name).replace("-", "_").replace(" ", "_").lower()

    def get_application_emoji(self, name: str) -> discord.Emoji | None:
        """Retrieve an application emoji from its filename.

        Args:
            name: The filename of the emoji you'd like to retrieve. Must originate from this cog.

        Raises:
            NotImplementedError: Raised if [`self.provides_application_emojis`][tidegear.Cog.provides_application_emojis]
                evaluates to `False`, indicating that this cog does not ship with any application emojis to fetch.

        Returns:
            The retrieved emoji matching the provided filename, or `None` if it could not be found.
        """
        if not self.provides_application_emojis:
            msg = f"Cog '{self.__cog_name__}' does not provide application emojis!"
            raise NotImplementedError(msg)
        name = self._get_emoji_name(name)
        return self.application_emojis.get(name, None)

    async def add_application_emojis(self) -> dict[str, discord.Emoji]:
        """Upload all of the application emojis that ship with a cog to Discord.

        This is automatically ran by [`cog_load`][tidegear.Cog.cog_load]
        if your cog [ships with application emojis][tidegear.Cog.provides_application_emojis],
        so you shouldn't usually have to run this yourself.

        Raises:
            NotImplementedError: Raised if [`self.provides_application_emojis`][tidegear.Cog.provides_application_emojis]
                evaluates to `False`, indicating that this cog does not ship with any application emojis to upload.

        Returns:
            A dictionary containing the cog's emojis and their names as keys.
                Consider using [`self.get_application_emoji`][tidegear.Cog.get_application_emoji]
                to access uploaded emojis instead of checking keys manually.
        """
        if not self.provides_application_emojis:
            msg = f"Cog '{self.__cog_name__}' does not provide application emojis!"
            raise NotImplementedError(msg)

        regex_pattern = re.compile(r"^[a-zA-Z0-9_]+$")
        emojis: dict[str, discord.Emoji] = {}
        existing_application_emojis = await self.bot.fetch_application_emojis()

        for file in self._application_emoji_path.iterdir():
            if not file.is_file():
                continue

            if (suffix := file.suffix.strip(".").upper()) not in constants.ALLOWED_EMOJI_EXTENSIONS:
                self.logger.error(
                    "Emoji file '%s' has an unsupported extension: '%s'\nSupported extensions: '%s'",
                    file,
                    suffix,
                    cf.humanize_list(items=[*constants.ALLOWED_EMOJI_EXTENSIONS], style="unit"),
                )
                continue

            if (filesize := file.stat().st_size) > constants.MAX_EMOJI_FILESIZE:
                self.logger.error(
                    "Emoji file '%s' is too large to be uploaded to Discord! (%s > %s)",
                    file,
                    humanize.naturalsize(filesize),
                    humanize.naturalsize(constants.MAX_EMOJI_FILESIZE),
                )
                continue

            emoji_name = self._get_emoji_name(name=file.stem)
            if not regex_pattern.fullmatch(emoji_name):
                self._tidegear_logger.error(
                    "Invalid emoji name '%s'! Emoji names must match regex pattern '%s'.", emoji_name, regex_pattern
                )
                continue

            if (length := len(emoji_name)) > constants.MAX_EMOJI_NAME_CHARACTERS:
                self._tidegear_logger.error(
                    "Skipping application emoji '%s' due to exceeding the name length limit. (%i > %i)",
                    emoji_name,
                    length,
                    constants.MAX_EMOJI_NAME_CHARACTERS,
                )
                continue

            if conflicting_emoji := next((e for e in existing_application_emojis if e.name == emoji_name), None):
                self._tidegear_logger.trace("Skipping application emoji '%s', due to conflicting name.", emoji_name)
                emojis[emoji_name] = conflicting_emoji
                continue

            try:
                with open(file, mode="rb") as f:
                    emoji = await self.bot.create_application_emoji(name=emoji_name, image=f.read())
                emojis[emoji_name] = emoji
                existing_application_emojis.append(emoji)
                self._tidegear_logger.info("Successfully uploaded application emoji '%s' to Discord.", emoji_name)
            except discord.HTTPException:
                self._tidegear_logger.exception("Failed to upload application emoji '%s' from file '%s'!", emoji_name, file)
                continue

        self.application_emojis = emojis
        return emojis

    async def delete_application_emojis(self, fetch: bool = False) -> list[discord.Emoji]:
        """Delete all application emojis associated with this cog.

        Args:
            fetch: Whether or not to fetch all application emojis from the Discord API.
                If this is not `True`, the application emoji cache on this cog class will be used instead.

        Returns:
            The application emojis that were deleted.
        """
        if fetch:
            to_delete = await self.bot.fetch_application_emojis()
        else:
            to_delete = self.application_emojis.values()

        deleted_emojis: list[discord.Emoji] = []

        for emoji in to_delete:
            if not emoji.name.startswith(self._application_emoji_prefix):
                continue

            if not emoji.is_application_owned():
                self._tidegear_logger.warning(
                    "Application emoji '%s' with id '%s' does not appear to be an application emoji.", emoji.name, emoji.id
                )
                continue

            deleted_emojis.append(emoji)
            await emoji.delete()
            self._tidegear_logger.debug("Deleted application emoji '%s' with id '%s'.", emoji.name, emoji.id)
        return deleted_emojis

    async def get_enabled_guilds(self) -> list[discord.Guild]:
        """Return a list of guilds where this cog is enabled.

        Returns:
            A list of guilds where this cog is enabled.
        """
        sem = asyncio.Semaphore(20)

        async def is_enabled(guild: discord.Guild) -> bool:
            async with sem:
                try:
                    is_disabled = await self.bot.cog_disabled_in_guild(self, guild)
                    return not is_disabled
                except Exception:
                    return False

        results = await asyncio.gather(*(is_enabled(guild) for guild in self.bot.guilds))

        return [guild for guild, enabled in zip(self.bot.guilds, results) if enabled]

    async def get_or_fetch_user(self, user_id: int) -> discord.User:
        """Retrieve a user from the internal cache, or fetch it if it cannot be found.

        Use this sparingly, as the [`fetch_user`][discord.ext.commands.Bot.fetch_user] endpoint has a strict ratelimit.

        Args:
            user_id: The ID of the user to retrieve.

        Returns:
            The retrieved user.
        """
        user = self.bot.get_user(user_id)
        if not user:
            user = await self.bot.fetch_user(user_id)
        return user

    async def get_or_fetch_guild(self, guild_id: int) -> discord.Guild:
        """Retrieve a guild from the internal cache, or fetch it if it cannot be found.

        Use this sparingly, as the [`fetch_guild`][discord.ext.commands.Bot.fetch_guild] endpoint has a strict ratelimit.

        Args:
            guild_id: The ID of the guild to retrieve.

        Returns:
            The retrieved guild.
        """
        guild = self.bot.get_guild(guild_id)
        if not guild:
            guild = await self.bot.fetch_guild(guild_id)
        return guild

    @staticmethod
    async def get_or_fetch_channel(guild: discord.Guild, channel_id: int) -> GuildChannel:
        """Retrieve a channel or thread from the internal cache, or fetch it if it cannot be found.

        Use this sparingly, as the [`fetch_channel`][discord.Guild.fetch_channel] endpoint has a strict ratelimit.

        Args:
            guild: The guild to use to retrieve the channel.
            channel_id: The ID of the channel to retrieve.

        Returns:
            The retrieved channel or thread.
        """
        channel = guild.get_channel_or_thread(channel_id)
        if not channel:
            channel = await guild.fetch_channel(channel_id)
        return channel
