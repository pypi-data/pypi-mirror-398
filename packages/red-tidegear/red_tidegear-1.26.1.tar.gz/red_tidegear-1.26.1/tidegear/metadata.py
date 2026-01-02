# SPDX-FileCopyrightText: 2025 cswimr <copyright@csw.im>
# SPDX-License-Identifier: MPL-2.0

"""This module contains metadata objects for keeping track of cog information."""

from pathlib import Path
from typing import Self

import orjson
from pydantic import Field
from pydantic_extra_types.semantic_version import SemanticVersion
from typing_extensions import override

from tidegear.pydantic import BaseModel, HttpUrl


class User(BaseModel):
    """Model representing a User, primarily for storing cog authors."""

    name: str
    """The user's username."""
    profile: HttpUrl | None = Field(default=None, alias="url")
    """The user's preferred social networking profile, should usually be a GitHub or other software forge link."""

    @override
    def __str__(self) -> str:
        """Return the user's name."""
        return self.name

    @property
    def markdown(self) -> str:
        """Return the user's name within a Markdown masked link pointing to their profile URL."""
        return f"[{self.name}]({self.profile})"


class Repository(BaseModel):
    """Model representing a git repository."""

    owner: str
    """The name of the repository owner."""
    name: str
    """The name of the repository itself."""
    url: HttpUrl
    """A link pointing to the repository."""

    @override
    def __str__(self) -> str:
        """Return the repository's owner and name."""
        return f"{self.owner}/{self.name}"

    @property
    def issues(self) -> HttpUrl:
        """Return a URl pointing to the repository's issues page."""
        return self.url / "issues"

    @property
    def markdown(self) -> str:
        """Return the repository's owner and name, wrapped in a Markdown masked link."""
        return f"[{self.owner}/{self.name}]({self.url})"

    def slug(self, sep: str = "/") -> str:
        """Return the repository's lowercased owner and name.

        Args:
            sep: The separator to put between the owner and name.
        """
        return f"{self.owner.lower()}{sep}{self.name.lower()}"


class CogMetadata(BaseModel):
    """Convenient metadata model containing some useful information regarding the loaded cog."""

    name: str
    """The name of the cog's class - NOT the cog's package name."""
    version: SemanticVersion
    """The version of the cog, provided in the cog's `meta.json`."""
    authors: list[User]
    """The authors of the cog, provided in the cog's `meta.json`."""
    repository: Repository
    """The repository information provided in the cog's `meta.json`."""
    documentation: HttpUrl | None = None
    """An optional link to the cog's documentation, provided in the cog's `meta.json`."""

    @classmethod
    def from_json(cls, cog_name: str, file: Path) -> Self:
        """Load cog metadata from a JSON file.

        Args:
            cog_name: The name of the cog.
            file: The file path of the JSON file to load from.

        Returns:
            (CogMetadata): The constructed metadata object.
        """
        with open(file, "rb") as f:
            obj = orjson.loads(f.read())
        return cls(name=cog_name, **obj)


class TidegearMeta(BaseModel):
    """A metadata class containing version and repository information for Tidegear.
    You shouldn't use this for your own cogs, use [`tidegear.metadata.CogMetadata`][] instead.
    """

    version: SemanticVersion
    """The current Tidegear version."""
    repository: Repository
    """Information about the Tidegear git repository."""

    @override
    def __str__(self) -> str:
        """Return the current Tidegear version as a string."""
        return str(self.version)

    @property
    def markdown(self) -> str:
        """Return the current Tidegear version in a markdown hyperlink linking to the Tidegear git repository."""
        return f"[{self.version}]({self.repository.url})"
