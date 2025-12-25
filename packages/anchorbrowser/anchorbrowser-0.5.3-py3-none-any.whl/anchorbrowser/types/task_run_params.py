# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union
from typing_extensions import Literal, Required, Annotated, TypeAlias, TypedDict

from .._utils import PropertyInfo

__all__ = [
    "RunExecuteParams",
    "OverrideBrowserConfiguration",
    "OverrideBrowserConfigurationLiveView",
    "OverrideBrowserConfigurationProxy",
    "OverrideBrowserConfigurationProxyAnchorProxy",
    "OverrideBrowserConfigurationProxyCustomProxy",
    "OverrideBrowserConfigurationRecording",
    "OverrideBrowserConfigurationTimeout",
]


class RunExecuteParams(TypedDict, total=False):
    task_id: Required[Annotated[str, PropertyInfo(alias="taskId")]]
    """Task identifier"""

    async_: Annotated[bool, PropertyInfo(alias="async")]
    """Whether to run the task asynchronously."""

    inputs: Dict[str, str]
    """Environment variables for task execution (keys must start with ANCHOR\\__)"""

    override_browser_configuration: Annotated[
        OverrideBrowserConfiguration, PropertyInfo(alias="overrideBrowserConfiguration")
    ]
    """Override browser configuration for this execution"""

    version: str
    """Version to run (draft, latest, or version number)"""


class OverrideBrowserConfigurationLiveView(TypedDict, total=False):
    """Configuration for live viewing the browser session."""

    read_only: bool
    """Enable or disable read-only mode for live viewing. Defaults to `false`."""


class OverrideBrowserConfigurationProxyAnchorProxy(TypedDict, total=False):
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


class OverrideBrowserConfigurationProxyCustomProxy(TypedDict, total=False):
    active: Required[bool]

    password: Required[str]
    """Proxy password"""

    server: Required[str]
    """Proxy server address"""

    type: Required[Literal["custom"]]

    username: Required[str]
    """Proxy username"""


OverrideBrowserConfigurationProxy: TypeAlias = Union[
    OverrideBrowserConfigurationProxyAnchorProxy, OverrideBrowserConfigurationProxyCustomProxy
]


class OverrideBrowserConfigurationRecording(TypedDict, total=False):
    """Configuration for session recording."""

    active: bool
    """Enable or disable video recording of the browser session. Defaults to `true`."""


class OverrideBrowserConfigurationTimeout(TypedDict, total=False):
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


class OverrideBrowserConfiguration(TypedDict, total=False):
    """Override browser configuration for this execution"""

    initial_url: str
    """The URL to navigate to when the browser session starts.

    If not provided, the browser will load an empty page.
    """

    live_view: OverrideBrowserConfigurationLiveView
    """Configuration for live viewing the browser session."""

    proxy: OverrideBrowserConfigurationProxy
    """Proxy Documentation available at [Proxy Documentation](/advanced/proxy)"""

    recording: OverrideBrowserConfigurationRecording
    """Configuration for session recording."""

    timeout: OverrideBrowserConfigurationTimeout
    """Timeout configurations for the browser session."""

