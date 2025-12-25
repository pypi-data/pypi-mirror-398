# SPDX-FileCopyrightText: 2025 cswimr <copyright@csw.im>
# SPDX-License-Identifier: MPL-2.0

# ruff: noqa: D100, D101

from typing import Any

import aiohttp
import orjson
from aiohttp.typedefs import JSONDecoder
from typing_extensions import override


class ClientResponse(aiohttp.ClientResponse):
    @override
    async def json(self, *, encoding: str | None = None, loads: JSONDecoder = orjson.loads, content_type: str | None = "application/json") -> Any:
        """Read and decode the response's data as json.

        Args:
            encoding: Which encoding to use to encode the. Automatically computed based on response if not provided.
            loads: The function to use to deserialize the response's data.
                This is where this method differs from aiohttp's method, as this method defaults to `orjson.loads` instead of `json.loads`.
                As response size increases, this change of defaults will improve deserialization performance significantly.
            content_type: The content type of the response's data.

        Returns:
            A Python object representing the data contained within the response.
        """
        return await super().json(encoding=encoding, loads=loads, content_type=content_type)
