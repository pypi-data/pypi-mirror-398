# SPDX-FileCopyrightText: 2025 cswimr <copyright@csw.im>
# SPDX-License-Identifier: MPL-2.0

"""This module contains exceptions used within Sentinel and consuming cogs."""

from tidegear.exceptions import TidegearError


class HandlerError(TidegearError):
    """Raised whenever a moderation handler wants to show an error message to the end user."""

    send_to_end_user = True


class LoggedHandlerError(TidegearError):
    """Raised whenever a moderation handler wants to show an error message to the end user, while still logging that error for bot owners to see."""

    send_to_end_user = True


class UpsertError(TidegearError):
    """Raised whenever an upsert operation falis."""


class UnsetError(TidegearError):
    """Raised when attempting to access a database entry that is unset."""


class NotReadyError(TidegearError):
    """Raised when attempting to expire a moderation case that isn't ready to expire."""
