########################################################################################################################
# IMPORTS

import asyncio
import configparser
import logging
import random
import re
import shlex
import subprocess
import time
from datetime import timedelta
from typing import Sequence, overload

import pendulum
from babel.numbers import parse_decimal

from ..interfaces.proxy import ProxyInterface

########################################################################################################################
# FUNCTIONS

logger = logging.getLogger(__name__)


def get_config(config_path):
    cfg = configparser.RawConfigParser()
    cfg.read(config_path)
    return cfg


def set_logger(level):
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(level.upper())
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    log.addHandler(ch)


@overload
def ban_sleep(max_time: float) -> None: ...


@overload
def ban_sleep(min_time: float, max_time: float) -> None: ...


def ban_sleep(x: float, y: float | None = None) -> None:
    """
    Sleep for a random number of seconds.

    Usage:
        ban_sleep(5)          -> sleeps ~N(5, 2.5²) seconds, truncated to >= 0
        ban_sleep(3, 7)       -> sleeps uniformly between 3 and 7 seconds
        ban_sleep(7, 3)       -> same as above (order doesn't matter)
    """
    if y is None:
        mean = float(x)
        std_dev = mean / 2.0
        sleep_time = random.gauss(mean, std_dev)  # noqa: S311
        sleep_time = max(0.0, sleep_time)
    else:
        x, y = sorted([float(x), float(y)])
        sleep_time = random.uniform(x, y)  # noqa: S311

    logger.info(f"sleeping for {sleep_time:.2f} seconds...")
    time.sleep(sleep_time)


@overload
async def ban_sleep_async(seconds: float) -> None: ...


@overload
async def ban_sleep_async(min_time: float, max_time: float) -> None: ...


async def ban_sleep_async(min_time: float, max_time: float | None = None) -> None:
    """
    Asynchronous sleep for a random number of seconds.

    Usage:
        await ban_sleep_async(5)          # sleeps ~N(5, (5/2)²) seconds, truncated to >= 0
        await ban_sleep_async(3, 7)       # sleeps uniformly between 3 and 7 seconds
        await ban_sleep_async(7, 3)       # same as above (order doesn't matter)
    """
    if max_time is None:
        mean = float(min_time)
        std_dev = mean / 2.0
        sleep_time = random.gauss(mean, std_dev)  # noqa: S311
        sleep_time = max(0.0, sleep_time)
    else:
        min_time, max_time = sorted([float(min_time), float(max_time)])
        sleep_time = random.uniform(min_time, max_time)  # noqa: S311

    logger.info(f"sleeping for {sleep_time:.2f} seconds...")
    await asyncio.sleep(sleep_time)


def run_bash_command(command):
    p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    text_lines = []
    for line_b in iter(p.stdout.readline, ""):
        line_str = line_b.decode().strip()

        if not line_str:
            break

        logger.info(line_str)
        text_lines.append(line_str)

    return "\n".join(text_lines)


def text_to_int(text):
    max_int32 = 2147483647
    parsed_str = re.sub(r"[^\d]", "", text)
    if parsed_str:
        num = int(parsed_str)
    else:
        return None

    if -max_int32 < num < max_int32:
        return num


def text_to_float(text: str | None, locale: str = "es_ES") -> float | None:
    if not text:
        return None
    match = re.search(r"\d(?:[\d\s.,]*\d)?", text)
    if not match:
        return None
    number_str = match.group(0).replace(" ", "")
    try:
        return float(parse_decimal(number_str, locale=locale))
    except Exception:
        return None


def sleep_out_interval(from_h, to_h, tz="Europe/Madrid", seconds=1800):
    while pendulum.now(tz=tz).hour >= to_h or pendulum.now(tz=tz).hour < from_h:
        logger.warning("time to sleep and not scrape anything...")
        ban_sleep(seconds, seconds)


def sleep_in_interval(from_h, to_h, tz="Europe/Madrid", seconds=1800):
    while from_h <= pendulum.now(tz=tz).hour < to_h:
        logger.warning("time to sleep and not scrape anything...")
        ban_sleep(seconds, seconds)


def parse_field(dict_struct, field_path, format_method=None):
    if not isinstance(field_path, list):
        raise ValueError("Argument field_path must be of type list")

    field_value = dict_struct
    for field in field_path:
        if isinstance(field_value, dict):
            field_value = field_value.get(field)
        elif isinstance(field_value, list):
            field_value = field_value[field] if len(field_value) > field else None
        if field_value is None:
            return None
    return format_method(field_value) if format_method else field_value


def get_data(
    url: str,
    method: str = "GET",
    output: str = "json",
    sleep: tuple = (6, 3),
    proxy_interface: ProxyInterface = None,
    use_auth_proxies: bool = False,
    max_proxy_delay: timedelta = timedelta(minutes=10),
    ignored_status_codes: Sequence[int] = (),
    **kwargs,
):
    """
    Fetches data from a given URL using HTTP requests, with support for proxy configuration, retries, and flexible output formats.

    Args:
        url (str): The target URL to fetch data from.
        method (str, optional): HTTP method to use (e.g., 'GET', 'POST'). Defaults to 'GET'.
        output (str, optional): Output format ('json', 'text', 'soup', 'response'). Defaults to 'json'.
        sleep (tuple, optional): Tuple specifying max and min sleep times (seconds) after request. Defaults to (6, 3).
        use_auth_proxies (bool, optional): Whether to use authenticated proxies. Defaults to False.
        max_proxy_delay (timedelta, optional): Maximum delay for proxy retry logic. Defaults to 10 minutes.
        ignored_status_codes (Sequence[int], optional): Status codes to ignore and return response for. Defaults to ().
        **kwargs: Additional arguments passed to the requests method (timeout defaults to 30 seconds if not specified).

    Returns:
        Depends on the 'output' argument:
            - 'json': Parsed JSON response.
            - 'text': Response text.
            - 'soup': BeautifulSoup-parsed HTML.
            - 'response': Raw requests.Response object.

    Raises:
        IgnoredHTTPError: If a response status code is in `ignored_status_codes`.
        NotFoundError: If a 404 or 410 status code is returned and not in `ignored_status_codes`.
        BadRequestError: If a 400 status code is returned and not in `ignored_status_codes`.
        EmptyResponseError: If the response has no content.
        ProxyError: On proxy-related errors.
        requests.HTTPError: For other HTTP errors if not ignored.
    """

    from .requests import RequestsClient

    client = RequestsClient(proxy_interface)
    return client.get_data(
        url=url,
        method=method,
        output=output,
        sleep=sleep,
        use_auth_proxies=use_auth_proxies,
        max_proxy_delay=max_proxy_delay,
        ignored_status_codes=ignored_status_codes,
        **kwargs,
    )
