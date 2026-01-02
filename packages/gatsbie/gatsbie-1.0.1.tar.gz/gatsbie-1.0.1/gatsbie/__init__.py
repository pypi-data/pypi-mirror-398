"""Gatsbie SDK - Official Python SDK for the Gatsbie Captcha API."""

from .client import Client
from .errors import (
    APIError,
    ERR_AUTH_FAILED,
    ERR_INSUFFICIENT_CREDITS,
    ERR_INTERNAL_ERROR,
    ERR_INVALID_REQUEST,
    ERR_SOLVE_FAILED,
    ERR_UPSTREAM_ERROR,
    GatsbieError,
    RequestError,
)
from .types import (
    AkamaiRequest,
    AkamaiSolution,
    CloudflareWAFRequest,
    CloudflareWAFSolution,
    DatadomeRequest,
    DatadomeSliderRequest,
    DatadomeSliderSolution,
    DatadomeSolution,
    HealthResponse,
    PerimeterXCookies,
    PerimeterXRequest,
    PerimeterXSolution,
    RecaptchaV3Request,
    RecaptchaV3Solution,
    ShapeRequest,
    ShapeSolution,
    SolveResponse,
    TurnstileRequest,
    TurnstileSolution,
    VercelRequest,
    VercelSolution,
)

__version__ = "1.0.0"

__all__ = [
    # Client
    "Client",
    # Errors
    "GatsbieError",
    "APIError",
    "RequestError",
    "ERR_AUTH_FAILED",
    "ERR_INSUFFICIENT_CREDITS",
    "ERR_INVALID_REQUEST",
    "ERR_UPSTREAM_ERROR",
    "ERR_SOLVE_FAILED",
    "ERR_INTERNAL_ERROR",
    # Types
    "HealthResponse",
    "SolveResponse",
    # Request types
    "DatadomeRequest",
    "RecaptchaV3Request",
    "AkamaiRequest",
    "VercelRequest",
    "ShapeRequest",
    "TurnstileRequest",
    "PerimeterXRequest",
    "CloudflareWAFRequest",
    "DatadomeSliderRequest",
    # Solution types
    "DatadomeSolution",
    "RecaptchaV3Solution",
    "AkamaiSolution",
    "VercelSolution",
    "ShapeSolution",
    "TurnstileSolution",
    "PerimeterXCookies",
    "PerimeterXSolution",
    "CloudflareWAFSolution",
    "DatadomeSliderSolution",
]
