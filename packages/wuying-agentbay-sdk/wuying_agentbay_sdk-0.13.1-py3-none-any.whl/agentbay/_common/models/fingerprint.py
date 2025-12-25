"""
Fingerprint module data models.
"""
import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Union

@dataclass
class ScreenFingerprint:
    """Screen fingerprint data structure."""

    availHeight: int
    availWidth: int
    availTop: int
    availLeft: int
    colorDepth: int
    height: int
    pixelDepth: int
    width: int
    devicePixelRatio: float
    pageXOffset: int
    pageYOffset: int
    innerHeight: int
    outerHeight: int
    outerWidth: int
    innerWidth: int
    screenX: int
    clientWidth: int
    clientHeight: int
    hasHDR: bool


@dataclass
class Brand:
    """Brand information data structure."""

    brand: str
    version: str


@dataclass
class UserAgentData:
    """User agent data structure."""

    brands: List[Brand]
    mobile: bool
    platform: str
    architecture: str
    bitness: str
    fullVersionList: List[Brand]
    model: str
    platformVersion: str
    uaFullVersion: str


@dataclass
class ExtraProperties:
    """Navigator extra properties data structure."""

    vendorFlavors: List[str]
    isBluetoothSupported: bool
    globalPrivacyControl: Optional[Any]
    pdfViewerEnabled: bool
    installedApps: List[Any]


@dataclass
class NavigatorFingerprint:
    """Navigator fingerprint data structure."""

    userAgent: str
    userAgentData: UserAgentData
    doNotTrack: str
    appCodeName: str
    appName: str
    appVersion: str
    oscpu: str
    webdriver: str
    language: str
    languages: List[str]
    platform: str
    deviceMemory: Optional[int]
    hardwareConcurrency: int
    product: str
    productSub: str
    vendor: str
    vendorSub: str
    maxTouchPoints: Optional[int]
    extraProperties: ExtraProperties


@dataclass
class VideoCard:
    """Video card information data structure."""

    renderer: str
    vendor: str


@dataclass
class Fingerprint:
    """Main fingerprint data structure."""

    screen: ScreenFingerprint
    navigator: NavigatorFingerprint
    videoCodecs: Dict[str, str]
    audioCodecs: Dict[str, str]
    pluginsData: Dict[str, str]
    battery: Optional[Dict[str, str]]
    videoCard: VideoCard
    multimediaDevices: List[str]
    fonts: List[str]
    mockWebRTC: bool
    slim: Optional[bool]


@dataclass
class FingerprintFormat:
    """Complete fingerprint format including fingerprint data and headers."""

    fingerprint: Fingerprint
    headers: Dict[str, str]

    @classmethod
    def load(cls, data: Union[dict, str]) -> "FingerprintFormat":
        """
        Load fingerprint from dictionary or JSON string.

        This is the recommended public API for loading fingerprint data.

        Args:
            data: Either a dictionary or JSON string containing fingerprint data

        Returns:
            FingerprintFormat: Loaded fingerprint format object

        Raises:
            ValueError: If data is invalid or cannot be parsed

        Example:
            ```python
            # From dictionary
            fingerprint = FingerprintFormat.load({"fingerprint": {...}, "headers": {...}})

            # From JSON string
            fingerprint = FingerprintFormat.load('{"fingerprint": {...}, "headers": {...}}')
            ```
        """
        if isinstance(data, str):
            return cls._from_json(data)
        elif isinstance(data, dict):
            return cls._from_dict(data)
        else:
            raise ValueError(
                f"Invalid data type: expected dict or str, got {type(data)}"
            )

    def _to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return asdict(self)

    def _to_json(self, indent: int = 2, ensure_ascii: bool = False) -> str:
        """Convert to JSON string format."""
        return json.dumps(self._to_dict(), indent=indent, ensure_ascii=ensure_ascii)

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "FingerprintFormat":
        """Create FingerprintFormat from dictionary data."""
        if not data or not isinstance(data, dict):
            raise ValueError("Invalid data: expected a dictionary")

        fingerprint_dict = data.get("fingerprint") or {}
        headers_dict = data.get("headers") or {}

        # Convert nested dictionaries to dataclass instances
        screen_dict = fingerprint_dict.get("screen") or {}
        try:
            screen = ScreenFingerprint(**screen_dict)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Failed to create ScreenFingerprint: {e}")

        # Handle UserAgentData - safely get navigator data
        nav_dict = fingerprint_dict.get("navigator") or {}
        user_agent_data_dict = nav_dict.get("userAgentData") or {}

        # Handle brands and fullVersionList safely
        brands_data = user_agent_data_dict.get("brands", [])
        brands = []
        if isinstance(brands_data, list):
            for brand_data in brands_data:
                if isinstance(brand_data, dict):
                    brands.append(
                        Brand(
                            brand=brand_data.get("brand", ""),
                            version=brand_data.get("version", ""),
                        )
                    )

        full_version_list_data = user_agent_data_dict.get("fullVersionList", [])
        full_version_list = []
        if isinstance(full_version_list_data, list):
            for brand_data in full_version_list_data:
                if isinstance(brand_data, dict):
                    full_version_list.append(
                        Brand(
                            brand=brand_data.get("brand", ""),
                            version=brand_data.get("version", ""),
                        )
                    )

        user_agent_data = UserAgentData(
            brands=brands,
            mobile=user_agent_data_dict.get("mobile", False),
            platform=user_agent_data_dict.get("platform", ""),
            architecture=user_agent_data_dict.get("architecture", ""),
            bitness=user_agent_data_dict.get("bitness", ""),
            fullVersionList=full_version_list,
            model=user_agent_data_dict.get("model", ""),
            platformVersion=user_agent_data_dict.get("platformVersion", ""),
            uaFullVersion=user_agent_data_dict.get("uaFullVersion", ""),
        )

        # Handle ExtraProperties
        extra_props_dict = nav_dict.get("extraProperties") or {}
        extra_props = ExtraProperties(
            vendorFlavors=extra_props_dict.get("vendorFlavors", []),
            isBluetoothSupported=extra_props_dict.get("isBluetoothSupported", False),
            globalPrivacyControl=extra_props_dict.get("globalPrivacyControl"),
            pdfViewerEnabled=extra_props_dict.get("pdfViewerEnabled", True),
            installedApps=extra_props_dict.get("installedApps", []),
        )

        # Create NavigatorFingerprint
        navigator = NavigatorFingerprint(
            userAgent=nav_dict.get("userAgent", ""),
            userAgentData=user_agent_data,
            doNotTrack=nav_dict.get("doNotTrack", ""),
            appCodeName=nav_dict.get("appCodeName", ""),
            appName=nav_dict.get("appName", ""),
            appVersion=nav_dict.get("appVersion", ""),
            oscpu=nav_dict.get("oscpu", ""),
            webdriver=nav_dict.get("webdriver", ""),
            language=nav_dict.get("language", ""),
            languages=nav_dict.get("languages", []),
            platform=nav_dict.get("platform", ""),
            deviceMemory=nav_dict.get("deviceMemory"),
            hardwareConcurrency=nav_dict.get("hardwareConcurrency", 8),
            product=nav_dict.get("product", ""),
            productSub=nav_dict.get("productSub", ""),
            vendor=nav_dict.get("vendor", ""),
            vendorSub=nav_dict.get("vendorSub", ""),
            maxTouchPoints=nav_dict.get("maxTouchPoints"),
            extraProperties=extra_props,
        )

        # Create VideoCard
        video_card_dict = fingerprint_dict.get("videoCard") or {}
        try:
            video_card = VideoCard(**video_card_dict)
        except (TypeError, ValueError) as e:
            _logger.warning(f"Failed to create VideoCard: {e}, using defaults")
            video_card = VideoCard(renderer="Unknown", vendor="Unknown")

        # Create main Fingerprint
        fingerprint = Fingerprint(
            screen=screen,
            navigator=navigator,
            videoCodecs=fingerprint_dict.get("videoCodecs", {}),
            audioCodecs=fingerprint_dict.get("audioCodecs", {}),
            pluginsData=fingerprint_dict.get("pluginsData", {}),
            battery=fingerprint_dict.get("battery"),
            videoCard=video_card,
            multimediaDevices=fingerprint_dict.get("multimediaDevices", []),
            fonts=fingerprint_dict.get("fonts", []),
            mockWebRTC=fingerprint_dict.get("mockWebRTC", False),
            slim=fingerprint_dict.get("slim"),
        )

        return cls(fingerprint=fingerprint, headers=headers_dict)

    @classmethod
    def _from_json(cls, json_str: str) -> "FingerprintFormat":
        """Create FingerprintFormat from JSON string."""
        data = json.loads(json_str)
        return cls._from_dict(data)

    @classmethod
    def create(
        cls,
        screen: ScreenFingerprint,
        navigator: NavigatorFingerprint,
        video_card: VideoCard,
        headers: Dict[str, str],
        video_codecs: Optional[Dict[str, str]] = None,
        audio_codecs: Optional[Dict[str, str]] = None,
        plugins_data: Optional[Dict[str, str]] = None,
        battery: Optional[Dict[str, str]] = None,
        multimedia_devices: Optional[List[str]] = None,
        fonts: Optional[List[str]] = None,
        mock_webrtc: bool = False,
        slim: Optional[bool] = None,
    ) -> "FingerprintFormat":
        """
        Create FingerprintFormat directly using component classes.

        Args:
            screen: ScreenFingerprint object
            navigator: NavigatorFingerprint object
            video_card: VideoCard object
            headers: Headers dictionary
            video_codecs: Video codecs dictionary (optional)
            audio_codecs: Audio codecs dictionary (optional)
            plugins_data: Plugins data dictionary (optional)
            battery: Battery information dictionary (optional)
            multimedia_devices: List of multimedia devices (optional)
            fonts: List of available fonts (optional)
            mock_webrtc: Whether WebRTC is mocked (default: False)
            slim: Slim mode flag (optional)

        Returns:
            FingerprintFormat: Complete fingerprint format object
        """
        fingerprint = Fingerprint(
            screen=screen,
            navigator=navigator,
            videoCodecs=video_codecs or {},
            audioCodecs=audio_codecs or {},
            pluginsData=plugins_data or {},
            battery=battery,
            videoCard=video_card,
            multimediaDevices=multimedia_devices or [],
            fonts=fonts or [],
            mockWebRTC=mock_webrtc,
            slim=slim,
        )

        return cls(fingerprint=fingerprint, headers=headers)
