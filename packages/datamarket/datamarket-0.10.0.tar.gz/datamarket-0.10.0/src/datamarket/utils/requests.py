########################################################################################################################
# IMPORTS

import logging
from contextlib import suppress
from datetime import timedelta
from email.utils import parsedate_to_datetime
from http.cookies import SimpleCookie
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from requests.cookies import RequestsCookieJar, create_cookie
from requests.exceptions import HTTPError
from rnet import Emulation, Proxy
from rnet.blocking import Client
from rnet.blocking import Response as RnetResponse
from rnet.exceptions import ConnectionError, TimeoutError, TlsError
from rnet.header import OrigHeaderMap
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    retry_if_not_exception_type,
    stop_after_attempt,
    stop_after_delay,
    wait_exponential,
)

from datamarket.exceptions.main import IgnoredHTTPError

from ..exceptions import BadRequestError, EmptyResponseError, NotFoundError, RedirectionDetectedError
from ..interfaces.proxy import ProxyInterface
from .main import ban_sleep

########################################################################################################################
# SETUP LOGGER

logger = logging.getLogger(__name__)

########################################################################################################################
# CLASSES


class RnetRequestAdapter:
    """Adapter class for converting requests-style kwargs to rnet kwargs."""

    @staticmethod
    def _validate_supported_kwargs(requests_kwargs: Mapping[str, Any], supported: set) -> None:
        """Validate that all kwargs are in the supported set."""
        for key in requests_kwargs:
            if key not in supported:
                raise ValueError(
                    f"The parameter '{key}' exists in requests but "
                    f"is NOT supported by RNET. Remove it or add an explicit mapping."
                )

    @staticmethod
    def _stringify_mapping(mapping: Mapping[Any, Any]) -> Dict[str, str]:
        """Helper to ensure strict string conversion for keys and values."""
        return {str(k): str(v) for k, v in mapping.items()}

    @staticmethod
    def _normalize_headers(value: Any) -> Dict[str, str]:
        """Convert headers to a clean string dictionary."""
        if isinstance(value, Mapping):
            return RnetRequestAdapter._stringify_mapping(value)
        try:
            return RnetRequestAdapter._stringify_mapping(dict(value))
        except (TypeError, ValueError) as e:
            raise TypeError(f"Unsupported type for 'headers': {type(value)!r}") from e

    @staticmethod
    def _build_orig_header_map(clean_headers: Dict[str, str]) -> Optional[OrigHeaderMap]:
        """Build OrigHeaderMap from clean headers to preserve order and casing."""
        if not hasattr(OrigHeaderMap, "insert"):
            return None

        header_map = OrigHeaderMap()
        for k in clean_headers:
            header_map.insert(k)
        return header_map

    @staticmethod
    def _map_headers(value: Any) -> Dict[str, Any]:
        """Map headers parameter to rnet kwargs (headers and orig_headers)."""
        rnet_kwargs = {}
        clean_headers = RnetRequestAdapter._normalize_headers(value)
        rnet_kwargs["headers"] = clean_headers

        header_map = RnetRequestAdapter._build_orig_header_map(clean_headers)
        if header_map is not None:
            rnet_kwargs["orig_headers"] = header_map

        return rnet_kwargs

    @staticmethod
    def _normalize_timeout(value: Any) -> Any:
        """
        Normalize timeout value to int or None.

        WARNING: rnet does not support separate connect and read timeouts.
        If a tuple is provided (connect, read), only the connect timeout is used
        as the TOTAL timeout for the request.
        """
        if isinstance(value, (int, float)):
            return int(value)

        if isinstance(value, tuple) and len(value) == 2:
            connect_timeout = value[0]
            read_timeout = value[1]

            # We use the connect_timeout as the total timeout to respect the stricter constraint,
            # but this may cause the read phase to timeout prematurely.
            if connect_timeout is not None and read_timeout is not None:
                logger.warning(
                    f"RNET LIMITATION: Separate connect/read timeouts are not supported (received {value}). "
                    f"Using the connect timeout ({connect_timeout}s) as the TOTAL timeout. "
                    f"The read timeout ({read_timeout}s) is IGNORED."
                )

            return int(connect_timeout) if connect_timeout is not None else None

        return value

    @staticmethod
    def _map_direct_mappings(requests_kwargs: Mapping[str, Any]) -> Dict[str, Any]:
        """Map direct mappings: headers, timeout, allow_redirects, and verify."""
        rnet_kwargs = {}
        direct_map = {
            "headers": "headers",
            "timeout": "timeout",
            "allow_redirects": "allow_redirects",
            "verify": "verify",
        }

        for src in ["headers", "timeout", "allow_redirects", "verify"]:
            if src in requests_kwargs and requests_kwargs[src] is not None:
                value = requests_kwargs[src]
                dst = direct_map[src]

                if src == "headers":
                    rnet_kwargs.update(RnetRequestAdapter._map_headers(value))
                elif src == "timeout":
                    rnet_kwargs[dst] = RnetRequestAdapter._normalize_timeout(value)
                else:
                    rnet_kwargs[dst] = value

        return rnet_kwargs

    @staticmethod
    def _map_query(requests_kwargs: Mapping[str, Any]) -> Dict[str, Any]:
        """Map params to query."""
        rnet_kwargs = {}
        params = requests_kwargs.get("params")

        if params is None:
            return rnet_kwargs

        if isinstance(params, Mapping):
            rnet_kwargs["query"] = RnetRequestAdapter._stringify_mapping(params)
            return rnet_kwargs

        if not isinstance(params, (str, bytes, bytearray)):
            with suppress(TypeError, ValueError):
                rnet_kwargs["query"] = [(str(k), str(v)) for k, v in params]
                return rnet_kwargs

        raise TypeError(
            "Unsupported format for 'params'. Expected a mapping or an iterable of "
            "(key, value) pairs (e.g. [('a', 1), ('b', 2)]). "
            f"Got type {type(params)!r}."
        )

    @staticmethod
    def _map_body_and_files(requests_kwargs: Mapping[str, Any]) -> Dict[str, Any]:
        """Map json, data, and files to appropriate rnet fields."""
        rnet_kwargs = {}

        json_data = requests_kwargs.get("json")
        if json_data is not None:
            if not isinstance(json_data, Mapping):
                raise TypeError("Rnet 'json' expects a dict-like object.")
            rnet_kwargs["json"] = dict(json_data)

        data = requests_kwargs.get("data")
        if data is not None:
            if isinstance(data, Mapping):
                rnet_kwargs["form"] = RnetRequestAdapter._stringify_mapping(data)

            elif not isinstance(data, (str, bytes, bytearray)):
                with suppress(TypeError, ValueError):
                    rnet_kwargs["form"] = [(str(k), str(v)) for k, v in data]
                    return rnet_kwargs

                raise TypeError(
                    "Unsupported format for 'data'. Expected a mapping or an iterable of "
                    "(key, value) pairs (e.g. [('a', 1), ('b', 2)]). "
                    f"Got type {type(data)!r}."
                )

            else:
                rnet_kwargs["body"] = data

        if requests_kwargs.get("files") is not None:
            raise NotImplementedError("Mapping 'files' -> Rnet 'multipart' is not implemented yet.")

        return rnet_kwargs

    @staticmethod
    def _map_auth(requests_kwargs: Mapping[str, Any]) -> Dict[str, Any]:
        """Map auth to basic_auth or auth."""
        rnet_kwargs = {}
        auth = requests_kwargs.get("auth")
        if auth:
            if isinstance(auth, tuple) and len(auth) == 2:
                user, pwd = auth
                rnet_kwargs["basic_auth"] = (str(user), None if pwd is None else str(pwd))
            else:
                if not isinstance(auth, str):
                    raise TypeError("Rnet 'auth' only supports string values (e.g. 'user:pass').")
                rnet_kwargs["auth"] = auth
        return rnet_kwargs

    @staticmethod
    def _map_proxy(requests_kwargs: Mapping[str, Any]) -> Dict[str, Any]:
        """Map requests 'proxies' (dict o Proxy) a rnet 'proxy'."""
        rnet_kwargs: Dict[str, Any] = {}

        proxies = requests_kwargs.get("proxies")
        if proxies is None:
            return rnet_kwargs

        if isinstance(proxies, Mapping):
            url = proxies.get("https") or proxies.get("http")
            if url is None:
                raise ValueError("No suitable proxy URL found in 'proxies' dict")

            rnet_kwargs["proxy"] = Proxy(url)
        else:
            rnet_kwargs["proxy"] = proxies

        return rnet_kwargs

    @staticmethod
    def _map_cookies(requests_kwargs: Mapping[str, Any]) -> Dict[str, str]:
        """Convert 'cookies' arg to a Cookie header string."""
        cookies = requests_kwargs.get("cookies")
        if not cookies:
            return {}

        cookie_list = []
        if isinstance(cookies, Mapping):
            for k, v in cookies.items():
                cookie_list.append(f"{k}={v}")
        else:
            # Assume it's a CookieJar or iterable
            try:
                for c in cookies:
                    # RequestsCookieJar yields cookies, specific cookie objects, or sometimes keys
                    # depending on iteration. Safe access via name/value attributes.
                    if hasattr(c, "name") and hasattr(c, "value"):
                        cookie_list.append(f"{c.name}={c.value}")
                    elif isinstance(c, tuple) and len(c) == 2:
                        cookie_list.append(f"{c[0]}={c[1]}")
            except TypeError:
                pass

        if not cookie_list:
            return {}

        return {"Cookie": "; ".join(cookie_list)}

    @staticmethod
    def requests_to_rnet_kwargs(**requests_kwargs: Any) -> Dict[str, Any]:
        supported = {
            "headers",
            "timeout",
            "allow_redirects",
            "params",
            "json",
            "data",
            "files",
            "auth",
            "proxies",
            "cookies",
            "verify",
        }

        RnetRequestAdapter._validate_supported_kwargs(requests_kwargs, supported)

        rnet_kwargs: Dict[str, Any] = {}
        rnet_kwargs.update(RnetRequestAdapter._map_direct_mappings(requests_kwargs))
        rnet_kwargs.update(RnetRequestAdapter._map_query(requests_kwargs))
        rnet_kwargs.update(RnetRequestAdapter._map_body_and_files(requests_kwargs))
        rnet_kwargs.update(RnetRequestAdapter._map_auth(requests_kwargs))
        rnet_kwargs.update(RnetRequestAdapter._map_proxy(requests_kwargs))

        # Handle Cookies: Convert to header and merge into existing headers
        cookie_header = RnetRequestAdapter._map_cookies(requests_kwargs)
        if cookie_header:
            if "headers" not in rnet_kwargs:
                rnet_kwargs["headers"] = {}

            # Merge logic: if Cookie exists, append; otherwise set.
            existing_key = next((k for k in rnet_kwargs["headers"] if k.lower() == "cookie"), None)
            if existing_key:
                rnet_kwargs["headers"][existing_key] = (
                    f"{rnet_kwargs['headers'][existing_key]}; {cookie_header['Cookie']}"
                )
            else:
                rnet_kwargs["headers"]["Cookie"] = cookie_header["Cookie"]

        return rnet_kwargs


class RequestsCompatibleResponse:
    """
    A wrapper around rnet Response that provides backward compatibility with requests.Response API.
    """

    def __init__(self, rnet_response: RnetResponse):
        self._rnet_response = rnet_response

    @property
    def text(self) -> str:
        return self._rnet_response.text()

    @property
    def content(self) -> bytes:
        return self._rnet_response.bytes()

    @property
    def status_code(self) -> int:
        return self._rnet_response.status.as_int()

    @property
    def headers(self) -> Dict[str, str]:
        headers = {}
        for key, value in self._rnet_response.headers:
            key_str = key.decode("utf-8") if isinstance(key, bytes) else str(key)
            value_str = value.decode("utf-8") if isinstance(value, bytes) else str(value)
            headers[key_str] = value_str
        return headers

    @property
    def url(self) -> str:
        return str(self._rnet_response.url)

    @property
    def ok(self) -> bool:
        return self._rnet_response.status.is_success()

    @property
    def cookies(self) -> RequestsCookieJar:
        jar = RequestsCookieJar()

        raw = getattr(self._rnet_response, "cookies", None)
        if raw is not None:
            try:
                items = raw.items() if hasattr(raw, "items") else raw
                for k, v in items:
                    jar.set(k, v)
            except (TypeError, ValueError):
                pass

        host = urlparse(self.url).hostname
        for k, v in self._rnet_response.headers:
            key = k.decode("utf-8") if isinstance(k, bytes) else str(k)
            if key.lower() == "set-cookie":
                val = v.decode("utf-8") if isinstance(v, bytes) else str(v)
                sc = SimpleCookie()
                sc.load(val)
                for name, morsel in sc.items():
                    raw = morsel["expires"]
                    try:
                        expires = (
                            int(raw)
                            if raw and raw.isdigit()
                            else (int(parsedate_to_datetime(raw).timestamp()) if raw else None)
                        )
                    except (ValueError, TypeError, AttributeError):
                        expires = None

                    ck = create_cookie(
                        name=name,
                        value=morsel.value,
                        domain=morsel["domain"] or host,
                        path=morsel["path"] or "/",
                        secure=bool(morsel["secure"]),
                        expires=expires,
                        rest={"HttpOnly": morsel["httponly"]} if morsel["httponly"] else None,
                    )
                    jar.set_cookie(ck)

        return jar

    def raise_for_status(self) -> None:
        if not self._rnet_response.status.is_success():
            status_code = self._rnet_response.status.as_int()
            url = str(self._rnet_response.url)
            error = HTTPError(f"HTTP {status_code} error for {url}")
            error.response = self
            raise error

    def bytes(self) -> bytes:
        return self._rnet_response.bytes()

    def json(self) -> Any:
        return self._rnet_response.json()

    @property
    def status(self):
        return self._rnet_response.status

    def __getattr__(self, name):
        return getattr(self._rnet_response, name)


class RequestsClient:
    """A robust, proxy-enabled HTTP client with retry logic and flexible output formats."""

    # 1. FORBIDDEN HEADERS:
    # We strip these entirely from user input. This forces rnet to generate them
    # based on the selected Emulation (e.g., Firefox143).
    MANAGED_HEADERS_TO_STRIP = {
        "user-agent",
        "connection",
        "dnt",
        "pragma",
        "cache-control",
        "upgrade-insecure-requests",
        "priority",
        "sec-ch-ua",
        "sec-ch-ua-mobile",
        "sec-ch-ua-platform",
    }

    # 2. OVERRIDE HEADERS:
    # If the user provides these, we must use them EXACTLY as provided.
    CRITICAL_OVERRIDE_HEADERS = {
        "accept",
        "accept-language",
        "accept-encoding",
        "sec-fetch-dest",
        "sec-fetch-mode",
        "sec-fetch-site",
        "sec-fetch-user",
    }

    _REDIRECT_STATUS_CODES = set(range(300, 309))

    def __init__(self, proxy_interface: Optional[ProxyInterface] = None):
        self.proxy_interface = proxy_interface
        # Default client for general use
        self.client = Client(
            emulation=Emulation.Firefox143,
            cookie_store=True,
            allow_redirects=True,
            max_redirects=10,
        )
        # Cache for specialized clients
        self._client_cache: Dict[Tuple[Tuple[str, str], ...], Client] = {}

    def _get_cached_client(self, headers: Dict[str, str], allow_redirects: bool) -> Client:
        """
        Retrieves a cached Client instance or creates a new one if the specific
        header/redirect configuration hasn't been seen before.
        """
        # Convert headers dict to a sorted tuple of items to make it hashable
        # e.g., (('accept', 'application/json'), ('accept-language', 'en-US'))
        headers_key = tuple(sorted(headers.items()))

        # storage key includes headers and the allow_redirects flag
        cache_key = (headers_key, allow_redirects)

        if cache_key not in self._client_cache:
            # specific logging to track when we actually incur the cost of creation
            logger.debug(f"Initializing new rnet Client for specific headers: {headers.keys()}")

            # Optional: Simple guard to prevent memory leaks if headers are randomized per request
            if len(self._client_cache) > 50:
                self._client_cache.clear()

            self._client_cache[cache_key] = Client(
                emulation=Emulation.Firefox143,
                cookie_store=True,
                allow_redirects=allow_redirects,
                max_redirects=10,
                headers=headers,
            )

        return self._client_cache[cache_key]

    def _process_headers(self, headers: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        Splits headers into client_init_headers and request_headers.
        """
        if not headers:
            return {}, {}

        client_init_headers = {}
        request_headers = {}

        for key, value in headers.items():
            key_lower = str(key).lower()

            if key_lower in self.MANAGED_HEADERS_TO_STRIP:
                continue

            if key_lower in self.CRITICAL_OVERRIDE_HEADERS:
                client_init_headers[key] = value
                continue

            request_headers[key] = value

        return client_init_headers, request_headers

    @retry(
        retry=retry_if_exception_type((TlsError, TimeoutError, ConnectionError)),
        wait=wait_exponential(exp_base=3, multiplier=3, max=60),
        stop=stop_after_delay(timedelta(minutes=10)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _request_with_proxy_retry(self, url: str, method: str, use_auth: bool, **params):
        logger.info(f"Fetching data from {url} ...")

        proxy_obj = None
        if self.proxy_interface:
            host, port, user, pwd = self.proxy_interface.get_proxies(raw=True, use_auth=use_auth)
            if host and port:
                proxy_url = f"http://{host}:{port}"
                proxy_obj = Proxy.all(proxy_url, username=user, password=pwd) if user and pwd else Proxy.all(proxy_url)
                logger.info(f"Using proxy: {host}:{port}")

        request_params = params.copy()

        if proxy_obj:
            request_params["proxies"] = proxy_obj

        client_init_headers = {}

        if "headers" in request_params:
            client_init_headers, request_method_headers = self._process_headers(request_params["headers"])
            request_params["headers"] = request_method_headers

        if client_init_headers:
            active_client = self._get_cached_client(
                headers=client_init_headers, allow_redirects=request_params.get("allow_redirects", True)
            )
        else:
            active_client = self.client

        # Convert args (including cookies) to rnet format
        rnet_params = RnetRequestAdapter.requests_to_rnet_kwargs(**request_params)

        rnet_response = getattr(active_client, method.lower())(url, **rnet_params)

        return RequestsCompatibleResponse(rnet_response)

    def _handle_http_error(self, status_code: int, url: str, response, allow_redirects: bool) -> None:
        """
        Handle HTTP errors with special handling for redirects when allow_redirects is False.

        Args:
            status_code: HTTP status code
            url: Request URL
            response: Response object
            allow_redirects: Whether redirects are allowed

        Raises:
            RedirectionDetectedError: If a redirect status is received and allow_redirects is False
            NotFoundError: For 404/410 errors
            BadRequestError: For 400 errors
            HTTPError: For other non-2xx status codes
        """
        # Check for redirect status codes when redirects are disabled

        if not allow_redirects and status_code in self._REDIRECT_STATUS_CODES:
            raise RedirectionDetectedError(
                message=f"HTTP {status_code} redirect detected but allow_redirects is False for {url}",
                response=response,
            )

        # Standard error handlers
        error_handlers = {
            404: lambda: NotFoundError(message=f"404 Not Found error for {url}", response=response),
            410: lambda: NotFoundError(message=f"410 Gone error for {url}", response=response),
            400: lambda: BadRequestError(message=f"400 Bad Request error for {url}", response=response),
        }

        if status_code in error_handlers:
            raise error_handlers[status_code]()

        # Raise for any other non-2xx status
        response.raise_for_status()

    @retry(
        retry=retry_if_not_exception_type((NotFoundError, BadRequestError, RedirectionDetectedError, IgnoredHTTPError)),
        wait=wait_exponential(exp_base=3, multiplier=3, max=60),
        stop=stop_after_attempt(5),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def get_data(
        self,
        url: str,
        method: str = "GET",
        output: str = "json",
        sleep: tuple = (6, 3),
        use_auth_proxies: bool = False,
        max_proxy_delay: timedelta = timedelta(minutes=10),
        ignored_status_codes: Sequence[int] = (),
        **kwargs,
    ):
        params = kwargs.copy()

        if "timeout" not in params and "read_timeout" not in params:
            params["timeout"] = 30

        r = self._request_with_proxy_retry.retry_with(stop=stop_after_delay(max_proxy_delay))(
            self, url, method, use_auth_proxies, **params
        )

        ban_sleep(*sleep)

        status_code = r.status_code

        if status_code in ignored_status_codes:
            raise IgnoredHTTPError(message=f"Status {status_code} in ignored_status_codes for URL {url}", response=r)

        # Check if allow_redirects is explicitly set in params, default to True
        allow_redirects = params.get("allow_redirects", True)

        # Handle HTTP errors with redirect detection
        self._handle_http_error(status_code, url, r, allow_redirects)

        response_content = r.content
        if not response_content:
            raise EmptyResponseError(message=f"Empty response received from {url} (status {status_code})", response=r)

        output_format = {
            "json": lambda: r.json(),
            "text": lambda: r.text,
            "soup": lambda: BeautifulSoup(response_content, "html.parser"),
            "response": lambda: r,
        }

        if output in output_format:
            return output_format[output]()

        raise ValueError(f"Unsupported output format: {output}")
