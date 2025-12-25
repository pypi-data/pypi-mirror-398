"""
Browser module data models.
"""
import os
import base64
from typing import Literal, Optional

from ..config import _BROWSER_FINGERPRINT_PERSIST_PATH
from .fingerprint import FingerprintFormat

class BrowserFingerprintContext:
    """
    Browser fingerprint context configuration.
    """

    def __init__(self, fingerprint_context_id: str):
        """
        Initialize FingerprintContext with context id.

        Args:
            fingerprint_context_id (str): ID of the fingerprint context for browser fingerprint.

        Raises:
            ValueError: If fingerprint_context_id is empty.
        """
        if not fingerprint_context_id or not fingerprint_context_id.strip():
            raise ValueError("fingerprint_context_id cannot be empty")

        self.fingerprint_context_id = fingerprint_context_id


class BrowserProxy:
    """
    Browser proxy configuration.
    Supports two types of proxy: custom proxy, wuying proxy.
    wuying proxy support two strategies: restricted and polling.
    """

    def __init__(
        self,
        proxy_type: Literal["custom", "wuying"],
        server: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        strategy: Optional[Literal["restricted", "polling"]] = None,
        pollsize: int = 10,
    ):
        """
        Initialize a BrowserProxy.

        Args:
            proxy_type: Type of proxy - "custom" or "wuying"
            server: Proxy server address (required for custom type)
            username: Proxy username (optional for custom type)
            password: Proxy password (optional for custom type)
            strategy: Strategy for wuying support "restricted" and "polling"
            pollsize: Pool size (optional for proxy_type wuying and strategy polling)

            example:
            # custom proxy
            proxy_type: custom
            server: "127.0.0.1:9090"
            username: "username"
            password: "password"

            # wuying proxy with polling strategy
            proxy_type: wuying
            strategy: "polling"
            pollsize: 10

            # wuying proxy with restricted strategy
            proxy_type: wuying
            strategy: "restricted"
        """
        self.type = proxy_type
        self.server = server
        self.username = username
        self.password = password
        self.strategy = strategy
        self.pollsize = pollsize

        # Validation
        if proxy_type not in ["custom", "wuying"]:
            raise ValueError("proxy_type must be custom or wuying")

        if proxy_type == "custom" and not server:
            raise ValueError("server is required for custom proxy type")

        if proxy_type == "wuying" and not strategy:
            raise ValueError("strategy is required for wuying proxy type")

        if proxy_type == "wuying" and strategy not in ["restricted", "polling"]:
            raise ValueError(
                "strategy must be restricted or polling for wuying proxy type"
            )

        if proxy_type == "wuying" and strategy == "polling" and pollsize <= 0:
            raise ValueError("pollsize must be greater than 0 for polling strategy")

    def _to_map(self):
        """
        Convert BrowserProxy to dictionary format.

        Returns:
            dict: Dictionary representation of the proxy configuration.

        Example:
            ```python
            proxy = BrowserProxy(proxy_type="custom", server="127.0.0.1:8080", username="user", password="pass")
            proxy_dict = proxy._to_map()
            print(proxy_dict)
            ```
        """
        proxy_map = {"type": self.type}

        if self.type == "custom":
            proxy_map["server"] = self.server
            if self.username:
                proxy_map["username"] = self.username
            if self.password:
                proxy_map["password"] = self.password
        elif self.type == "wuying":
            proxy_map["strategy"] = self.strategy
            if self.strategy == "polling":
                proxy_map["pollsize"] = self.pollsize

        return proxy_map

    @classmethod
    def _from_map(cls, m: dict = None):
        """
        Create BrowserProxy from dictionary format.

        Args:
            m (dict): Dictionary containing proxy configuration.

        Returns:
            BrowserProxy: BrowserProxy instance created from the dictionary, or None if m is None.

        Raises:
            ValueError: If the proxy configuration is invalid.

        Example:
            ```python
            proxy_dict = {"type": "custom", "server": "127.0.0.1:8080"}
            proxy = BrowserProxy._from_map(proxy_dict)
            print(f"Proxy type: {proxy.type}, Server: {proxy.server}")
            ```
        """
        if not m:
            return None

        proxy_type = m.get("type")
        if not proxy_type:
            raise ValueError("type is required in proxy configuration")

        if proxy_type == "custom":
            return cls(
                proxy_type=proxy_type,
                server=m.get("server"),
                username=m.get("username"),
                password=m.get("password"),
            )
        elif proxy_type == "wuying":
            return cls(
                proxy_type=proxy_type,
                strategy=m.get("strategy"),
                pollsize=m.get("pollsize", 10),
            )
        else:
            raise ValueError(f"Unsupported proxy type: {proxy_type}")


class BrowserViewport:
    """
    Browser viewport options.
    """

    def __init__(self, width: int = 1920, height: int = 1080):
        self.width = width
        self.height = height

    def _to_map(self):
        """
        Convert BrowserViewport to dictionary format.

        Returns:
            dict: Dictionary representation of the viewport configuration.

        Example:
            ```python
            viewport = BrowserViewport(width=1920, height=1080)
            viewport_dict = viewport._to_map()
            print(viewport_dict)
            ```
        """
        viewport_map = dict()
        if self.width is not None:
            viewport_map["width"] = self.width
        if self.height is not None:
            viewport_map["height"] = self.height
        return viewport_map

    def _from_map(self, m: dict = None):
        """
        Update BrowserViewport from dictionary format.

        Args:
            m (dict): Dictionary containing viewport configuration.

        Returns:
            BrowserViewport: Updated viewport instance.

        Example:
            ```python
            viewport = BrowserViewport()
            viewport._from_map({"width": 1280, "height": 720})
            print(f"Viewport: {viewport.width}x{viewport.height}")
            ```
        """
        m = m or dict()
        if m.get("width") is not None:
            self.width = m.get("width")
        if m.get("height") is not None:
            self.height = m.get("height")
        return self


class BrowserScreen:
    """
    Browser screen options.
    """

    def __init__(self, width: int = 1920, height: int = 1080):
        self.width = width
        self.height = height

    def _to_map(self):
        """
        Convert BrowserScreen to dictionary format.

        Returns:
            dict: Dictionary representation of the screen configuration.

        Example:
            ```python
            screen = BrowserScreen(width=1920, height=1080)
            screen_dict = screen.to_map()
            print(screen_dict)
            ```
        """
        screen_map = dict()
        if self.width is not None:
            screen_map["width"] = self.width
        if self.height is not None:
            screen_map["height"] = self.height
        return screen_map

    def _from_map(self, m: dict = None):
        """
        Update BrowserScreen from dictionary format.

        Args:
            m (dict): Dictionary containing screen configuration.

        Returns:
            BrowserScreen: Updated screen instance.

        Example:
            ```python
            screen = BrowserScreen()
            screen._from_map({"width": 2560, "height": 1440})
            print(f"Screen: {screen.width}x{screen.height}")
            ```
        """
        m = m or dict()
        if m.get("width") is not None:
            self.width = m.get("width")
        if m.get("height") is not None:
            self.height = m.get("height")
        return self


class BrowserFingerprint:
    """
    Browser fingerprint options.
    """

    def __init__(
        self,
        devices: list[Literal["desktop", "mobile"]] = None,
        operating_systems: list[
            Literal["windows", "macos", "linux", "android", "ios"]
        ] = None,
        locales: list[str] = None,
    ):
        self.devices = devices
        self.operating_systems = operating_systems
        self.locales = locales

        # Validation

        if devices is not None:
            if not isinstance(devices, list):
                raise ValueError("devices must be a list")
            for device in devices:
                if device not in ["desktop", "mobile"]:
                    raise ValueError("device must be desktop or mobile")

        if operating_systems is not None:
            if not isinstance(operating_systems, list):
                raise ValueError("operating_systems must be a list")
            for operating_system in operating_systems:
                if operating_system not in [
                    "windows",
                    "macos",
                    "linux",
                    "android",
                    "ios",
                ]:
                    raise ValueError(
                        "operating_system must be windows, macos, linux, android or ios"
                    )

    def _to_map(self):
        fingerprint_map = dict()
        if self.devices is not None:
            fingerprint_map["devices"] = self.devices
        if self.operating_systems is not None:
            fingerprint_map["operatingSystems"] = self.operating_systems
        if self.locales is not None:
            fingerprint_map["locales"] = self.locales
        return fingerprint_map

    def _from_map(self, m: dict = None):
        m = m or dict()
        if m.get("devices") is not None:
            self.devices = m.get("devices")
        if m.get("operatingSystems") is not None:
            self.operating_systems = m.get("operatingSystems")
        if m.get("locales") is not None:
            self.locales = m.get("locales")
        return self


class BrowserOption:
    """
    browser initialization options.
    """

    def __init__(
        self,
        use_stealth: bool = False,
        user_agent: str = None,
        viewport: BrowserViewport = None,
        screen: BrowserScreen = None,
        fingerprint: BrowserFingerprint = None,
        fingerprint_format: Optional["FingerprintFormat"] = None,
        fingerprint_persistent: bool = False,
        solve_captchas: bool = False,
        proxies: Optional[list[BrowserProxy]] = None,
        extension_path: Optional[str] = "/tmp/extensions/",
        cmd_args: Optional[list[str]] = None,
        default_navigate_url: Optional[str] = None,
        browser_type: Optional[Literal["chrome", "chromium"]] = None,
    ):
        self.use_stealth = use_stealth
        self.user_agent = user_agent
        self.viewport = viewport
        self.screen = screen
        self.fingerprint = fingerprint
        self.fingerprint_format = fingerprint_format
        self.solve_captchas = solve_captchas
        self.proxies = proxies
        self.extension_path = extension_path
        self.cmd_args = cmd_args
        self.default_navigate_url = default_navigate_url
        self.browser_type = browser_type

        # Check fingerprint persistent if provided
        if fingerprint_persistent:
            # Currently only support persistent fingerprint in docker env
            self.fingerprint_persist_path = os.path.join(
                _BROWSER_FINGERPRINT_PERSIST_PATH, "fingerprint.json"
            )
        else:
            self.fingerprint_persist_path = None

        # Validate proxies list items
        if proxies is not None:
            if not isinstance(proxies, list):
                raise ValueError("proxies must be a list")
            if len(proxies) > 1:
                raise ValueError("proxies list length must be limited to 1")

        # Validate extension_path if provided
        if extension_path is not None:
            if not isinstance(extension_path, str):
                raise ValueError("extension_path must be a string")
            if not extension_path.strip():
                raise ValueError("extension_path cannot be empty")

        if cmd_args is not None:
            if not isinstance(cmd_args, list):
                raise ValueError("cmd_args must be a list")

        # Validate browser_type
        if browser_type is not None and browser_type not in ["chrome", "chromium"]:
            raise ValueError("browser_type must be 'chrome' or 'chromium'")

    def _to_map(self):
        option_map = dict()
        if behavior_simulate_env := os.getenv("AGENTBAY_BROWSER_BEHAVIOR_SIMULATE"):
            option_map["behaviorSimulate"] = behavior_simulate_env != "0"
        if self.use_stealth is not None:
            option_map["useStealth"] = self.use_stealth
        if self.user_agent is not None:
            option_map["userAgent"] = self.user_agent
        if self.viewport is not None:
            option_map["viewport"] = self.viewport._to_map()
        if self.screen is not None:
            option_map["screen"] = self.screen._to_map()
        if self.fingerprint is not None:
            option_map["fingerprint"] = self.fingerprint._to_map()
        if self.fingerprint_format is not None:
            # Encode fingerprint format to base64 string
            json_str = self.fingerprint_format._to_json()
            option_map["fingerprintRawData"] = base64.b64encode(
                json_str.encode("utf-8")
            ).decode("utf-8")
        if self.fingerprint_persist_path is not None:
            option_map["fingerprintPersistPath"] = self.fingerprint_persist_path
        if self.solve_captchas is not None:
            option_map["solveCaptchas"] = self.solve_captchas
        if self.proxies is not None:
            option_map["proxies"] = [proxy._to_map() for proxy in self.proxies]
        if self.extension_path is not None:
            option_map["extensionPath"] = self.extension_path
        if self.cmd_args is not None:
            option_map["cmdArgs"] = self.cmd_args
        if self.default_navigate_url is not None:
            option_map["defaultNavigateUrl"] = self.default_navigate_url
        if self.browser_type is not None:
            option_map["browserType"] = self.browser_type
        return option_map

    def _from_map(self, m: dict = None):
        m = m or dict()
        if m.get("useStealth") is not None:
            self.use_stealth = m.get("useStealth")
        else:
            self.use_stealth = False
        if m.get("userAgent") is not None:
            self.user_agent = m.get("userAgent")
        if m.get("viewport") is not None:
            self.viewport = BrowserViewport()._from_map(m.get("viewport"))
        if m.get("screen") is not None:
            self.screen = BrowserScreen()._from_map(m.get("screen"))
        if m.get("fingerprint") is not None:
            self.fingerprint = BrowserFingerprint()._from_map(m.get("fingerprint"))
        if m.get("fingerprintRawData") is not None:
            import base64

            from .fingerprint import FingerprintFormat

            fingerprint_raw = m.get("fingerprintRawData")
            if isinstance(fingerprint_raw, str):
                # Decode base64 encoded fingerprint data
                fingerprint_json = base64.b64decode(
                    fingerprint_raw.encode("utf-8")
                ).decode("utf-8")
                self.fingerprint_format = FingerprintFormat._from_json(fingerprint_json)
            else:
                self.fingerprint_format = fingerprint_raw
        if m.get("fingerprintPersistPath") is not None:
            self.fingerprint_persist_path = m.get("fingerprintPersistPath")
        if m.get("solveCaptchas") is not None:
            self.solve_captchas = m.get("solveCaptchas")
        else:
            self.solve_captchas = False
        if m.get("proxies") is not None:
            proxy_list = m.get("proxies")
            if len(proxy_list) > 1:
                raise ValueError("proxies list length must be limited to 1")
            self.proxies = [
                BrowserProxy._from_map(proxy_data) for proxy_data in proxy_list
            ]
        if m.get("cmdArgs") is not None:
            self.cmd_args = m.get("cmdArgs")
        if m.get("defaultNavigateUrl") is not None:
            self.default_navigate_url = m.get("defaultNavigateUrl")
        if m.get("browserType") is not None:
            self.browser_type = m.get("browserType")
        return self