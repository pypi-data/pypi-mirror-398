########################################################################################################################
# IMPORTS

import logging
import random
import time
from datetime import timedelta
from functools import partial

import requests
import tenacity
from stem import Signal
from stem.control import Controller

from datamarket.exceptions import EnsureNewIPTimeoutError, NoWorkingProxiesError

########################################################################################################################
# SETUP

logger = logging.getLogger(__name__)
logging.getLogger("stem").setLevel(logging.WARNING)

PROXY_ROTATION_INTERVAL = timedelta(minutes=10)
PROXY_ROTATION_TIMEOUT_SECONDS = int(PROXY_ROTATION_INTERVAL.total_seconds())

########################################################################################################################
# CLASSES


class ProxyInterface:
    """
    Manage HTTP, HTTPS, and SOCKS5 proxies configured in the [proxy] section.
    """

    CHECK_IP_URL = "https://wtfismyip.com/json"

    def __init__(self, config):
        """
        Initialize the ProxyInterface with configuration.

        Args:
            config: Configuration object with proxy settings in the [proxy] section.
                Expected to have 'hosts' and optionally 'tor_password' settings.
        """
        self._load_from_config(config)
        self.current_index = -2  # -2: None, -1: Tor, >=0: Index in entries
        self._health = {}  # {entry: {"ok": bool, "last_checked": ts, "last_error": str}}
        self._traversal_queue = []
        self._traversal_start = None
        self._last_ip_wait = {}
        self._traversal_cycle = 0
        self._automatic_rotation = True
        self._pool = []

    def _load_from_config(self, cfg):
        """
        Load proxy configuration from config object.
        """
        self.tor_password = cfg.get("proxy", "tor_password", fallback=None)
        hosts_raw = cfg.get("proxy", "hosts", fallback="")

        if not hosts_raw:
            raise RuntimeError("[proxy] hosts list is empty")

        entries = []
        for host_entry in (h.strip() for h in hosts_raw.split(",") if h.strip()):
            host, port, user, password = self._parse_host_entry(host_entry)
            entries.append((host, port, user, password))

        self.entries = entries

    def _parse_host_entry(self, host_entry):
        """
        Parse a host entry string into components.
        """
        if "@" in host_entry:
            auth_part, host_part = host_entry.rsplit("@", 1)
            host, port = host_part.split(":")
            user, password = auth_part.split(":", 1)
            return host, port, user, password
        return *host_entry.split(":"), None, None

    @property
    def proxies(self):
        """
        Get current proxies using Tor if configured, otherwise standard proxies.
        """
        return self.get_proxies(use_tor=bool(self.tor_password))

    def set_automatic_rotation(self, enable=True):
        """Configures automatic proxy rotation on each request."""
        self._automatic_rotation = enable

    def rotate_proxies(self, randomize=False, use_auth=False):
        """
        Manually rotate to the next proxy in the pool.
        """
        if not self.entries:
            logger.warning("No proxy entries available to rotate")
            return

        self._pool = self._build_pool(use_auth)

        self._refresh_traversal_queue(self._pool, randomize)

        if self._traversal_queue:
            next_index = self._traversal_queue[0]
            self.current_index = next_index
            self._traversal_queue.pop(0)
            entry = self.entries[next_index]
            logger.info(f"Rotated to proxy: {entry[0]}:{entry[1]} (index {next_index})")
        else:
            logger.warning("Traversal queue is empty, cannot rotate")

    @staticmethod
    def get_proxy_url(host, port, user=None, password=None, schema="http"):
        """
        Build a proxy URL from components.
        """
        auth = f"{user}:{password}@" if user and password else ""
        return f"{schema}://{auth}{host}:{port}"

    def _get_proxies_dict_from_entry(self, entry, schema="http"):
        """
        Build a proxy dictionary from an entry tuple.
        """
        host, port, user, pwd = entry
        if schema == "socks5":
            return {"socks5": self.get_proxy_url(host, port, user, pwd, "socks5")}

        url = self.get_proxy_url(host, port, user, pwd, "http")
        return {"http": url, "https": url}

    def get_proxies(
        self,
        use_tor=False,
        randomize=False,
        raw=False,
        use_auth=False,
        use_socks=False,
        check_timeout=5,
        cooldown_seconds=30,
        proxy_rotation_interval=PROXY_ROTATION_INTERVAL,
    ):
        """
        Get a working proxy with rotation and health checking.
        """
        # Tor handling
        if use_tor:
            self.current_index = -1
            if raw:
                return ("127.0.0.1", "9050", None, None)
            return {"socks5": self.get_proxy_url("127.0.0.1", 9050, schema="socks5")}

        # Standard Proxy handling
        entry = self._get_working_entry(
            use_auth=use_auth,
            randomize=randomize,
            check_timeout=check_timeout,
            cooldown_seconds=cooldown_seconds,
            proxy_rotation_interval=proxy_rotation_interval,
        )

        if raw:
            return entry

        return self._get_proxies_dict_from_entry(entry, "socks5" if use_socks else "http")

    def check_current_ip(self, proxies=None):
        """
        Check the current IP address when using the given proxy.
        """
        try:
            proxies_arg = proxies or self.proxies
            resp = requests.get(self.CHECK_IP_URL, proxies=proxies_arg, timeout=30)
            return resp.json().get("YourFuckingIPAddress")
        except Exception as ex:
            logger.error(f"Failed to check IP: {ex}")

    def renew_tor_ip(self):
        """
        Request Tor to generate a new exit node IP address.
        """
        if not self.tor_password:
            logger.error("Tor password not configured")
            return

        try:
            logger.debug(f"Current IP: {self.check_current_ip()}")
            with Controller.from_port(port=9051) as controller:
                controller.authenticate(password=self.tor_password)
                controller.signal(Signal.NEWNYM)
            time.sleep(5)
            logger.debug(f"New IP: {self.check_current_ip()}")
        except Exception as ex:
            logger.error(f"Failed to renew Tor IP: {ex}")

    def wait_for_new_ip(self, timeout=PROXY_ROTATION_TIMEOUT_SECONDS, interval=30, check_timeout=5):
        """
        Wait for the current proxy to provide a different IP address (proxy IP rotation).
        """
        if self.current_index == -2:
            logger.debug("No proxy currently selected, selecting one for IP waiting")
            self.get_proxies(raw=True)

        if self.current_index == -1:
            entry = ("127.0.0.1", "9050", None, None)
        elif 0 <= self.current_index < len(self.entries):
            entry = self.entries[self.current_index]
        else:
            raise RuntimeError("Could not select a proxy for IP waiting")

        now = time.time()
        interval_seconds = PROXY_ROTATION_INTERVAL.total_seconds()
        last_ts, last_cycle = self._last_ip_wait.get(entry, (None, 0))

        if last_ts and (now - last_ts) <= interval_seconds and self._traversal_cycle <= last_cycle:
            logger.debug("Skipping wait_for_new_ip: recently checked.")
            return

        self._last_ip_wait[entry] = (now, self._traversal_cycle)

        health = self._health.get(entry, {})
        baseline = health.get("last_ip")
        if not baseline:
            try:
                proxies = self._get_proxies_dict_from_entry(entry)
                baseline = self.check_current_ip(proxies)
            except Exception:
                logger.debug("Could not fetch baseline IP for proxy entry")

            if not baseline:
                raise RuntimeError(f"Could not determine baseline IP for entry {entry[0]}:{entry[1]}")

        return self._wait_for_new_ip(entry, baseline, timeout, interval, check_timeout)

    def _mark_entry_status(self, entry, ok, error=None, last_ip=None):
        """
        Update the health status of a proxy entry.
        """
        self._health[entry] = {
            "ok": ok,
            "last_checked": time.time(),
            "last_error": error,
            "last_ip": last_ip,
        }

    def _is_entry_alive(self, entry, timeout=5):
        """
        Check if a proxy entry is functional.
        """
        try:
            proxies = self._get_proxies_dict_from_entry(entry)
            resp = requests.get(self.CHECK_IP_URL, proxies=proxies, timeout=timeout)
            ok = resp.status_code == 200
            last_ip = resp.json().get("YourFuckingIPAddress") if ok else None
            self._mark_entry_status(entry, ok, last_ip=last_ip)
            return ok
        except Exception as ex:
            self._mark_entry_status(entry, False, str(ex))
            return False

    def _get_working_entry(
        self,
        use_auth=False,
        randomize=False,
        check_timeout=5,
        cooldown_seconds=30,
        proxy_rotation_interval=PROXY_ROTATION_INTERVAL,
    ):
        """
        Find and return a working proxy entry.
        """
        if not self.entries:
            raise NoWorkingProxiesError("No proxies available")

        pool = self._build_pool(use_auth)
        self._pool = pool

        # Initialize queue: sticky (current) or full refresh
        if not self._automatic_rotation and self.current_index >= 0:
            self._traversal_queue = [self.current_index]
        elif self._automatic_rotation or not self._traversal_queue:
            logger.debug(f"Refreshing rotation queue (randomize={randomize})")
            self._refresh_traversal_queue(pool, randomize)

        find_once = partial(self._find_working_entry_once, check_timeout, cooldown_seconds)

        if not proxy_rotation_interval:
            return find_once()

        def before_sleep(retry_state):
            tenacity.before_sleep_log(logger, logging.INFO)(retry_state)

            if self._automatic_rotation:
                self._refresh_traversal_queue(pool, randomize)
            elif self.current_index >= 0:
                self._traversal_queue = [self.current_index]

        retrying = tenacity.Retrying(
            wait=tenacity.wait_fixed(cooldown_seconds),
            stop=tenacity.stop_after_delay(proxy_rotation_interval),
            before_sleep=before_sleep,
            retry=tenacity.retry_if_exception_type(NoWorkingProxiesError),
            reraise=True,
        )
        return retrying(find_once)

    def _build_pool(self, use_auth):
        """
        Build a pool of available proxies based on authentication requirements.
        """
        pool = self.entries if use_auth else [e for e in self.entries if not e[2] and not e[3]]
        return pool or self.entries

    def _refresh_traversal_queue(self, pool, randomize):
        """
        Rebuild the proxy traversal queue for the current rotation cycle.
        """
        current_pool_indices = [idx for idx, entry in enumerate(self.entries) if entry in pool]

        if not current_pool_indices:
            return

        if randomize:
            self._traversal_queue = current_pool_indices.copy()
            random.shuffle(self._traversal_queue)
        else:
            # Round-robin: start from next after current_index
            self._traversal_queue = []
            start_idx = (self.current_index + 1) % len(self.entries) if self.current_index >= 0 else 0
            for i in range(len(self.entries)):
                idx = (start_idx + i) % len(self.entries)
                if idx in current_pool_indices:
                    self._traversal_queue.append(idx)

        self._traversal_start = time.time()
        self._traversal_cycle += 1

    def _find_working_entry_once(self, check_timeout, cooldown_seconds):
        """
        Attempt to find a working proxy from the current traversal queue once.
        """
        for idx in list(self._traversal_queue):
            entry = self.entries[idx]
            health = self._health.get(entry, {})
            last_checked = health.get("last_checked", 0)
            ok = health.get("ok", False)
            now = time.time()

            is_fresh = (now - last_checked) < cooldown_seconds

            if ok and is_fresh:
                logger.debug(f"Using cached working proxy: {entry[0]}:{entry[1]}")
                self.current_index = idx
                self._traversal_queue.remove(idx)
                return entry

            if not ok and is_fresh:
                # This proxy failed recently, skip it for this traversal.
                continue

            # Stale or never checked, so we check it.
            logger.debug(f"Checking proxy health: {entry[0]}:{entry[1]}")
            if self._is_entry_alive(entry, timeout=check_timeout):
                self.current_index = idx
                self._traversal_queue.remove(idx)
                return entry
            else:
                # It's dead. Remove it from the queue for this traversal to avoid re-checking.
                self._traversal_queue.remove(idx)

        raise NoWorkingProxiesError("No working proxies available in current queue")

    def _wait_for_new_ip(self, entry, baseline, timeout, interval, check_timeout):
        """
        Poll the proxy repeatedly until its IP address changes from the baseline.
        """
        logger.info(f"Refreshing proxy IP (current baseline: {baseline})...")
        start = time.time()
        proxies = self._get_proxies_dict_from_entry(entry)

        while time.time() - start < timeout:
            try:
                resp = requests.get(self.CHECK_IP_URL, proxies=proxies, timeout=check_timeout)
                current_ip = resp.json().get("YourFuckingIPAddress")
            except Exception:
                current_ip = None

            if current_ip and current_ip != baseline:
                self._mark_entry_status(entry, True, last_ip=current_ip)
                logger.info(f"IP changed from {baseline} to {current_ip}")
                return

            time.sleep(interval)

        raise EnsureNewIPTimeoutError(f"Timed out waiting for new IP after {timeout}s")
