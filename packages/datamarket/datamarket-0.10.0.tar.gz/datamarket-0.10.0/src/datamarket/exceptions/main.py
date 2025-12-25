########################################################################################################################
# CLASSES


from typing import Optional

from requests import Request, Response
from requests.exceptions import HTTPError


class ManagedHTTPError(HTTPError):
    """Signal that this HTTP status was handled and should not be retried."""

    def __init__(
        self,
        message: Optional[str] = None,
        response: Optional[Response] = None,
        request: Optional[Request] = None,
        *args,
        **kwargs,
    ):
        self.response = response
        self.request = request or getattr(response, "request", None)

        # Build a safe default message
        if not message:
            status = getattr(self.response, "status_code", "unknown")
            url = getattr(self.request, "url", "unknown")
            message = f"HTTP {status} for {url}"

        self.message = message

        super().__init__(message, *args, response=response, **kwargs)


class IgnoredHTTPError(ManagedHTTPError):
    """Exception type that signals the error should be ignored by retry logic."""

    pass


class NotFoundError(ManagedHTTPError):
    def __init__(
        self,
        message: Optional[str] = None,
        response: Optional[Response] = None,
        request: Optional[Request] = None,
        *args,
        **kwargs,
    ):
        if not message:
            status = getattr(response, "status_code", 404)
            req = request or getattr(response, "request", None)
            url = getattr(req, "url", "unknown")
            message = f"HTTP {status} for {url}"
        super().__init__(message, response, request, *args, **kwargs)


class BadRequestError(ManagedHTTPError):
    def __init__(
        self,
        message: Optional[str] = None,
        response: Optional[Response] = None,
        request: Optional[Request] = None,
        *args,
        **kwargs,
    ):
        if not message:
            status = getattr(response, "status_code", 400)
            req = request or getattr(response, "request", None)
            url = getattr(req, "url", "unknown")
            message = f"HTTP {status} for {url}"
        super().__init__(message, response, request, *args, **kwargs)


class EmptyResponseError(ManagedHTTPError):
    def __init__(
        self,
        message: Optional[str] = None,
        response: Optional[Response] = None,
        request: Optional[Request] = None,
        *args,
        **kwargs,
    ):
        if not message:
            req = request or getattr(response, "request", None)
            url = getattr(req, "url", "unknown")
            message = f"Empty response for {url}"
        super().__init__(message, response, request, *args, **kwargs)


class RedirectionDetectedError(ManagedHTTPError):
    def __init__(
        self,
        message: Optional[str] = None,
        response: Optional[Response] = None,
        request: Optional[Request] = None,
        *args,
        **kwargs,
    ):
        if not message:
            status = getattr(response, "status_code", 300)
            req = request or getattr(response, "request", None)
            url = getattr(req, "url", "unknown")
            message = f"HTTP {status} for {url}"
        super().__init__(message, response, request, *args, **kwargs)


class NoWorkingProxiesError(Exception):
    def __init__(self, message="No working proxies available"):
        self.message = message
        super().__init__(self.message)


class EnsureNewIPTimeoutError(Exception):
    def __init__(self, message="Timed out waiting for new IP"):
        self.message = message
        super().__init__(self.message)
