# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0


from typing import NamedTuple, Optional


class HTTPResponseStatus(NamedTuple):
    code: int
    status: str


HTTP_400_BAD_REQUEST = HTTPResponseStatus(400, "Bad Request")
HTTP_500_INTERNAL_SERVER_ERROR = HTTPResponseStatus(500, "Internal Server Error")


class DyffError(Exception):
    """Base class for Errors originating from the Dyff Platform."""

    def __init__(self, message, *, http_status: Optional[HTTPResponseStatus] = None):
        self.message = message
        self.http_status = http_status


class ClientError(DyffError):
    """The error was caused by the client using an API incorrectly."""

    def __init__(
        self, message, *, http_status: HTTPResponseStatus = HTTP_400_BAD_REQUEST
    ):
        if not (400 <= http_status.code <= 499):
            raise AssertionError(
                f"ClientError should map to a 4xx HTTP status; got {http_status}"
            )
        super().__init__(message, http_status=http_status)


class PlatformError(DyffError):
    """The error was caused by an internal problem with the platform."""

    def __init__(
        self,
        message,
        *,
        http_status: HTTPResponseStatus = HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        if not (500 <= http_status.code <= 599):
            raise AssertionError(
                f"PlatformError should map to a 5xx HTTP status; got {http_status}"
            )
        super().__init__(message, http_status=http_status)
