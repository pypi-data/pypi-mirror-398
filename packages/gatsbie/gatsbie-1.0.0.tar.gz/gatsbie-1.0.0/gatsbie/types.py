"""Type definitions for the Gatsbie SDK."""

from dataclasses import dataclass, field
from typing import Any, Dict, Generic, Optional, TypeVar

T = TypeVar("T")


# ============================================================================
# Response Types
# ============================================================================


@dataclass
class HealthResponse:
    """Response from the health check endpoint."""

    status: str


@dataclass
class SolveResponse(Generic[T]):
    """Generic response for successful captcha solves."""

    success: bool
    task_id: str
    service: str
    solution: T
    cost: float
    solve_time: float


# ============================================================================
# Solution Types
# ============================================================================


@dataclass
class DatadomeSolution:
    """Solution for Datadome challenges."""

    datadome: str
    user_agent: str


@dataclass
class RecaptchaV3Solution:
    """Solution for reCAPTCHA v3 challenges."""

    token: str
    user_agent: str


@dataclass
class AkamaiSolution:
    """Solution for Akamai challenges."""

    abck: str
    bm_sz: str
    user_agent: str
    country: Optional[str] = None
    usr_locale: Optional[str] = None


@dataclass
class VercelSolution:
    """Solution for Vercel challenges."""

    vcrcs: str
    user_agent: str


@dataclass
class ShapeSolution:
    """Solution for Shape challenges.

    Shape uses dynamic header names that vary by site.
    Access the headers dict to get all solution headers.
    """

    headers: Dict[str, str]
    user_agent: str


@dataclass
class TurnstileSolution:
    """Solution for Cloudflare Turnstile challenges."""

    token: str
    user_agent: str


@dataclass
class PerimeterXCookies:
    """PerimeterX cookies needed for requests."""

    px3: str
    pxde: str
    pxvid: str
    pxcts: str


@dataclass
class PerimeterXSolution:
    """Solution for PerimeterX challenges."""

    cookies: PerimeterXCookies
    user_agent: str


@dataclass
class CloudflareWAFSolution:
    """Solution for Cloudflare WAF challenges."""

    cf_clearance: str
    user_agent: str


@dataclass
class DatadomeSliderSolution:
    """Solution for Datadome Slider challenges."""

    datadome: str
    user_agent: str


# ============================================================================
# Request Types
# ============================================================================


@dataclass
class DatadomeRequest:
    """Request for solving Datadome device check challenges."""

    proxy: str
    target_url: str
    target_method: str = "GET"


@dataclass
class RecaptchaV3Request:
    """Request for solving reCAPTCHA v3 challenges."""

    proxy: str
    target_url: str
    site_key: str
    action: Optional[str] = None
    title: Optional[str] = None
    enterprise: bool = False


@dataclass
class AkamaiRequest:
    """Request for solving Akamai challenges."""

    proxy: str
    target_url: str
    akamai_js_url: str
    page_fp: Optional[str] = None


@dataclass
class VercelRequest:
    """Request for solving Vercel challenges."""

    proxy: str
    target_url: str


@dataclass
class ShapeRequest:
    """Request for solving Shape challenges."""

    proxy: str
    target_url: str
    target_api: str
    shape_js_url: str
    title: str
    method: str


@dataclass
class TurnstileRequest:
    """Request for solving Cloudflare Turnstile challenges."""

    proxy: str
    target_url: str
    site_key: str


@dataclass
class PerimeterXRequest:
    """Request for solving PerimeterX challenges."""

    proxy: str
    target_url: str
    perimeterx_js_url: str
    px_app_id: str


@dataclass
class CloudflareWAFRequest:
    """Request for solving Cloudflare WAF challenges."""

    proxy: str
    target_url: str
    target_method: str = "GET"


@dataclass
class DatadomeSliderRequest:
    """Request for solving Datadome Slider challenges."""

    proxy: str
    target_url: str
    target_method: str = "GET"
