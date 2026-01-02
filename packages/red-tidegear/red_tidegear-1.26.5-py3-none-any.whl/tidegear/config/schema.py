# SPDX-FileCopyrightText: 2025 cswimr <copyright@csw.im>
# SPDX-License-Identifier: MPL-2.0

"""Definition for the BaseConfigSchema class."""

import ast
import inspect
import re
from functools import cached_property, lru_cache
from typing import Annotated, Any, ClassVar, Mapping, Self, get_args, get_origin, get_type_hints

from discord.utils import MISSING
from red_commons import logging
from redbot.core import config as red_config

from tidegear.config.exceptions import ConfigMigrationError, SchemaRegistrationError
from tidegear.config.options import CustomConfigGroup, CustomConfigOption, GlobalConfigOption
from tidegear.config.types import Jsonable
from tidegear.pydantic import BaseModel
from tidegear.utils import class_overrides_attribute


class ConfigMeta(BaseModel):
    """Metadata class for use in type annotations for [`GlobalConfigOption`][tidegear.config.options.GlobalConfigOption] and its subclasses."""  # noqa: E501

    default: Jsonable
    internal: bool = False
    read_only: bool = False
    help: str | None = MISSING


class BaseConfigSchema:
    """A configuration schema for a Tidegear cog.

    Warning:
        Subclasses of this class should not have method names that start with `tidegear_` or `_tidegear_`.
        They also should not have dunder methods whose names begin with `__tidegear`.
        Methods with these names are reserved for future functionality within Tidegear.
    """

    version: ClassVar[int] = 1
    """The version of this config schema. Used for migrations.

    Danger:
        If you change this value, **you must override [`run_migrations`][tidegear.config.schema.BaseConfigSchema.run_migrations]
        to update the version number yourself.** Tidegear deliberately does not automatically handle updating schema version
        numbers to prevent accidental data corruption. If you are not making a breaking change that requires a migration for users
        on the previous config version, you do not need to, and should not, change this value.

        In the circumstance where this value is incremented,
        [`run_migrations`][tidegear.config.schema.BaseConfigSchema.run_migrations] is not overridden or does not update the
        version number, and the cog utilizing the configuration schema is updated and loaded, any attempts to initialize the
        configuration schema through [`init`][tidegear.config.schema.BaseConfigSchema.init] will result in an exception being
        raised and initialization failing. This will most likely make your cog fail to load, if you initialize the
        configuration schema within your [`cog_load`][tidegear.cog.Cog.cog_load] method.
    """

    cog_name: str
    """The name of the cog to register this configuration schema under. Can be any arbitrary string."""
    identifier: int
    """The identifier to register this configuration schema under."""
    logger: logging.RedTraceLogger | None
    """An optional logger to use internally."""
    config_version: Annotated[GlobalConfigOption[int], ConfigMeta(default=-1, internal=True, read_only=True)]
    """An internal reference for a config schema's version, used for migrations.
    Override `version` to set your config schema's version, not this.
    """

    def __init__(self, *, cog_name: str, identifier: int, logger: logging.RedTraceLogger | None = None) -> None:
        self.cog_name = cog_name
        self.identifier = identifier
        self.logger = logger

        result: dict[str, dict[str, Any]] = {}
        for k, v in self.registered_options.items():
            setattr(self, k, v)
            result[k] = {**v.model_dump(mode="python", exclude={"key"}), "type": v.type(), "scope": v.scope}

        if self.logger:
            self.logger.trace("Registered configuration: %s", result)

    @property
    def config(self) -> red_config.Config:
        """Return a [`Config`][redbot.core.config.Config] instance for accessing methods not re-implemented within this class."""
        return self._tidegear_get_config(self.cog_name, self.identifier, logger=self.logger)

    @property
    def unsafe_config(self) -> red_config.Config:
        """Return an unsafe [`Config`][redbot.core.config.Config] instance for accessing methods not re-implemented within this class.

        Prefer [`config`][tidegear.config.BaseConfigSchema.config] instead when possible,
        as that sets `force_registration=True`, which is safer and recommended by upstream.
        """  # noqa: E501
        return self._tidegear_get_config(self.cog_name, self.identifier, force_registration=False, logger=self.logger)

    @property
    def implements_migrations(self) -> bool:
        """Returns whether or not this schema overrides the [`run_migrations`][tidegear.config.schema.BaseConfigSchema.run_migrations] method."""  # noqa: E501
        return class_overrides_attribute(
            child=self.__class__, parent=BaseConfigSchema, attribute=BaseConfigSchema.run_migrations.__name__
        )

    @cached_property
    def registered_options(self) -> dict[str, GlobalConfigOption]:
        """Return a dictionary containing all of the configuration options registered by this schema."""
        return self._tidegear_register_config(self.config, self.logger)

    # not sure if this has a notable performance impact,
    # but Config objects don't really have any risk for becoming stale, so it's harmless
    @classmethod
    @lru_cache()
    def _tidegear_get_config(
        cls, cog_name: str, identifier: int, *, force_registration: bool = True, logger: logging.RedTraceLogger | None
    ) -> red_config.Config:
        config = red_config.Config.get_conf(
            cog_instance=None, cog_name=cog_name, identifier=identifier, force_registration=force_registration
        )
        cls._tidegear_register_config(config, logger)
        return config

    @classmethod
    async def init(cls, cog_name: str, identifier: int, *, logger: logging.RedTraceLogger | None = None) -> Self:
        """Register the configuration schema and return an instance of the schema for accessing attributes.

        Args:
            cog_name: The cog name to register the configuration schema under.
            identifier: The identifier to register the configuration schema under.
            logger: An optional logger to pass into the created schema instance.

        Returns:
            The registered configuration schema.
        """
        if logger:
            logger = logger.getChild("config")
        self = cls(cog_name=cog_name, identifier=identifier, logger=logger)
        await self._tidegear_run_migrations()
        return self

    @classmethod
    def _tidegear_validate_annotation(
        cls, config: red_config.Config, attribute: str, logger: logging.RedTraceLogger | None
    ) -> GlobalConfigOption | None:
        hints = get_type_hints(cls, include_extras=True)
        if attribute not in hints:
            msg = f"Missing annotation for key {attribute!r}."
            raise AttributeError(msg)

        annotation = hints[attribute]
        if get_origin(annotation) is not Annotated:
            return None

        type_tuple = get_args(annotation)
        value_type = type_tuple[0]
        if not issubclass(value_type, GlobalConfigOption):
            return None

        is_custom = issubclass(value_type, CustomConfigOption)

        meta: ConfigMeta | None = None
        custom_group: CustomConfigGroup | None = None
        for i in type_tuple:
            if isinstance(i, ConfigMeta):
                meta = i
            if isinstance(i, CustomConfigGroup):
                custom_group = i
        if not meta:
            msg = f"{attribute!r} must be annotated with a 'ConfigMeta()' instance."
            raise TypeError(msg)
        if is_custom and not custom_group:
            msg = f"{attribute!r} must be annotated with a `CustomConfigGroup()` instance."
            raise TypeError(msg)

        extra: Mapping[str, Any] = {}

        if is_custom and custom_group:
            extra["group"] = custom_group

        if meta.help is MISSING:
            try:
                meta.help = cls._tidegear_get_fallback_help_from_attribute_docstring(attribute)
            except Exception:
                meta.help = None

        return value_type(
            config=config,
            key=attribute,
            default=meta.default,
            internal=meta.internal,
            read_only=meta.read_only,
            help=meta.help,
            logger=logger,
            **extra,
        )

    @staticmethod
    def _tidegear_get_classdef(obj: type) -> ast.ClassDef:
        class_source = inspect.getsource(obj)
        tree = ast.parse(class_source)

        for element in ast.walk(tree):
            if isinstance(element, ast.ClassDef):
                return element

        msg = f"Couldn't find class definition for class {obj!r}. Is it a class?"
        raise ValueError(msg)

    @classmethod
    def _tidegear_get_fallback_help_from_attribute_docstring(cls, attribute: str) -> str | None:
        for _cls in cls.__mro__:
            if not issubclass(_cls, BaseConfigSchema):
                continue

            tree = cls._tidegear_get_classdef(_cls)
            last_attribute: str | None = None

            for expr in tree.body:
                if last_attribute == attribute and isinstance(expr, ast.Expr):
                    value = expr.value
                    if not isinstance(value, ast.Constant):
                        break
                    if not isinstance(value.value, str):
                        break
                    docstring = value.value.strip()
                    collapsed = re.sub(r" +", " ", docstring)
                    return re.sub(r"\n ", "\n", collapsed)

                if isinstance(expr, ast.AnnAssign):
                    last_attribute = ast.unparse(expr.target)

        return None

    @classmethod
    def _tidegear_register_config(
        cls, config: red_config.Config, logger: logging.RedTraceLogger | None
    ) -> dict[str, GlobalConfigOption]:
        d: dict[str, GlobalConfigOption] = {}
        errors: dict[str, Exception] = {}

        for _cls in reversed(cls.__mro__):
            if not issubclass(_cls, BaseConfigSchema):
                continue

            for attribute, annotation in _cls.__annotations__.items():
                try:
                    if not annotation:
                        msg = f"Field {attribute!r} on class {_cls!r} does not have an annotation!"
                        raise TypeError(msg)

                    config_value = cls._tidegear_validate_annotation(config, attribute, logger)
                    if config_value is None:
                        continue

                    config_value.register()
                    d[attribute] = config_value
                except Exception as err:
                    errors[attribute] = err

        if errors:
            msg = "Schema registration failed for the following keys:\n" + "\n".join([
                f"  - {key}: {error.__class__.__qualname__}: {error}" for key, error in errors.items()
            ])
            raise SchemaRegistrationError(msg)

        return d

    async def run_migrations(self, version: int) -> None:
        """Run migrations for this configuration schema.

        This is called internally whenever [`init`][tidegear.config.schema.BaseConfigSchema.init] is called.
        As such, you do not have to call this manually. Errors thrown by this method will be re-raised,
        and any modifications to the configuration will be rolled back automatically.

        Args:
            version: The current version of the configuration schema.
        """
        pass

    async def _tidegear_run_migrations(self) -> None:
        identifier_data = red_config.IdentifierData(self.cog_name, self.config.unique_identifier, "", (), (), 0)
        group = red_config.Group(identifier_data, defaults={}, driver=self.config._driver, config=self.config)  # noqa: SLF001

        before = await group.all()
        try:
            version = await self._tidegear_ensure_config_version()

            if self.implements_migrations:
                await self.run_migrations(version)
                if self.logger:
                    self.logger.info("Successfully ran migrations for `%s` (`%s`).", self.cog_name, self.__class__.__qualname__)

            if (current_version := await self.config_version.get()) != self.version:
                msg = (
                    f"`{self.cog_name}` (`{self.__class__.__qualname__}`)'s config version "
                    f"({self.version}) does not match the current version ({current_version})."
                )
                raise ConfigMigrationError(msg)

        except ConfigMigrationError as err:
            await group.set(before)
            raise err
        except Exception as err:
            await group.set(before)
            msg = (
                "Encountered an unexpected error when running migrations "
                f"for `{self.cog_name}` (`{self.__class__.__qualname__}`)."
            )
            raise ConfigMigrationError(msg) from err

    async def _tidegear_ensure_config_version(self) -> int:
        if not isinstance(self.version, int):
            msg = f"The `version` attribute on the `{self.__class__.__qualname__}` class is not an integer."
            raise TypeError(msg)
        if self.version <= 0:
            msg = f"The `version` attribute on the `{self.__class__.__qualname__}` class is not a positive, non-zero integer."
            raise ValueError(msg)

        if await self.config_version.get() == self.config_version.default:
            await self.config_version.set(self.version, force=True)

        return await self.config_version.get()
