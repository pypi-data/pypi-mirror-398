# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from datetime import datetime
from typing_extensions import Literal, TypeAlias

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = [
    "TaskListResponse",
    "Data",
    "DataTask",
    "DataTaskBrowserConfiguration",
    "DataTaskBrowserConfigurationLiveView",
    "DataTaskBrowserConfigurationProxy",
    "DataTaskBrowserConfigurationProxyAnchorProxy",
    "DataTaskBrowserConfigurationProxyCustomProxy",
    "DataTaskBrowserConfigurationRecording",
    "DataTaskBrowserConfigurationTimeout",
]


class DataTaskBrowserConfigurationLiveView(BaseModel):
    """Configuration for live viewing the browser session."""

    read_only: Optional[bool] = None
    """Enable or disable read-only mode for live viewing. Defaults to `false`."""


class DataTaskBrowserConfigurationProxyAnchorProxy(BaseModel):
    active: bool

    city: Optional[str] = None
    """City name for precise geographic targeting.

    Supported for anchor_proxy only. Can only be used when region is also provided.
    """

    country_code: Optional[
        Literal[
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
    ] = None
    """Supported country codes ISO 2 lowercase

    **On change make sure to update the Proxy type.**
    """

    region: Optional[str] = None
    """
    Region code for more specific geographic targeting. The city parameter can only
    be used when region is also provided.
    """

    type: Optional[Literal["anchor_proxy", "anchor_residential", "anchor_mobile", "anchor_gov"]] = None
    """**On change make sure to update the country_code.**"""


class DataTaskBrowserConfigurationProxyCustomProxy(BaseModel):
    active: bool

    password: str
    """Proxy password"""

    server: str
    """Proxy server address"""

    type: Literal["custom"]

    username: str
    """Proxy username"""


DataTaskBrowserConfigurationProxy: TypeAlias = Union[
    DataTaskBrowserConfigurationProxyAnchorProxy, DataTaskBrowserConfigurationProxyCustomProxy
]


class DataTaskBrowserConfigurationRecording(BaseModel):
    """Configuration for session recording."""

    active: Optional[bool] = None
    """Enable or disable video recording of the browser session. Defaults to `true`."""


class DataTaskBrowserConfigurationTimeout(BaseModel):
    """Timeout configurations for the browser session."""

    idle_timeout: Optional[int] = None
    """
    The amount of time (in minutes) the browser session waits for new connections
    after all others are closed before stopping. Defaults to `5`.
    """

    max_duration: Optional[int] = None
    """Maximum amount of time (in minutes) for the browser to run before terminating.

    Defaults to `20`.
    """


class DataTaskBrowserConfiguration(BaseModel):
    """Browser configuration for task execution"""

    initial_url: Optional[str] = None
    """The URL to navigate to when the browser session starts.

    If not provided, the browser will load an empty page.
    """

    live_view: Optional[DataTaskBrowserConfigurationLiveView] = None
    """Configuration for live viewing the browser session."""

    proxy: Optional[DataTaskBrowserConfigurationProxy] = None
    """Proxy Documentation available at [Proxy Documentation](/advanced/proxy)"""

    recording: Optional[DataTaskBrowserConfigurationRecording] = None
    """Configuration for session recording."""

    timeout: Optional[DataTaskBrowserConfigurationTimeout] = None
    """Timeout configurations for the browser session."""


class DataTask(BaseModel):
    id: str
    """Unique identifier for the task"""

    code: str
    """Base64 encoded task code"""

    created_at: datetime = FieldInfo(alias="createdAt")
    """Task creation timestamp"""

    deleted: bool
    """Whether the task is soft deleted"""

    language: Literal["typescript"]
    """Programming language for the task"""

    latest_version: str = FieldInfo(alias="latestVersion")
    """Latest version identifier (draft, latest, or version number)"""

    name: str
    """Task name (letters, numbers, hyphens, and underscores only)"""

    team_id: str = FieldInfo(alias="teamId")
    """Team identifier that owns this task"""

    updated_at: datetime = FieldInfo(alias="updatedAt")
    """Task last update timestamp"""

    browser_configuration: Optional[DataTaskBrowserConfiguration] = FieldInfo(
        alias="browserConfiguration", default=None
    )
    """Browser configuration for task execution"""

    description: Optional[str] = None
    """Optional description of the task"""


class Data(BaseModel):
    limit: int
    """Number of tasks per page"""

    page: int
    """Current page number"""

    tasks: List[DataTask]

    total: int
    """Total number of tasks"""


class TaskListResponse(BaseModel):
    data: Optional[Data] = None
