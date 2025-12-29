import os
import aiohttp
from typing import Dict, Any, Optional
import json

# Import necessary libraries for IAP authentication
from google.auth.transport.requests import Request
from google.oauth2 import service_account


class TokenVerifyClient:
    """Client for interacting with Botrun token verification API."""

    def __init__(self, api_base: Optional[str] = None):
        """
        Initialize the token verify client.

        Args:
            api_base: Base URL for the Botrun API. If None, will use BOTRUN_BACK_API_BASE env var.
        """
        if os.getenv("BOTRUN_BACK_API_BASE", "") == "":
            return
        self.api_base = api_base or os.getenv("BOTRUN_BACK_API_BASE")
        if not self.api_base:
            raise ValueError("BOTRUN_BACK_API_BASE environment variable not set")

        # Get IAP configuration from environment variables
        self.iap_client_id = os.getenv("IAP_CLIENT_ID")
        self.iap_service_account_key_file = os.getenv("IAP_SERVICE_ACCOUNT_KEY_FILE")

        from botrun_flow_lang.utils.botrun_logger import get_default_botrun_logger

        self.logger = get_default_botrun_logger()

    def _get_iap_jwt(self) -> str:
        """
        Generate a JWT token for IAP authentication.

        Returns:
            JWT token as string

        Raises:
            ValueError: If the service account file can't be read or token generation fails
        """
        try:
            credentials = service_account.IDTokenCredentials.from_service_account_file(
                self.iap_service_account_key_file,
                target_audience=self.iap_client_id,
            )
            credentials.refresh(Request())
            return credentials.token
        except Exception as e:
            raise ValueError(f"Error generating IAP JWT token: {str(e)}")

    async def _make_iap_request(self, url: str, data: Dict[str, str]) -> Dict[Any, Any]:
        """
        Make an authenticated POST request to an IAP-protected endpoint.

        Args:
            url: The URL to request
            data: Form data to send in the request body

        Returns:
            JSON response as dictionary

        Raises:
            ValueError: If the request fails
        """
        try:
            token = self._get_iap_jwt()
            headers = {"Authorization": f"Bearer {token}"}

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientResponseError as e:
            raise ValueError(f"IAP API error: {e.status} - {e.message}")
        except Exception as e:
            raise ValueError(f"Error making IAP request: {str(e)}")

    async def verify_token(self, access_token: str) -> Dict[Any, Any]:
        """
        Verify access token via the Botrun backend API.

        Uses IAP authentication if IAP_CLIENT_ID and IAP_SERVICE_ACCOUNT_KEY_FILE
        environment variables are set, otherwise falls back to standard authentication.

        Args:
            access_token: The access token to verify

        Returns:
            Dictionary containing verification result:
            {
                "is_success": true,
                "username": "user@example.com"
            }

        Raises:
            ValueError: If the API call fails or token is invalid
        """
        self.logger.info(
            f"verify_token called with token length: {len(access_token) if access_token else 0}"
        )

        if os.getenv("BOTRUN_BACK_API_BASE", "") == "":
            self.logger.info(
                "BOTRUN_BACK_API_BASE is not set, return default verification"
            )
            return {
                "is_success": False,
                "message": "Token verification service not configured",
            }

        url = f"{self.api_base}/botrun/token_verify"
        data = {"access_token": access_token}
        self.logger.info(f"Token verify URL: {url}")

        # Use IAP authentication if both required environment variables are set
        if self.iap_client_id and self.iap_service_account_key_file:
            self.logger.info("IAP authentication is used")
            return await self._make_iap_request(url, data)

        # Otherwise, use standard authentication
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, data=data) as response:
                    response.raise_for_status()
                    self.logger.info(
                        f"Token verification response status: {response.status}"
                    )
                    text = await response.text()
                    self.logger.info(f"Token verification response: {text}")
                    return json.loads(text)
            except aiohttp.ClientResponseError as e:
                self.logger.error(
                    f"API error: {e.status} - {e.message}",
                    error=str(e),
                    exc_info=True,
                )
                if e.status == 401:
                    raise ValueError(f"Invalid access token")
                elif e.status == 400:
                    raise ValueError(f"Bad request: missing or invalid token format")
                else:
                    raise ValueError(f"API error: {e.status} - {e.message}")
            except Exception as e:
                self.logger.error(
                    f"Error verifying token: {str(e)}",
                    error=str(e),
                    exc_info=True,
                )
                raise ValueError(f"Error verifying token: {str(e)}")
