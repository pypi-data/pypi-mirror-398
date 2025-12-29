import os
from fastapi import APIRouter, HTTPException
import aiohttp
from urllib.parse import urljoin
import json
from google.auth.transport.requests import Request
from google.oauth2 import service_account

router = APIRouter()

router = APIRouter(prefix="/botrun_back")


def normalize_url(base_url, path):
    f_base_url = base_url
    if not f_base_url.endswith("/"):
        f_base_url = f_base_url + "/"
    return urljoin(f_base_url, path)


@router.get("/info")
async def get_botrun_back_info():
    """Get information from the botrun backend service."""
    try:
        botrun_base_url = os.environ.get("BOTRUN_BACK_API_BASE")
        if not botrun_base_url:
            raise HTTPException(
                status_code=500, detail="BOTRUN_BACK_API_BASE not configured"
            )

        info_url = normalize_url(botrun_base_url, "botrun/info")
        iap_client_id = os.getenv("IAP_CLIENT_ID")
        iap_service_account_key_file = os.getenv("IAP_SERVICE_ACCOUNT_KEY_FILE")
        headers = {}
        if iap_client_id and iap_service_account_key_file:
            try:
                credentials = (
                    service_account.IDTokenCredentials.from_service_account_file(
                        iap_service_account_key_file,
                        target_audience=iap_client_id,
                    )
                )
                credentials.refresh(Request())
                token = credentials.token
                headers = {"Authorization": f"Bearer {token}"}
            except Exception as e:
                raise ValueError(f"Error generating IAP JWT token: {str(e)}")

        async with aiohttp.ClientSession() as session:
            async with session.get(info_url, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Error calling botrun backend: {error_text}",
                    )

                text = await response.text()
                return json.loads(text)
    except aiohttp.ClientError as e:
        raise HTTPException(
            status_code=500, detail=f"Error connecting to botrun backend: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
