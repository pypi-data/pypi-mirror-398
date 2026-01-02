"""Gatsbie API client."""

from typing import Any, Dict, Optional, Type, TypeVar

import httpx

from .errors import APIError, RequestError
from .types import (
    AkamaiCookies,
    AkamaiRequest,
    AkamaiSolution,
    CloudflareWAFCookies,
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

T = TypeVar("T")

DEFAULT_BASE_URL = "https://api2.gatsbie.io"
DEFAULT_TIMEOUT = 120.0


class Client:
    """Gatsbie API client.

    Args:
        api_key: Your Gatsbie API key (should start with 'gats_').
        base_url: Custom base URL for the API (optional).
        timeout: Request timeout in seconds (default: 120).
        http_client: Custom httpx.Client instance (optional).

    Example:
        >>> client = Client("gats_your_api_key")
        >>> response = client.solve_turnstile(TurnstileRequest(
        ...     proxy="http://user:pass@proxy:8080",
        ...     target_url="https://example.com",
        ...     site_key="0x4AAAAAAABS7TtLxsNa7Z2e"
        ... ))
        >>> print(response.solution.token)
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        http_client: Optional[httpx.Client] = None,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._client = http_client or httpx.Client(timeout=timeout)
        self._owns_client = http_client is None

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        if self._owns_client:
            self._client.close()

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an authenticated request to the API."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            response = self._client.request(
                method,
                f"{self.base_url}{path}",
                headers=headers,
                json=body,
            )
        except httpx.RequestError as e:
            raise RequestError(f"Request failed: {e}") from e

        data = response.json()

        if response.status_code >= 400:
            error = data.get("error", {})
            raise APIError(
                code=error.get("code", "UNKNOWN"),
                message=error.get("message", "Unknown error"),
                details=error.get("details"),
                timestamp=error.get("timestamp"),
                http_status=response.status_code,
            )

        return data

    def _get(self, path: str) -> Dict[str, Any]:
        """Make a GET request."""
        return self._request("GET", path)

    def _post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request."""
        return self._request("POST", path, body)

    # ========================================================================
    # API Methods
    # ========================================================================

    def health(self) -> HealthResponse:
        """Check the API server health status.

        Returns:
            HealthResponse with the server status.
        """
        data = self._get("/health")
        return HealthResponse(status=data["status"])

    def solve_datadome(
        self, request: DatadomeRequest
    ) -> SolveResponse[DatadomeSolution]:
        """Solve a Datadome device check challenge.

        Args:
            request: The Datadome request parameters.

        Returns:
            SolveResponse containing the Datadome solution.
        """
        body = {
            "task_type": "datadome-device-check",
            "proxy": request.proxy,
            "target_url": request.target_url,
            "target_method": request.target_method,
        }
        data = self._post("/v1/solve/datadome-device-check", body)
        solution = DatadomeSolution(
            datadome=data["solution"]["datadome"],
            user_agent=data["solution"]["ua"],
        )
        return SolveResponse(
            success=data["success"],
            task_id=data["taskId"],
            service=data["service"],
            solution=solution,
            cost=data["cost"],
            solve_time=data["solveTime"],
        )

    def solve_recaptcha_v3(
        self, request: RecaptchaV3Request
    ) -> SolveResponse[RecaptchaV3Solution]:
        """Solve a reCAPTCHA v3 challenge.

        Args:
            request: The reCAPTCHA v3 request parameters.

        Returns:
            SolveResponse containing the reCAPTCHA v3 solution.
        """
        body = {
            "task_type": "recaptchav3",
            "proxy": request.proxy,
            "target_url": request.target_url,
            "site_key": request.site_key,
        }
        if request.action:
            body["action"] = request.action
        if request.title:
            body["title"] = request.title
        if request.enterprise:
            body["enterprise"] = request.enterprise

        data = self._post("/v1/solve/recaptchav3", body)
        solution = RecaptchaV3Solution(
            token=data["solution"]["token"],
            user_agent=data["solution"]["ua"],
        )
        return SolveResponse(
            success=data["success"],
            task_id=data["taskId"],
            service=data["service"],
            solution=solution,
            cost=data["cost"],
            solve_time=data["solveTime"],
        )

    def solve_akamai(self, request: AkamaiRequest) -> SolveResponse[AkamaiSolution]:
        """Solve an Akamai bot management challenge.

        Args:
            request: The Akamai request parameters.

        Returns:
            SolveResponse containing the Akamai solution.
        """
        body = {
            "task_type": "akamai",
            "proxy": request.proxy,
            "target_url": request.target_url,
            "akamai_js_url": request.akamai_js_url,
        }
        if request.page_fp:
            body["page_fp"] = request.page_fp

        data = self._post("/v1/solve/akamai", body)
        sol = data["solution"]
        cookies_dict = sol["cookies_dict"]
        cookies = AkamaiCookies(
            abck=cookies_dict["_abck"],
            bm_sz=cookies_dict["bm_sz"],
            country=cookies_dict.get("Country"),
            usr_locale=cookies_dict.get("UsrLocale"),
        )
        solution = AkamaiSolution(
            cookies=cookies,
            user_agent=sol["ua"],
        )
        return SolveResponse(
            success=data["success"],
            task_id=data["taskId"],
            service=data["service"],
            solution=solution,
            cost=data["cost"],
            solve_time=data["solveTime"],
        )

    def solve_vercel(self, request: VercelRequest) -> SolveResponse[VercelSolution]:
        """Solve a Vercel bot protection challenge.

        Args:
            request: The Vercel request parameters.

        Returns:
            SolveResponse containing the Vercel solution.
        """
        body = {
            "task_type": "vercel",
            "proxy": request.proxy,
            "target_url": request.target_url,
        }
        data = self._post("/v1/solve/vercel", body)
        solution = VercelSolution(
            vcrcs=data["solution"]["_vcrcs"],
            user_agent=data["solution"]["ua"],
        )
        return SolveResponse(
            success=data["success"],
            task_id=data["taskId"],
            service=data["service"],
            solution=solution,
            cost=data["cost"],
            solve_time=data["solveTime"],
        )

    def solve_shape(self, request: ShapeRequest) -> SolveResponse[ShapeSolution]:
        """Solve a Shape antibot challenge.

        Args:
            request: The Shape request parameters.

        Returns:
            SolveResponse containing the Shape solution with dynamic headers.
        """
        body = {
            "task_type": "shape",
            "proxy": request.proxy,
            "target_url": request.target_url,
            "target_api": request.target_api,
            "shape_js_url": request.shape_js_url,
            "title": request.title,
            "method": request.method,
        }
        data = self._post("/v1/solve/shape", body)
        sol = data["solution"].copy()
        # Shape returns dynamic headers, extract User-Agent separately
        user_agent = sol.pop("User-Agent", "")
        solution = ShapeSolution(
            headers=sol,
            user_agent=user_agent,
        )
        return SolveResponse(
            success=data["success"],
            task_id=data["taskId"],
            service=data["service"],
            solution=solution,
            cost=data["cost"],
            solve_time=data["solveTime"],
        )

    def solve_turnstile(
        self, request: TurnstileRequest
    ) -> SolveResponse[TurnstileSolution]:
        """Solve a Cloudflare Turnstile challenge.

        Args:
            request: The Turnstile request parameters.

        Returns:
            SolveResponse containing the Turnstile solution.
        """
        body = {
            "task_type": "turnstile",
            "proxy": request.proxy,
            "target_url": request.target_url,
            "site_key": request.site_key,
        }
        data = self._post("/v1/solve/turnstile", body)
        solution = TurnstileSolution(
            token=data["solution"]["token"],
            user_agent=data["solution"]["ua"],
        )
        return SolveResponse(
            success=data["success"],
            task_id=data["taskId"],
            service=data["service"],
            solution=solution,
            cost=data["cost"],
            solve_time=data["solveTime"],
        )

    def solve_perimeterx(
        self, request: PerimeterXRequest
    ) -> SolveResponse[PerimeterXSolution]:
        """Solve a PerimeterX Invisible challenge.

        Args:
            request: The PerimeterX request parameters.

        Returns:
            SolveResponse containing the PerimeterX solution.
        """
        body = {
            "task_type": "perimeterx_invisible",
            "proxy": request.proxy,
            "target_url": request.target_url,
            "perimeterx_js_url": request.perimeterx_js_url,
            "pxAppId": request.px_app_id,
        }
        data = self._post("/v1/solve/perimeterx-invisible", body)
        cookies_data = data["solution"]["perimeterx_cookies"]
        cookies = PerimeterXCookies(
            px3=cookies_data["_px3"],
            pxde=cookies_data["_pxde"],
            pxvid=cookies_data["_pxvid"],
            pxcts=cookies_data["pxcts"],
        )
        solution = PerimeterXSolution(
            cookies=cookies,
            user_agent=data["solution"]["ua"],
        )
        return SolveResponse(
            success=data["success"],
            task_id=data["taskId"],
            service=data["service"],
            solution=solution,
            cost=data["cost"],
            solve_time=data["solveTime"],
        )

    def solve_cloudflare_waf(
        self, request: CloudflareWAFRequest
    ) -> SolveResponse[CloudflareWAFSolution]:
        """Solve a Cloudflare WAF challenge.

        Args:
            request: The Cloudflare WAF request parameters.

        Returns:
            SolveResponse containing the Cloudflare WAF solution.
        """
        body = {
            "task_type": "cloudflare_waf",
            "proxy": request.proxy,
            "target_url": request.target_url,
            "target_method": request.target_method,
        }
        data = self._post("/v1/solve/cloudflare-waf", body)
        cookies_data = data["solution"]["cookies"]
        cookies = CloudflareWAFCookies(
            cf_clearance=cookies_data["cf_clearance"],
        )
        solution = CloudflareWAFSolution(
            cookies=cookies,
            user_agent=data["solution"]["ua"],
        )
        return SolveResponse(
            success=data["success"],
            task_id=data["taskId"],
            service=data["service"],
            solution=solution,
            cost=data["cost"],
            solve_time=data["solveTime"],
        )

    def solve_datadome_slider(
        self, request: DatadomeSliderRequest
    ) -> SolveResponse[DatadomeSliderSolution]:
        """Solve a Datadome Slider CAPTCHA challenge.

        Args:
            request: The Datadome Slider request parameters.

        Returns:
            SolveResponse containing the Datadome Slider solution.
        """
        body = {
            "task_type": "datadome-slider",
            "proxy": request.proxy,
            "target_url": request.target_url,
            "target_method": request.target_method,
        }
        data = self._post("/v1/solve/datadome-slider", body)
        solution = DatadomeSliderSolution(
            datadome=data["solution"]["datadome"],
            user_agent=data["solution"]["ua"],
        )
        return SolveResponse(
            success=data["success"],
            task_id=data["taskId"],
            service=data["service"],
            solution=solution,
            cost=data["cost"],
            solve_time=data["solveTime"],
        )
