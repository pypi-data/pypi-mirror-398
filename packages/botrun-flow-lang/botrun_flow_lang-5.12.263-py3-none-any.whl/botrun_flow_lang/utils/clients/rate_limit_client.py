import os
import aiohttp
from typing import Dict, Any, Optional

# Import necessary libraries for IAP authentication
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import json


class RateLimitClient:
    """Client for interacting with Botrun rate limit API."""

    def __init__(self, api_base: Optional[str] = None):
        """
        Initialize the rate limit client.

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

    async def _make_iap_request(self, url: str, method: str = "GET") -> Dict[Any, Any]:
        """
        Make an authenticated request to an IAP-protected endpoint.

        Args:
            url: The URL to request
            method: HTTP method to use (default: GET)

        Returns:
            JSON response as dictionary

        Raises:
            ValueError: If the request fails
        """
        try:
            token = self._get_iap_jwt()
            headers = {"Authorization": f"Bearer {token}"}

            async with aiohttp.ClientSession() as session:
                if method.upper() == "GET":
                    async with session.get(url, headers=headers) as response:
                        response.raise_for_status()
                        return await response.json()
                elif method.upper() == "PUT":
                    async with session.put(url, headers=headers) as response:
                        response.raise_for_status()
                        return await response.json()
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
        except aiohttp.ClientResponseError as e:
            raise ValueError(f"IAP API error: {e.status} - {e.message}")
        except Exception as e:
            raise ValueError(f"Error making IAP request: {str(e)}")

    async def get_rate_limit(self, username: str) -> Dict[Any, Any]:
        """
        Get rate limit information for a user from the Botrun backend API.

        Uses IAP authentication if IAP_CLIENT_ID and IAP_SERVICE_ACCOUNT_KEY_FILE
        environment variables are set, otherwise falls back to standard authentication.

        Args:
            username: The username to get rate limit information for

        Returns:
            Dictionary containing rate limit information

        Raises:
            ValueError: If the API call fails
        """
        self.logger.info(f"get_rate_limit username: {username}")
        if os.getenv("BOTRUN_BACK_API_BASE", "") == "":
            self.logger.info(
                "BOTRUN_BACK_API_BASE is not set, return default rate limit"
            )
            return {
                "drawing": {"daily_limit": 999, "current_usage": 0, "can_use": True},
                "voice": {"max_size": 1024},
                "document": {"max_size": 1024},
            }
        url = f"{self.api_base}/botrun/rate_limit/{username}"
        self.logger.info(f"IAP URL: {url}")

        # Use IAP authentication if both required environment variables are set
        if self.iap_client_id and self.iap_service_account_key_file:
            self.logger.info("IAP authentication is used")
            return await self._make_iap_request(url)

        # Otherwise, use standard authentication
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    self.logger.info(
                        f"Rate limit data fetched successfully response:{response}"
                    )
                    text = await response.text()
                    self.logger.info(
                        f"Rate limit data fetched successfully text:{text}"
                    )
                    return json.loads(text)
            except aiohttp.ClientResponseError as e:
                self.logger.error(
                    f"API error: {e.status} - {e.message}",
                    error=str(e),
                    exc_info=True,
                )
                raise ValueError(f"API error: {e.status} - {e.message}")
            except Exception as e:
                self.logger.error(
                    f"Error fetching rate limit data: {str(e)}",
                    error=str(e),
                    exc_info=True,
                )
                raise ValueError(f"Error fetching rate limit data: {str(e)}")

    async def update_drawing_usage(self, username: str) -> Dict[Any, Any]:
        """
        Update drawing usage counter for a user via the Botrun backend API.

        Uses IAP authentication if IAP_CLIENT_ID and IAP_SERVICE_ACCOUNT_KEY_FILE
        environment variables are set, otherwise falls back to standard authentication.

        Args:
            username: The username to update drawing usage for

        Returns:
            Dictionary with update status information:
            {
                "username": "example@gmail.com",
                "is_success": true,
                "message": "Usage counter updated successfully"
            }

        Raises:
            ValueError: If the API call fails with status code 404 (user not found)
                       or 500 (server error)
        """
        self.logger.info(f"update_drawing_usage username: {username}")
        if os.getenv("BOTRUN_BACK_API_BASE", "") == "":
            self.logger.info("BOTRUN_BACK_API_BASE is not set, return ")
            return {}

        url = f"{self.api_base}/botrun/rate_limit/{username}/drawing_usage"
        self.logger.info(f"Update drawing usage URL: {url}")

        # Use IAP authentication if both required environment variables are set
        if self.iap_client_id and self.iap_service_account_key_file:
            self.logger.info("IAP authentication is used")
            return await self._make_iap_request(url, method="PUT")

        # Otherwise, use standard authentication
        async with aiohttp.ClientSession() as session:
            try:
                async with session.put(url) as response:
                    response.raise_for_status()
                    text = await response.text()
                    self.logger.info(f"Update drawing usage response: {text}")
                    return json.loads(text)
            except aiohttp.ClientResponseError as e:
                self.logger.error(
                    f"API error: {e.status} - {e.message}",
                    error=str(e),
                    exc_info=True,
                )
                if e.status == 404:
                    raise ValueError(f"User not found: {username}")
                else:
                    raise ValueError(f"API error: {e.status} - {e.message}")
            except Exception as e:
                self.logger.error(
                    f"Error updating drawing usage: {str(e)}",
                    error=str(e),
                    exc_info=True,
                )
                raise ValueError(f"Error updating drawing usage: {str(e)}")
