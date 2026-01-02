# SPDX-FileCopyrightText: 2025 cswimr <copyright@csw.im>
# SPDX-License-Identifier: MPL-2.0

"""Defines a subclass of [`pydantic.HttpUrl`][] for use in Tidegear cogs which take advantage of Pydantic."""

import typing

import pydantic
import yarl
from discord.utils import MISSING


class HttpUrl(pydantic.HttpUrl):
    """A subclass of [`pydantic.HttpUrl`][] that adds some useful methods and operator overloads for ergonomic path manipulation.

    Operations:
      - `url / "segment"`  - returns a new HttpUrl with "segment" appended to the path
      - `url /= "segment"` - in-place append of "segment" to the path
    """

    def __truediv__(self, segment: str) -> typing.Self:
        """Use [`HttpUrl.join`][tidegear.pydantic.HttpUrl.join] to return a new HttpUrl with a string segment appended.

        Examples:
            >>> u = HttpUrl("https://example.com/api")
            >>> u2 = u / "v1" / "users"
            >>> print(u2)
            https://example.com/api/v1/users

        Args:
            segment: The segment to add to the existing HttpUrl.

        Returns:
            (HttpUrl): The resulting HttpUrl.
        """
        return self.join(segment)

    def __itruediv__(self, segment: str) -> typing.Self:
        """Use [`HttpUrl.join`][tidegear.pydantic.HttpUrl.join] to append a string segment to the existing HttpUrl in-place.

        Examples:
            >>> u = HttpUrl("https://example.com/api")
            >>> u /= "v1/users"
            >>> print(u)
            https://example.com/api/v1/users

        Args:
            segment: The segment to add to the existing HttpUrl.

        Returns:
            (HttpUrl): The resulting HttpUrl.
        """
        return self.__truediv__(segment)

    @property
    def base(self) -> "HttpUrl":
        """Wrapper around [`HttpUrl.join`][tidegear.pydantic.HttpUrl.join] that returns the base URL (scheme, host, etc.).

        Returns:
            The new HttpUrl object pointing to the base URL of the source HttpUrl object.
        """
        return self.join(None, query=None, fragment=None)

    @property
    def yarl(self) -> yarl.URL:
        """Create a [`yarl.URL`][] object from this `HttpUrl`. Included for convenience when using [aiohttp][]."""
        return yarl.URL(str(self))

    def join(self, path: str | None = MISSING, /, *, query: str | None = MISSING, fragment: str | None = MISSING) -> typing.Self:
        """Create a new HttpUrl object from an existing object.

        Args:
            path: The path to add to this HttpUrl's path.
                This will replace the original path if set to `None`.
            query: The query to replace this HttpUrl's query with.
                This will replace the original query if set to `None`.
            fragment: The fragment to replace this HttpUrl's fragment with.
                This will replace the original fragment if set to `None`.

        Returns:
            (HttpUrl): The new HttpUrl object.
        """

        def _strip(s: str, /) -> str:
            return s.lstrip("/").rstrip("/")

        base = _strip(self.path or "")

        if path is MISSING:
            new_path = base
        elif path is None:
            new_path = ""
        else:
            seg = _strip(path)
            new_path = f"{base}/{seg}" if base else seg

        return self.build(
            scheme=self.scheme,
            username=self.username,
            password=self.password,
            host=self.host or "",
            port=self.port,
            path=new_path,
            query=self.query if query is MISSING else query,
            fragment=self.fragment if fragment is MISSING else fragment,
        )
