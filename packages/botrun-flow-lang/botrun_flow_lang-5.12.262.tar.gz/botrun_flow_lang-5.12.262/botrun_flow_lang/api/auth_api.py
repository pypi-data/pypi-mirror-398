from fastapi import APIRouter, HTTPException, Form
from typing import Dict, Any

from botrun_flow_lang.utils.clients.token_verify_client import TokenVerifyClient

router = APIRouter(prefix="/auth")


@router.post("/token_verify")
async def verify_token(access_token: str = Form(...)) -> Dict[Any, Any]:
    """
    驗證 access token 的有效性。

    Args:
        access_token: 要驗證的 access token (from form data)

    Returns:
        包含驗證結果的字典:
        {
            "is_success": true,
            "username": "user@example.com"
        }

    Raises:
        HTTPException: 當 token 無效 (401) 或後端 API 無法訪問時 (500)
    """
    try:
        client = TokenVerifyClient()
        result = await client.verify_token(access_token)
        return result
    except ValueError as e:
        error_msg = str(e).lower()
        # Token 無效時回傳 401
        if "invalid" in error_msg and "token" in error_msg:
            raise HTTPException(status_code=401, detail="Invalid access token")
        # 請求格式錯誤時回傳 400  
        elif "bad request" in error_msg:
            raise HTTPException(status_code=400, detail="Bad request: missing or invalid token format")
        # 其他錯誤回傳 500
        raise HTTPException(status_code=500, detail=str(e))