# SPDX-FileCopyrightText: 2025 cswimr <copyright@csw.im>
# SPDX-License-Identifier: MPL-2.0

"""A collection of useful utility functions and classes, to reduce repetitiveness between cogs."""

import functools
import inspect
import os
import random
import secrets
import string
import typing
import warnings
from contextlib import contextmanager
from importlib.resources import as_file, files
from importlib.util import find_spec
from typing import TYPE_CHECKING, Any, Callable, Generator, Literal, TypeVar, overload

import discord
from discord.utils import MISSING
from pydantic_extra_types.semantic_version import SemanticVersion
from red_commons.logging import RedTraceLogger
from redbot.core.bot import Red

from tidegear import chat_formatting as cf
from tidegear import constants
from tidegear.exceptions import ArgumentError, ArgumentTypeError
from tidegear.version import version

if TYPE_CHECKING:
    from functools import _Wrapped

_T = TypeVar("_T")


def deprecated_alias(
    *,
    new_func: Callable,
    old_name: str,
    module_name: str = "tidegear",
    current_version: SemanticVersion | str = version,
    removal_version: SemanticVersion | str | None = None,
    kwarg_map: dict[str, str] | None = None,
) -> "_Wrapped[..., Any, ..., Any]":
    """Create a deprecated alias for a function.

    Args:
        new_func: The new function to forward calls to.
        old_name: The deprecated function name.
        module_name: The name of the module to mention in the deprecation warning.
            Only does anything if `removal_version` is also passed.
        current_version: The current version of whatever module the deprecated function is coming from.
            For Tidegear cogs, this would be [`tidegear.Cog.metadata.version`][tidegear.metadata.CogMetadata].
        removal_version: The version in which the alias will be removed.
        kwarg_map: Optional mapping from old kwarg names to new kwarg names.

    Returns:
        The wrapped alias function.
    """
    if isinstance(current_version, str):
        current_version = SemanticVersion.validate_from_str(current_version)
    if isinstance(removal_version, str):
        removal_version = SemanticVersion.validate_from_str(removal_version)

    @functools.wraps(new_func)
    def wrapper(*args, **kwargs):
        if removal_version and current_version >= removal_version:
            msg = (
                f"'{old_name}' is deprecated, and is no longer available beginning in '{module_name}>={removal_version}'."
                f" Please use '{new_func.__module__}.{new_func.__name__}' instead."
            )
            raise AttributeError(msg)

        if kwarg_map is not None:
            for old_kw, new_kw in list(kwarg_map.items()):
                if old_kw in kwargs:
                    if new_kw in kwargs:
                        msg = f"{old_name} received both '{old_kw}' (deprecated) and '{new_kw}'"
                        raise TypeError(msg)
                    kwargs[new_kw] = kwargs.pop(old_kw)

        warnings.warn(
            (
                f"'{old_name}' is deprecated{f', and will be removed in {module_name} {removal_version}' if removal_version else ''}. "  # noqa: E501
                f"Please use '{new_func.__module__}.{new_func.__name__}' instead."
            ),
            DeprecationWarning,
            stacklevel=2,
        )
        return new_func(*args, **kwargs)

    wrapper.__name__ = old_name
    return wrapper


def dashboard_page(
    *,
    name: str | None = None,
    methods: tuple[Literal["HEAD", "GET", "OPTIONS", "PATCH", "POST", "PATCH", "DELETE"], ...] = ("GET",),
    context_ids: list[str] | None = None,
    required_kwargs: list[str] | None = None,
    optional_kwargs: list[str] | None = None,
    requires_owner: bool = False,
    hidden: bool | None = None,
) -> Callable[..., Callable[..., Any]]:
    """Mark a function as a Dashboard page.

    See the upstream documentation [here](https://red-web-dashboard.readthedocs.io/en/latest/third_parties.html) for more info.

    Args:
        name: The name of the Dashboard page.
        methods: The methods that this Dashboard page should accept.
        context_ids: Manually specify required context IDs.
            This will be inferred automatically based on your function arguments if not provided.
        required_kwargs: Manually specify required keyword arguments (query parameters).
            This will be inferred automatically based on your function arguments if not provided..
        optional_kwargs: Manually specify optional keyword arguments (query parameters).
            This will be inferred automatically based on your function arguments if not provided.
        requires_owner: Whether or not the user must be logged in as a bot owner to view this page.
        hidden: Whether or not this page appears in the Third Parties UI in the Dashboard.
            Automatically set to `True` if there are any required keyword arguments (query parameters).

    Returns:
        The passed function with the `__dashboard_decorator_params__` attribute set on it.
    """
    params: dict[str, Any] = {
        "name": name,
        "methods": methods,
        "is_owner": requires_owner,
        "hidden": hidden,
        "context_ids": context_ids,
        "required_kwargs": required_kwargs,
        "optional_kwargs": optional_kwargs,
    }

    def decorator(func: typing.Callable) -> Callable[..., Any]:
        func.__dashboard_decorator_params__ = ([], params)  # pyright: ignore[reportFunctionMemberAccess]
        return func

    return decorator


@contextmanager
def set_env(
    key: str,
    value: str | None,
    logger: RedTraceLogger | None = None,
) -> Generator[None, Any, None]:
    """Temporarily set or unset an environment variable, then restore old value or delete on exit.

    Example:
        ```python
        import os
        from tidegear.utils import set_env


        def hello_world():
            return os.environ.get("HELLO_WORLD")


        with set_env(key="HELLO_WORLD", value="hello world"):
            print(hello_world())  # hello world

        print(hello_world())  # None
        ```

    Args:
        key: The environment variable to set.
        value: The content you want to set the environment variable to.
            If this is None, the environment variable will be deleted if it exists.
        logger: The logger to use to log the environment variables. Logs at `TRACE` level.
    """
    old_value = os.environ.get(key)
    if logger:
        logger.trace("Setting '%s' -> '%s'", key, value)
    if value is not None:
        os.environ[key] = value
    else:
        os.environ.pop(key, None)

    try:
        yield
    finally:
        if logger:
            logger.trace("Restoring '%s' -> '%s'", key, old_value)
        if old_value is not None:
            os.environ[key] = old_value
        else:
            os.environ.pop(key, None)


def class_overrides_attribute(child: type, parent: type, attribute: str) -> bool:
    """Check whether or not a child class overrides an attribute from a parent class.

    Args:
        child (type): The child class to check against.
        parent (type): The parent class to check against.
        attribute (str): The name of the attribute to check for.

    Raises:
        TypeError: If the `child` class is not a subclass of `parent`.
        AttributeError: If `attribute` does not exist on `parent`.

    Returns:
        Whether or not the attribute specified is overridden on `child`.
    """
    if not issubclass(child, parent):
        msg = f"{child.__name__} is not a subclass of {parent.__name__}!"
        raise TypeError(msg)

    child_attr = inspect.getattr_static(obj=child, attr=attribute, default=None)

    try:
        parent_attr = inspect.getattr_static(obj=parent, attr=attribute)
    except AttributeError as e:
        msg = f"Parent class {parent} does not have an attribute named {attribute}!"
        raise AttributeError(msg) from e

    return child_attr is not parent_attr


async def get_embed_color_from_interaction(bot: Red, interaction: discord.Interaction) -> discord.Color:
    """Retrieve the bot's configured embed color for an interaction's location.

    Args:
        bot: The bot object to use to retrieve the color.
        interaction: The interaction to retrieve a color for.

    Returns:
        The retrieved embed color.
    """
    location = interaction.channel
    if not isinstance(location, discord.abc.Messageable):
        location = interaction.user
    return await bot.get_embed_color(location)


def get_bool_emoji(value: bool | None) -> discord.Emoji | discord.PartialEmoji:
    """Return a unicode emoji based on a boolean value.

    Example:
        ```python
        from tidegear.utils import get_bool_emoji

        print(get_bool_emoji(True))  # ✅
        print(get_bool_emoji(False))  # 🚫
        print(get_bool_emoji(None))  # ❓️
        ```

    Args:
        value: The boolean value to check against.

    Returns:
        The corresponding emoji.
    """
    match value:
        case True:
            return constants.TRUE
        case False:
            return constants.FALSE
        case _:
            return constants.NONE


def get_asset_as_file(
    *, package: str = "tidegear.assets", filename: str, description: str | None = None, spoiler: bool = MISSING
) -> discord.File:
    """Create a [`discord.File`][] from a file within a Python package.

    Args:
        package: The package to retrieve the file from.
        filename: The name of the file you'd like to retrieve. Does not support subpaths.
        description: The description of the uploaded file on Discord, used by screen readers.
        spoiler: Whether or not to mark the image as a spoiler on Discord.

    Raises:
        ImportError: Raised if the package provided cannot be found.
        FileNotFoundError: Raised if the filename provided does not exist within the provided package.

    Returns:
        The resulting object.
    """
    if not find_spec(name=package):
        msg = f"Unable to find a package named '{package}'!"
        raise ImportError(msg)

    asset = files(package=package).joinpath(filename)
    with as_file(asset) as path:
        if not path.exists():
            msg = f"Asset at path '{path}' does not exist! Is there a file named '{filename}' in the '{package}' package?"
            raise FileNotFoundError(msg)
        return discord.File(fp=path, filename=filename, description=description, spoiler=spoiler)


def random_string(length: int, *, characters: str = string.ascii_letters + string.digits) -> str:
    """Create a random string using the given characters.

    Danger:
        This uses the [`random`][] module. As such, it is **not** "random" enough to be considered cryptographically secure,
        and should not be used to generate passwords, secret keys, security tokens, or anything of the sort.

        If you need to generate a cryptographically-secure string,
        please use [`random_secret_string`][tidegear.utils.random_secret_string] instead.

    Args:
        length: The length of the string to generate.
        characters: The characters to use in the string.

    Returns:
        The generated string.
    """
    return "".join(random.choices(population=characters, k=length))


def random_secret_string(length: int, *, characters: str = string.ascii_letters + string.digits) -> str:
    """Create a random string using the given characters.

    This function uses the [`secrets`][] module. As such, it **is** "random" enough to be considered cryptographically secure.
    This is in contrast to the [`random_string`][tidegear.utils.random_string] function, which uses [`random`][].

    Args:
        length: The length of the string to generate.
        characters: The characters to use in the string.

    Returns:
        The generated string.
    """
    return "".join(secrets.choice(seq=characters) for _ in range(length))


def title(string: str, /) -> str:
    """Replace any underscores in a string with spaces, then titlecase it.

    Args:
        string: The string to modify.

    Returns:
        The modified string.
    """
    return string.replace("_", " ").title()


def call_with_kwargs(func: typing.Callable[..., _T], /, *args: typing.Any, **kwargs: typing.Any) -> _T:
    """Call a function while filtering a keyword arguments dictionary.

    Args:
        func: The function to call.
        *args: The positional arguments to use.
        **kwargs: The keyword arguments to use.

    Returns:
        The return of the function.
    """
    sig = inspect.signature(func)
    allowed = {
        name
        for name, param in sig.parameters.items()
        if param.kind
        in {
            inspect.Parameter.KEYWORD_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        }
    }
    return func(*args, **{k: v for k, v in kwargs.items() if k in allowed})


@overload
async def send_error(
    messageable: discord.abc.Messageable | discord.Message,
    /,
    *,
    func: Callable[[str], str] = ...,
    edit_original: bool = ...,
    **kwargs: Any,
) -> discord.Message: ...
@overload
async def send_error(
    messageable: discord.Interaction, /, *, func: Callable[[str], str] = ..., edit_original: typing.Literal[True], **kwargs: Any
) -> discord.InteractionMessage: ...
@overload
async def send_error(
    messageable: discord.Interaction,
    /,
    *,
    func: Callable[[str], str] = ...,
    edit_original: typing.Literal[False] = ...,
    **kwargs: Any,
) -> discord.InteractionMessage | discord.WebhookMessage: ...


async def send_error(
    messageable: discord.abc.Messageable | discord.Interaction | discord.Message,
    /,
    *,
    func: Callable[[str], str] = cf.error,
    edit_original: bool = False,
    **kwargs: Any,
) -> discord.Message | discord.InteractionMessage | discord.WebhookMessage:
    """Send a message with the content wrapped in an error function.

    Args:
        messageable: The context to send the message to, or an existing message to edit.
        func: The function to use to wrap the message.
        edit_original: Determines behavior when `messageable` is a [`discord.Interaction`][] that has already been responded to.
            If this argument is `True`, the passed interaction's original response message will be edited instead.
            If this argument is `False`, a follow-up message will be sent instead.
        **kwargs: Additional keyword arguments to pass to [`Messageable.send()`][discord.abc.Messageable.send].

    Returns:
        The sent message.
    """
    kwargs.pop("wait", None)  # pop "wait" so as to not break `discord.Interaction.followup.send`.
    kwargs.setdefault(
        "ephemeral", True
    )  # error messages should usually be ephemeral if possible, so default to them being ephemeral.

    if content := get_kwarg(kwargs, argument="content", default=None):
        kwargs["content"] = func(content)

    if isinstance(messageable, discord.Message):
        return await call_with_kwargs(messageable.edit, **kwargs)

    if isinstance(messageable, discord.Interaction):
        if not messageable.response.is_done():
            response = await call_with_kwargs(messageable.response.send_message, **kwargs)
            # Will always be an InteractionMessage, as we don't launch an activity here.
            return typing.cast(discord.InteractionMessage, response.resource)

        if edit_original:
            return await call_with_kwargs(messageable.edit_original_response, **kwargs)

        return await call_with_kwargs(messageable.followup.send, wait=True, **kwargs)

    # My typechecker was complaining that `messageable` is somehow still typehinted as a `discord.Message`,
    # even though that branch was already handled earlier in the method. Doesn't do this with interactions, not sure what's wrong.
    # Screw it, let's cast :P
    return await call_with_kwargs(typing.cast(discord.abc.Messageable, messageable).send, **kwargs)


async def noop() -> None:
    """Do nothing. Serves as an asynchronous no-operation call."""
    return


@overload
def get_kwarg(
    kwargs: dict[str, Any],
    /,
    argument: str,
    *,
    default: Any = ...,
    expected_type: type[_T] | tuple[type[_T], ...],
) -> _T: ...
@overload
def get_kwarg(
    kwargs: dict[str, Any],
    /,
    argument: str,
    *,
    default: Any = ...,
    expected_type: None = None,
) -> Any: ...


def get_kwarg(
    kwargs: dict[str, Any], /, argument: str, *, default: Any = MISSING, expected_type: type | tuple[type, ...] | None = None
) -> Any:
    """Retrieve a keyword argument from a dictionary with optional type validation.

    This function is a strict helper for fetching values from a `kwargs` dictionary.
    It raises an error if the key is missing and no default is provided, and it
    can also enforce that the value matches a specified type or tuple of types.

    Args:
        kwargs: A dictionary of keyword arguments, typically from `**kwargs`.
        argument: The name of the key to retrieve from `kwargs`.
        default: Optional default value to return if the key is not present.
        expected_type: Optional type or tuple of types to validate the value against.

    Raises:
        ArgumentError: If `argument` is missing and `default` is not provided.
        ArgumentTypeError: If `expected_type` is provided and the value does not match the specified type(s).

    Returns:
        The value associated with `argument` in `kwargs`, or the `default` if provided.
            If `expected_type` is specified, the return type is guaranteed to match it.
    """
    try:
        value = kwargs[argument]
    except KeyError:
        if default is not MISSING:
            value = default
        else:
            msg = f"Caller didn't pass {argument} argument"
            raise ArgumentError(msg)

    if expected_type is not None:
        if not isinstance(value, expected_type):
            expected_names = (
                ", ".join(t.__name__ for t in expected_type) if isinstance(expected_type, tuple) else expected_type.__name__
            )
            msg = f"Argument '{argument}' must be of type {expected_names}, got {type(value).__name__}"
            raise ArgumentTypeError(msg)

    return value
