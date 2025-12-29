from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from botrun_flow_lang.utils.clients.rate_limit_client import RateLimitClient

router = APIRouter(prefix="/rate_limit")


@router.get("/{username}")
async def get_user_rate_limit(username: str) -> Dict[Any, Any]:
    """
    獲取指定用戶的 rate limit 信息。

    Args:
        username: 用戶名

    Returns:
        包含用戶 rate limit 信息的字典

    Raises:
        HTTPException: 當用戶不存在或後端 API 無法訪問時
    """
    try:
        client = RateLimitClient()
        result = await client.get_rate_limit(username)
        return result
    except ValueError as e:
        # 使用者不存在時會回傳 404
        if "User not found" in str(e):
            raise HTTPException(status_code=404, detail=f"User not found: {username}")
        # 其他錯誤回傳 500
        raise HTTPException(status_code=500, detail=str(e))
