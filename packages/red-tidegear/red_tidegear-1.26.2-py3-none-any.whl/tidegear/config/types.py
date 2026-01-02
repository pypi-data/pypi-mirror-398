# SPDX-FileCopyrightText: 2025 cswimr <copyright@csw.im>
# SPDX-License-Identifier: MPL-2.0

# pyright: reportInvalidTypeForm=information

"""Types used by Tidegear's config module."""

import datetime
import decimal
import enum
import pathlib
import types
import typing
import uuid

import pydantic
import typing_extensions

Jsonable = typing_extensions.TypeAliasType(
    "Jsonable",
    "str | bytes | bool | int | float | decimal.Decimal | pathlib.Path | uuid.UUID | datetime.datetime | datetime.date \
    | datetime.time | datetime.timedelta | types.NoneType | enum.Enum | typing.Sequence[Jsonable] \
    | typing.Mapping[str, Jsonable] | pydantic.BaseModel | pydantic.AnyUrl \
    | pydantic.networks.IPvAnyAddress | pydantic.networks.IPvAnyInterface | pydantic.networks.IPvAnyNetwork",
)
"""
Type alias representing an object that either is natively JSON-compatible, or can easily be converted to be JSON-compatible.

Supported types:

- [`str`][]
- [`bytes`][]
- [`bool`][]
- [`int`][]
- [`float`][]
- [`decimal.Decimal`][]
- [`pathlib.Path`][]
- [`uuid.UUID`][]
- [`datetime.datetime`][]
- [`datetime.date`][]
- [`datetime.time`][]
- [`datetime.timedelta`][]
- [`types.NoneType`][]
- [`enum.Enum`][]
- [`typing.Sequence`][] of `Jsonable` ([`list`][], [`tuple`][])
- [`typing.Mapping`][] with [`str`][] keys and `Jsonable` values ([`dict`][])
- [`pydantic.BaseModel`][] (including [`tidegear.pydantic.BaseModel`][])
- [`pydantic.AnyUrl`][] (including [`tidegear.pydantic.HttpUrl`][])
- [`pydantic.networks.IPvAnyAddress`][]
- [`pydantic.networks.IPvAnyInterface`][]
- [`pydantic.networks.IPvAnyNetwork`][]
"""


JsonableType = typing.TypeVar("JsonableType", bound=Jsonable)
"""TypeVar bound to [`Jsonable`][tidegear.config.Jsonable]."""
