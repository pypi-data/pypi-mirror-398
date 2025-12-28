"""OAuth authentication flow."""

import webbrowser
from datetime import datetime, timedelta
from typing import Any

import httpx

from inverseui.config import get_config
from inverseui.utils.keychain import clear_tokens, get_tokens, store_tokens


class AuthManager:
    """Manages OAuth authentication flow."""

    def __init__(self):
        self.config = get_config()

    async def login(self) -> dict[str, Any]:
        """Start OAuth login flow with one-time code exchange."""
        # Build login URL with cli=1 flag
        login_url = f"{self.config.web_base_url}/login?cli=1"

        # Try to open browser
        browser_opened = False
        try:
            browser_opened = webbrowser.open(login_url)
        except Exception:
            pass

        # Clean output
        print()
        if browser_opened:
            print("  Browser opened for login.")
        else:
            print("  Could not open browser automatically.")
        print()
        print("  If needed, open this URL manually:")
        print(f"  {login_url}")
        print()

        # Prompt user to paste the one-time code
        try:
            code = input("  Paste code here: ").strip()
        except (KeyboardInterrupt, EOFError):
            raise

        if not code:
            raise RuntimeError("No code provided")

        print()
        print("  Verifying...")

        # Exchange code for token
        user_info = await self._exchange_code(code)

        return {
            "user": user_info.get("email") or "unknown",
            "expires_at": user_info.get("expires_at"),
        }

    async def _exchange_code(self, code: str) -> dict[str, Any]:
        """Exchange one-time code for token."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.config.api_base_url}/auth/cli/exchange",
                    json={"code": code},
                )
        except httpx.ConnectError:
            raise RuntimeError("Could not connect to server")
        except httpx.TimeoutException:
            raise RuntimeError("Connection timed out")
        except Exception:
            raise RuntimeError("Connection error")

        if response.status_code == 400:
            raise RuntimeError("Invalid or expired code")
        elif response.status_code == 404:
            raise RuntimeError("Code not found")
        elif response.status_code != 200:
            raise RuntimeError(f"Server error ({response.status_code})")

        data = response.json()

        # Extract user info from nested object
        user_data = data.get("user", {})
        user_email = user_data.get("email")

        # Calculate expiration (default 7 days if not provided)
        expires_in = data.get("expires_in", 7 * 24 * 3600)
        expires_at = datetime.now() + timedelta(seconds=expires_in)

        # Store token
        store_tokens(
            access_token=data["token"],
            refresh_token=data.get("refresh_token"),
            expires_at=expires_at,
            user_email=user_email,
        )

        return {
            "email": user_email,
            "expires_at": expires_at.isoformat(),
        }

    def logout(self) -> None:
        """Clear stored tokens."""
        clear_tokens()

    def get_status(self) -> dict[str, Any]:
        """Get current authentication status."""
        tokens = get_tokens()
        if not tokens:
            return {"authenticated": False}

        # Check expiration
        if tokens.expires_at and datetime.now() >= tokens.expires_at:
            return {
                "authenticated": False,
                "reason": "Token expired",
            }

        return {
            "authenticated": True,
            "user": tokens.user_email,
            "expires_at": tokens.expires_at.isoformat() if tokens.expires_at else None,
        }

    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        status = self.get_status()
        return status.get("authenticated", False)

    def get_access_token(self) -> str | None:
        """Get the current access token."""
        tokens = get_tokens()
        if not tokens:
            return None
        if tokens.expires_at and datetime.now() >= tokens.expires_at:
            return None
        return tokens.access_token

    async def refresh_if_needed(self) -> bool:
        """Refresh token if expired or about to expire."""
        tokens = get_tokens()
        if not tokens or not tokens.refresh_token:
            return False

        # Refresh if expires in less than 5 minutes
        if tokens.expires_at:
            time_until_expiry = tokens.expires_at - datetime.now()
            if time_until_expiry.total_seconds() > 300:
                return True  # No refresh needed

        # Attempt refresh
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config.api_base_url}/auth/refresh",
                json={"refresh_token": tokens.refresh_token},
            )

            if response.status_code != 200:
                return False

            data = response.json()
            expires_in = data.get("expires_in", 3600)
            expires_at = datetime.now() + timedelta(seconds=expires_in)

            store_tokens(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token", tokens.refresh_token),
                expires_at=expires_at,
                user_email=tokens.user_email,
            )

            return True
