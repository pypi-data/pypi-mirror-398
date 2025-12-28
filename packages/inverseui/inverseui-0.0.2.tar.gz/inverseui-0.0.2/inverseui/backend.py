"""Backend API client."""

from typing import TYPE_CHECKING, Any

import httpx
import structlog

from inverseui.config import get_config
from inverseui.utils.keychain import get_access_token

if TYPE_CHECKING:
    from inverseui.auth import AuthManager

log = structlog.get_logger(__name__)


class BackendClient:
    """Client for communicating with InverseUI backend API."""

    def __init__(self, auth_manager: "AuthManager | None" = None):
        self.config = get_config()
        self.auth_manager = auth_manager

    async def _ensure_auth(self):
        """Ensure token is fresh before making API calls."""
        if self.auth_manager:
            await self.auth_manager.refresh_if_needed()

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with auth token."""
        headers = {"Content-Type": "application/json"}
        token = get_access_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    # ============== TRACK API ==============

    async def get_track_resources(self, track_id: str) -> dict[str, Any]:
        """Get list of resource files for a track.

        GET /track/<track_id>/resources
        Returns: {"success": true, "resources": [{"name": "resume.pdf", "path": "resources/resume.pdf", "size": 0}]}
        """
        await self._ensure_auth()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.config.api_base_url}/track/{track_id}/resources",
                headers=self._get_headers(),
            )
            if response.status_code == 401:
                raise RuntimeError("Authentication required")
            if response.status_code == 404:
                # No resources endpoint or track not found - return empty list
                return {"success": True, "resources": []}
            response.raise_for_status()
            return response.json()

    # ============== GENERATE API ==============

    async def get_generated_code(
        self,
        track_id: str,
        regenerate: bool = False,
        framework: str | None = None,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Get generated code for a track.

        POST /generate/<track_id>
        Returns: {"success": true, "code": "...", "language": "python", "framework": "playwright", ...}
        """
        await self._ensure_auth()

        payload: dict[str, Any] = {
            "stream": False,
            "regenerate": regenerate,
        }
        if framework:
            payload["framework"] = framework
        if language:
            payload["language"] = language

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.config.api_base_url}/generate/{track_id}",
                headers=self._get_headers(),
                json=payload,
            )
            if response.status_code == 401:
                raise RuntimeError("Authentication required")
            if response.status_code == 404:
                raise RuntimeError(f"Track not found: {track_id}")
            response.raise_for_status()
            return response.json()

    async def request_fix(
        self,
        track_id: str,
        error_message: str,
        error_trace: str,
        previous_code: str,
        iteration: int = 1,
        screenshot_base64: str | None = None,
    ) -> dict[str, Any]:
        """Request a fix for failed code execution.

        POST /generate/<track_id>/fix
        Returns: {"success": true, "code": "...", "iteration": 2, "fix_explanation": "..."}
        """
        await self._ensure_auth()

        payload = {
            "error_message": error_message,
            "error_trace": error_trace,
            "previous_code": previous_code,
            "iteration": iteration,
            "stream": False,
        }
        if screenshot_base64:
            payload["screenshot"] = screenshot_base64

        async with httpx.AsyncClient(timeout=120.0) as client:  # Longer timeout for LLM
            response = await client.post(
                f"{self.config.api_base_url}/generate/{track_id}/fix",
                headers=self._get_headers(),
                json=payload,
            )
            if response.status_code == 401:
                raise RuntimeError("Authentication required")
            if response.status_code == 404:
                raise RuntimeError(f"Track not found: {track_id}")
            response.raise_for_status()
            return response.json()

    async def report_track_result(
        self,
        track_id: str,
        success: bool,
        iterations: int = 1,
        final_error: str | None = None,
    ) -> dict[str, Any]:
        """Report final execution result for a track.

        POST /generate/<track_id>/result
        """
        await self._ensure_auth()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config.api_base_url}/generate/{track_id}/result",
                headers=self._get_headers(),
                json={
                    "success": success,
                    "iterations": iterations,
                    "final_error": final_error,
                },
            )
            response.raise_for_status()
            return response.json()
