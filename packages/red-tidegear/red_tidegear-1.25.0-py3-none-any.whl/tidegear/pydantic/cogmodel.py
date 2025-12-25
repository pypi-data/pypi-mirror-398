# SPDX-FileCopyrightText: 2025 cswimr <copyright@csw.im>
# SPDX-License-Identifier: MPL-2.0

"""Define a CogModel wrapper."""

from pydantic import Field
from red_commons.logging import RedTraceLogger

from tidegear.cog import Cog
from tidegear.pydantic.basemodel import BaseModel


class CogModel(BaseModel):
    """Wrapper around [`BaseModel`][tidegear.pydantic.BaseModel] that adds a `cog` attribute.

    Attributes:
        cog: The cog that instantiated this model.
    """

    cog: Cog = Field(exclude=True)

    @property
    def logger(self) -> RedTraceLogger:
        """Get the cog's logger."""
        return self.cog.logger
