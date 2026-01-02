# SPDX-FileCopyrightText: 2025 cswimr <copyright@csw.im>
# SPDX-License-Identifier: MPL-2.0

"""Exception definitions."""

from tidegear.exceptions import TidegearError


class ReadOnlyConfigError(TidegearError):
    """Raised whenever attempting to modify a read-only configuration value without passing `force=True`."""


class MalformedConfigError(TidegearError):
    """Raised whenever a configuration entry is malformed or corrupted, resulting in a typechecking violation."""


class SchemaRegistrationError(TidegearError):
    """Raised whenever a configuration schema fails to register or fails validation in some way."""


class ConfigMigrationError(TidegearError):
    """Raised whenever a configuration schema's migration fails."""
