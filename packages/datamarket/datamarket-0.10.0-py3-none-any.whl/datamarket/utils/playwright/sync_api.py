########################################################################################################################
# IMPORTS

import json
import logging
import time
from datetime import timedelta
from random import randint
from types import TracebackType
from typing import Optional, Self, Sequence

from bs4 import BeautifulSoup
from camoufox import Camoufox
from playwright.sync_api import Browser, BrowserContext, Page, Response
from playwright.sync_api import (
    Error as PlaywrightError,
)
from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
)
from requests.exceptions import HTTPError, ProxyError
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    retry_if_not_exception_type,
    stop_after_attempt,
    stop_after_delay,
    wait_exponential,
)

from datamarket.exceptions import BadRequestError, EmptyResponseError, NotFoundError, RedirectionDetectedError
from datamarket.exceptions.main import IgnoredHTTPError
from datamarket.interfaces.proxy import ProxyInterface
from datamarket.utils.main import ban_sleep

########################################################################################################################
# SETUP LOGGER

logger = logging.getLogger(__name__)


########################################################################################################################
# HELPER FUNCTIONS


def human_type(page: Page, text: str, delay: int = 100):
    for char in text:
        page.keyboard.type(char, delay=randint(int(delay * 0.5), int(delay * 1.5)))  # noqa: S311


def human_press_key(page: Page, key: str, count: int = 1, delay: int = 100, add_sleep: bool = True) -> None:
    """Presses a key with a random delay, optionally sleeping between presses."""
    for _ in range(count):
        page.keyboard.press(key, delay=randint(int(delay * 0.5), int(delay * 1.5)))  # noqa: S311
        if add_sleep:
            time.sleep(randint(int(delay * 1.5), int(delay * 2.5)) / 1000)  # noqa: S311


########################################################################################################################
# CLASSES


class PlaywrightCrawler:
    """A robust, proxy-enabled Playwright crawler with captcha bypass and retry logic."""

    _REDIRECT_STATUS_CODES = set(range(300, 309))

    def __init__(self, proxy_interface: Optional[ProxyInterface] = None):
        """
        Initializes the crawler.

        Args:
            proxy_interface (Optional[ProxyInterface], optional): Provider used to fetch
                proxy credentials. Defaults to None. When None, no proxy is configured and
                the browser will run without a proxy.
        """
        self.proxy_interface = proxy_interface
        self.pw: Optional[Camoufox] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def __enter__(self) -> Self:
        """Initializes the browser context when entering the `with` statement."""
        self.init_context()
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Safely closes the browser context upon exit."""
        if self.pw:
            try:
                self.pw.__exit__(exc_type, exc_val, exc_tb)
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
            finally:
                self.pw = None
                self.browser = None
                self.context = None
                self.page = None

    def _build_proxy_config(self) -> Optional[dict]:
        """Builds the proxy configuration dictionary.

        Returns:
            Optional[dict]: Proxy configuration if a proxy_interface is provided; otherwise None.
        """
        if not self.proxy_interface:
            logger.info("Starting browser without proxy.")
            return None

        host, port, user, pwd = self.proxy_interface.get_proxies(raw=True, use_auth=True)
        proxy_url = f"http://{host}:{port}"
        proxy_cfg: dict = {"server": proxy_url}
        if user and pwd:
            proxy_cfg.update({"username": user, "password": pwd})

        logger.info(f"Starting browser with proxy: {proxy_url}")
        return proxy_cfg

    @retry(
        wait=wait_exponential(exp_base=2, multiplier=3, max=90),
        stop=stop_after_delay(timedelta(minutes=10)),
        before_sleep=before_sleep_log(logger, logging.INFO),
        reraise=True,
    )
    def init_context(self) -> Self:
        """
        Initializes a new browser instance and context.

        Behavior:
        - If a proxy_interface is provided, fetches fresh proxy credentials and starts
          the browser using that proxy.
        - If proxy_interface is None, starts the browser without any proxy.

        Returns:
            Self: The crawler instance with active browser, context, and page.
        """
        try:
            proxy_cfg: Optional[dict] = self._build_proxy_config()

            self.pw = Camoufox(headless=True, geoip=True, humanize=True, proxy=proxy_cfg)
            self.browser = self.pw.__enter__()
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
        except Exception as e:
            logger.error(f"Failed to initialize browser context: {e}")
            if self.pw:
                self.pw.__exit__(type(e), e, e.__traceback__)
            raise
        return self

    def restart_context(self) -> None:
        """Closes the current browser instance and initializes a new one."""
        logger.info("Restarting browser context...")
        if self.pw:
            self.pw.__exit__(None, None, None)
        self.init_context()

    @retry(
        retry=retry_if_exception_type((PlaywrightTimeoutError, PlaywrightError)),
        wait=wait_exponential(exp_base=2, multiplier=3, max=90),
        stop=stop_after_delay(timedelta(minutes=10)),
        before_sleep=before_sleep_log(logger, logging.INFO),
        before=lambda rs: rs.args[0].restart_context() if rs.attempt_number > 1 else None,
        reraise=True,
    )
    def _goto_with_retry(self, url: str, timeout: int = 30_000) -> Response:
        """
        Navigates to a URL with retries for common Playwright errors.
        Restarts the browser context on repeated failures.
        """
        if not (self.page and not self.page.is_closed()):
            logger.warning("Page is not available or closed. Restarting context.")
            self.restart_context()

        response = self.page.goto(url, timeout=timeout, wait_until="domcontentloaded")
        return response

    def goto(self, url: str, max_proxy_delay: timedelta = timedelta(minutes=10), timeout: int = 30_000) -> Response:
        """
        Ensures the browser is initialized and navigates to the given URL.
        Public wrapper for the internal retry-enabled navigation method.
        """
        if not self.page:
            logger.info("Browser context not found, initializing now...")
            self.init_context()
        return self._goto_with_retry.retry_with(stop=stop_after_delay(max_proxy_delay))(self, url, timeout)

    def _handle_http_error(self, status_code: int, url: str, response, allow_redirects: bool = True) -> None:
        """
        Handle HTTP errors with special handling for redirects.

        Args:
            status_code: HTTP status code
            url: Request URL
            response: Response object

        Raises:
            RedirectionDetectedError: If a redirect status is received
            NotFoundError: For 404/410 errors
            BadRequestError: For 400 errors
            HTTPError: For other non-2xx status codes
        """

        if not allow_redirects and response.request.redirected_from:  # noqa: F841
            raise RedirectionDetectedError(
                message=f"HTTP redirect detected from {response.request.redirected_from.url} to {response.request.redirected_from.redirected_to.url}",
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
        if status_code >= 400:
            raise HTTPError(f"Navigation failed: {status_code} - {url}", response=response)

    @retry(
        retry=retry_if_not_exception_type(
            (IgnoredHTTPError, NotFoundError, BadRequestError, RedirectionDetectedError, ProxyError)
        ),
        wait=wait_exponential(exp_base=3, multiplier=3, max=60),
        stop=stop_after_attempt(5),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=False,
        retry_error_callback=lambda rs: None,
    )
    def get_data(
        self,
        url: str,
        output: str = "json",
        sleep: tuple = (6, 3),
        max_proxy_delay: timedelta = timedelta(minutes=10),
        ignored_status_codes: Sequence[int] = (),
        timeout: int = 30_000,
        **kwargs,
    ):
        """Crawls a given URL using Playwright and attempts to parse its body content"""

        params = kwargs.copy()

        allow_redirects = params.get("allow_redirects", True)

        logger.info(f"Fetching data from {url} ...")
        r = self.goto(url, max_proxy_delay, timeout)
        ban_sleep(*sleep)
        body_content = self.page.eval_on_selector("body", "body => body.innerText")

        if r.status in ignored_status_codes:
            raise IgnoredHTTPError(message=f"Status {r.status} in ignored_status_codes for URL {url}", response=r)

        # Handle HTTP errors with redirect detection
        self._handle_http_error(r.status, url, r, allow_redirects)

        if not body_content:
            raise EmptyResponseError(message=f"Empty body received from {url} (status {r.status})", response=r)

        output_format = {
            "json": lambda: json.loads(body_content),
            "text": lambda: body_content,
            "soup": lambda: BeautifulSoup(body_content, "html.parser"),
            "response": lambda: r,
        }

        if output in output_format:
            return output_format[output]()

        raise ValueError(f"Unsupported output format: {output}")
