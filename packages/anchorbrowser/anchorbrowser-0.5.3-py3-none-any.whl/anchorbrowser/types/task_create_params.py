# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from typing_extensions import Literal, Required, Annotated, TypeAlias, TypedDict

from .._utils import PropertyInfo

__all__ = [
    "TaskCreateParams",
    "BrowserConfiguration",
    "BrowserConfigurationLiveView",
    "BrowserConfigurationProxy",
    "BrowserConfigurationProxyAnchorProxy",
    "BrowserConfigurationProxyCustomProxy",
    "BrowserConfigurationRecording",
    "BrowserConfigurationTimeout",
]


class TaskCreateParams(TypedDict, total=False):
    language: Required[Literal["typescript"]]
    """Programming language for the task"""

    name: Required[str]
    """Task name (letters, numbers, hyphens, and underscores only)"""

    browser_configuration: Annotated[BrowserConfiguration, PropertyInfo(alias="browserConfiguration")]
    """Browser configuration for task execution"""

    code: str
    """Base64 encoded task code (optional)"""

    description: str
    """Optional description of the task"""


class BrowserConfigurationLiveView(TypedDict, total=False):
    """Configuration for live viewing the browser session."""

    read_only: bool
    """Enable or disable read-only mode for live viewing. Defaults to `false`."""


class BrowserConfigurationProxyAnchorProxy(TypedDict, total=False):
    active: Required[bool]

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


class BrowserConfigurationProxyCustomProxy(TypedDict, total=False):
    active: Required[bool]

    password: Required[str]
    """Proxy password"""

    server: Required[str]
    """Proxy server address"""

    type: Required[Literal["custom"]]

    username: Required[str]
    """Proxy username"""


BrowserConfigurationProxy: TypeAlias = Union[BrowserConfigurationProxyAnchorProxy, BrowserConfigurationProxyCustomProxy]


class BrowserConfigurationRecording(TypedDict, total=False):
    """Configuration for session recording."""

    active: bool
    """Enable or disable video recording of the browser session. Defaults to `true`."""


class BrowserConfigurationTimeout(TypedDict, total=False):
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


class BrowserConfiguration(TypedDict, total=False):
    """Browser configuration for task execution"""

    initial_url: str
    """The URL to navigate to when the browser session starts.

    If not provided, the browser will load an empty page.
    """

    live_view: BrowserConfigurationLiveView
    """Configuration for live viewing the browser session."""

    proxy: BrowserConfigurationProxy
    """Proxy Documentation available at [Proxy Documentation](/advanced/proxy)"""

    recording: BrowserConfigurationRecording
    """Configuration for session recording."""

    timeout: BrowserConfigurationTimeout
    """Timeout configurations for the browser session."""
