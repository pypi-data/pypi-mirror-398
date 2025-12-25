# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .._types import SequenceNotStr

__all__ = [
    "SessionCreateParams",
    "Browser",
    "BrowserAdblock",
    "BrowserCaptchaSolver",
    "BrowserDisableWebSecurity",
    "BrowserExtraStealth",
    "BrowserFullscreen",
    "BrowserHeadless",
    "BrowserP2pDownload",
    "BrowserPopupBlocker",
    "BrowserProfile",
    "BrowserViewport",
    "Integration",
    "IntegrationConfiguration",
    "IntegrationConfigurationOnePasswordAllSecretsConfig",
    "IntegrationConfigurationOnePasswordSpecificSecretsConfig",
    "Session",
    "SessionLiveView",
    "SessionProxy",
    "SessionProxyAnchorProxy",
    "SessionProxyCustomProxy",
    "SessionRecording",
    "SessionTimeout",
]


class SessionCreateParams(TypedDict, total=False):
    browser: Browser
    """Browser-specific configurations."""

    integrations: Iterable[Integration]
    """Array of integrations to load in the browser session.

    Integrations must be previously created using the Integrations API.
    """

    session: Session
    """Session-related configurations."""


class BrowserAdblock(TypedDict, total=False):
    """Configuration for ad-blocking."""

    active: bool
    """Enable or disable ad-blocking. Defaults to `true`."""


class BrowserCaptchaSolver(TypedDict, total=False):
    """Configuration for captcha-solving."""

    active: bool
    """Enable or disable captcha-solving.

    Requires proxy to be active. Defaults to `false`.
    """


class BrowserDisableWebSecurity(TypedDict, total=False):
    """Configuration for disabling web security features."""

    active: bool
    """Whether to disable web security features (CORS, same-origin policy, etc.).

    Allows accessing iframes and resources from different origins. Defaults to
    `false`.
    """


class BrowserExtraStealth(TypedDict, total=False):
    """
    Configuration for extra stealth mode to enhance browser fingerprinting protection.
    """

    active: bool
    """Enable or disable extra stealth mode."""


class BrowserFullscreen(TypedDict, total=False):
    """Configuration for fullscreen mode."""

    active: bool
    """Enable or disable fullscreen mode.

    When enabled, the browser will start in fullscreen mode. Defaults to `false`.
    """


class BrowserHeadless(TypedDict, total=False):
    """Configuration for headless mode."""

    active: bool
    """Whether browser should be headless or headful. Defaults to `false`."""


class BrowserP2pDownload(TypedDict, total=False):
    """Configuration for peer-to-peer download capture functionality."""

    active: bool
    """Enable or disable P2P downloads.

    When enabled, the browser will capture downloads for direct data extraction,
    instead of uploading them on Anchor's storage. Defaults to `false`.
    """


class BrowserPopupBlocker(TypedDict, total=False):
    """Configuration for popup blocking."""

    active: bool
    """Blocks popups, including ads and CAPTCHA consent banners.

    Requires adblock to be active. Defaults to `true`.
    """


class BrowserProfile(TypedDict, total=False):
    """Options for managing and persisting browser session profiles."""

    name: str
    """The name of the profile to be used during the browser session."""

    persist: bool
    """
    Indicates whether the browser session profile data should be saved when the
    browser session ends. Defaults to `false`.
    """


class BrowserViewport(TypedDict, total=False):
    """Configuration for the browser's viewport size."""

    height: int
    """Height of the viewport in pixels. Defaults to `900`."""

    width: int
    """Width of the viewport in pixels. Defaults to `1440`."""


class Browser(TypedDict, total=False):
    """Browser-specific configurations."""

    adblock: BrowserAdblock
    """Configuration for ad-blocking."""

    captcha_solver: BrowserCaptchaSolver
    """Configuration for captcha-solving."""

    disable_web_security: BrowserDisableWebSecurity
    """Configuration for disabling web security features."""

    extensions: SequenceNotStr[str]
    """Array of extension IDs to load in the browser session.

    Extensions must be previously uploaded using the Extensions API.
    """

    extra_stealth: BrowserExtraStealth
    """
    Configuration for extra stealth mode to enhance browser fingerprinting
    protection.
    """

    fullscreen: BrowserFullscreen
    """Configuration for fullscreen mode."""

    headless: BrowserHeadless
    """Configuration for headless mode."""

    p2p_download: BrowserP2pDownload
    """Configuration for peer-to-peer download capture functionality."""

    popup_blocker: BrowserPopupBlocker
    """Configuration for popup blocking."""

    profile: BrowserProfile
    """Options for managing and persisting browser session profiles."""

    viewport: BrowserViewport
    """Configuration for the browser's viewport size."""


class IntegrationConfigurationOnePasswordAllSecretsConfig(TypedDict, total=False):
    load_mode: Required[Literal["all"]]
    """Load all secrets from 1Password"""


class IntegrationConfigurationOnePasswordSpecificSecretsConfig(TypedDict, total=False):
    load_mode: Required[Literal["specific"]]
    """Load specific secrets from 1Password"""

    secrets: Required[SequenceNotStr[str]]
    """Array of secret references to load"""


IntegrationConfiguration: TypeAlias = Union[
    IntegrationConfigurationOnePasswordAllSecretsConfig, IntegrationConfigurationOnePasswordSpecificSecretsConfig
]


class Integration(TypedDict, total=False):
    id: Required[str]
    """Unique integration ID"""

    configuration: Required[IntegrationConfiguration]

    type: Required[Literal["1PASSWORD"]]
    """Integration type"""


class SessionLiveView(TypedDict, total=False):
    """Configuration for live viewing the browser session."""

    read_only: bool
    """Enable or disable read-only mode for live viewing. Defaults to `false`."""


class SessionProxyAnchorProxy(TypedDict, total=False):
    active: Required[bool]

    """Enable or disable proxy usage. Defaults to `false`."""
    city: str
    """City name for precise geographic targeting.

    Supported for anchor_proxy only. Can only be used when region is also provided.
    """

    country_code: Literal[
        "af",
        "al",
        "dz",
        "ad",
        "ao",
        "as",
        "ag",
        "ar",
        "am",
        "aw",
        "au",
        "at",
        "az",
        "bs",
        "bh",
        "bb",
        "by",
        "be",
        "bz",
        "bj",
        "bm",
        "bo",
        "ba",
        "br",
        "bg",
        "bf",
        "cm",
        "ca",
        "cv",
        "td",
        "cl",
        "co",
        "cg",
        "cr",
        "ci",
        "hr",
        "cu",
        "cy",
        "cz",
        "dk",
        "dm",
        "do",
        "ec",
        "eg",
        "sv",
        "ee",
        "et",
        "fo",
        "fi",
        "fr",
        "gf",
        "pf",
        "ga",
        "gm",
        "ge",
        "de",
        "gh",
        "gi",
        "gr",
        "gd",
        "gp",
        "gt",
        "gg",
        "gn",
        "gw",
        "gy",
        "ht",
        "hn",
        "hu",
        "is",
        "in",
        "ir",
        "iq",
        "ie",
        "il",
        "it",
        "jm",
        "jp",
        "jo",
        "kz",
        "kw",
        "kg",
        "lv",
        "lb",
        "ly",
        "li",
        "lt",
        "lu",
        "mk",
        "ml",
        "mt",
        "mq",
        "mr",
        "mx",
        "md",
        "mc",
        "me",
        "ma",
        "nl",
        "nz",
        "ni",
        "ng",
        "no",
        "pk",
        "pa",
        "py",
        "pe",
        "ph",
        "pl",
        "pt",
        "pr",
        "qa",
        "ro",
        "lc",
        "sm",
        "sa",
        "sn",
        "rs",
        "sc",
        "sl",
        "sk",
        "si",
        "so",
        "za",
        "kr",
        "es",
        "sr",
        "se",
        "ch",
        "sy",
        "st",
        "tw",
        "tj",
        "tg",
        "tt",
        "tn",
        "tr",
        "tc",
        "ua",
        "ae",
        "us",
        "uy",
        "uz",
        "ve",
        "ye",
        "bd",
        "bw",
        "bn",
        "bi",
        "kh",
        "cn",
        "dj",
        "gq",
        "sz",
        "fj",
        "hk",
        "id",
        "ke",
        "la",
        "ls",
        "lr",
        "mg",
        "mw",
        "my",
        "mv",
        "mn",
        "mz",
        "mm",
        "na",
        "np",
        "nc",
        "ne",
        "om",
        "pg",
        "ru",
        "rw",
        "ws",
        "sg",
        "ss",
        "lk",
        "sd",
        "tz",
        "th",
        "tl",
        "tm",
        "ug",
        "gb",
        "vu",
        "vn",
        "zm",
        "zw",
        "bt",
        "mu",
    ]
    """Supported country codes ISO 2 lowercase

    **On change make sure to update the Proxy type.**
    """

    region: str
    """
    Region code for more specific geographic targeting. The city parameter can only
    be used when region is also provided.
    """

    type: Literal["anchor_proxy", "anchor_residential", "anchor_mobile", "anchor_gov"]
    """**On change make sure to update the country_code.**"""


class SessionProxyCustomProxy(TypedDict, total=False):
    active: Required[bool]

    password: Required[str]
    """Proxy password"""

    server: Required[str]
    """Proxy server address"""

    type: Required[Literal["custom"]]

    username: Required[str]
    """Proxy username"""


SessionProxy: TypeAlias = Union[SessionProxyAnchorProxy, SessionProxyCustomProxy]


class SessionRecording(TypedDict, total=False):
    """Configuration for session recording."""

    active: bool
    """Enable or disable video recording of the browser session. Defaults to `true`."""


class SessionTimeout(TypedDict, total=False):
    """Timeout configurations for the browser session."""

    idle_timeout: int
    """
    The amount of time (in minutes) the browser session waits for new connections
    after all others are closed before stopping. Defaults to `5`.
    """

    max_duration: int
    """Maximum amount of time (in minutes) for the browser to run before terminating.

    Defaults to `20`.
    """


class Session(TypedDict, total=False):
    """Session-related configurations."""

    initial_url: str
    """The URL to navigate to when the browser session starts.

    If not provided, the browser will load an empty page.
    """

    live_view: SessionLiveView
    """Configuration for live viewing the browser session."""

    proxy: SessionProxy
    """Proxy Documentation available at [Proxy Documentation](/advanced/proxy)"""

    recording: SessionRecording
    """Configuration for session recording."""

    timeout: SessionTimeout
    """Timeout configurations for the browser session."""
