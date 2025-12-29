"""Utility functions for authentication shared across API modules."""

import os
import logging
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import TYPE_CHECKING

from botrun_flow_lang.utils.clients.token_verify_client import TokenVerifyClient

if TYPE_CHECKING:
    from botrun_flow_lang.services.hatch.hatch_fs_store import HatchFsStore

# Reusable HTTPBearer security scheme
security = HTTPBearer()


class CurrentUser(BaseModel):
    """Current authenticated user information."""
    user_id: str  # From botrun_back API's username field or admin for universal tokens
    is_admin: bool = False  # Universal token users are marked as admin

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify that the provided Bearer token is in the allowed JWT_TOKENS list.

    Args:
        credentials: Parsed `Authorization` header credentials supplied by FastAPI's
            dependency injection using `HTTPBearer`.

    Raises:
        HTTPException: If the token is missing or not present in the allowed list.
    """
    jwt_tokens_env = os.getenv("JWT_TOKENS", "")
    tokens = [t.strip() for t in jwt_tokens_env.split("\n") if t.strip()]
    if credentials.credentials not in tokens:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True


async def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> CurrentUser:
    """Verify JWT token using dual authentication mechanism.
    
    First checks if token is in JWT_TOKENS (universal tokens for testing),
    then calls botrun_back API for user authentication using TokenVerifyClient.
    
    Args:
        credentials: Parsed Authorization header credentials
        
    Returns:
        CurrentUser: Authenticated user information
        
    Raises:
        HTTPException: If authentication fails
    """
    # 1. Check universal tokens (existing logic)
    jwt_tokens_env = os.getenv("JWT_TOKENS", "")
    tokens = [t.strip() for t in jwt_tokens_env.split("\n") if t.strip()]
    
    if credentials.credentials in tokens:
        return CurrentUser(user_id="admin", is_admin=True)
    
    # 2. Use TokenVerifyClient for authentication (with IAP support)
    try:
        client = TokenVerifyClient()
        result = await client.verify_token(credentials.credentials)
        
        if result.get('is_success', False):
            username = result.get('username', '')
            if username:
                return CurrentUser(user_id=username, is_admin=False)
            else:
                raise HTTPException(status_code=401, detail="Invalid response from auth service")
        else:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
            
    except ValueError as e:
        error_msg = str(e).lower()
        if "invalid" in error_msg and "token" in error_msg:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        elif "not configured" in error_msg:
            raise HTTPException(status_code=500, detail="Authentication service not configured")
        else:
            raise HTTPException(status_code=500, detail="Authentication service unavailable")
    except Exception as e:
        logging.error(f"Unexpected error during authentication: {e}")
        raise HTTPException(status_code=500, detail="Authentication error")


def verify_user_permission(current_user: CurrentUser, target_user_id: str):
    """Verify user has permission to access resources for the specified user_id.
    
    Args:
        current_user: Current authenticated user
        target_user_id: Target user ID to check permission for
        
    Raises:
        HTTPException: If user lacks permission
    """
    if current_user.is_admin:
        return  # Admin can access all resources
    
    if current_user.user_id != target_user_id:
        raise HTTPException(
            status_code=403, 
            detail="Insufficient permissions to access this resource"
        )


async def verify_hatch_owner(current_user: CurrentUser, hatch_id: str, store: "HatchFsStore"):
    """Verify user is the owner of the specified hatch.
    
    Args:
        current_user: Current authenticated user
        hatch_id: Hatch ID to check ownership for
        store: Hatch store instance
        
    Raises:
        HTTPException: If user is not the owner or hatch not found
    """
    if current_user.is_admin:
        return  # Admin can access all hatches
    
    hatch = await store.get_hatch(hatch_id)
    if not hatch:
        raise HTTPException(status_code=404, detail="Hatch not found")
    
    if hatch.user_id != current_user.user_id:
        raise HTTPException(
            status_code=403, 
            detail="Insufficient permissions to access this hatch"
        )


async def verify_hatch_access(current_user: CurrentUser, hatch_id: str, store: "HatchFsStore"):
    """Verify user can read the hatch (owner or shared with user).
    
    Args:
        current_user: Current authenticated user
        hatch_id: Hatch ID to check access for
        store: Hatch store instance
        
    Raises:
        HTTPException: If user lacks access or hatch not found
    """
    if current_user.is_admin:
        return  # Admin can access all hatches
    
    hatch = await store.get_hatch(hatch_id)
    if not hatch:
        raise HTTPException(status_code=404, detail="Hatch not found")
    
    # Check if user is owner
    if hatch.user_id == current_user.user_id:
        return
    
    # Check if hatch is shared with user
    is_shared, _ = await store.is_hatch_shared_with_user(hatch_id, current_user.user_id)
    if not is_shared:
        raise HTTPException(
            status_code=403, 
            detail="Insufficient permissions to access this hatch"
        )


def verify_admin_permission(current_user: CurrentUser):
    """Verify user has admin permissions.
    
    Args:
        current_user: Current authenticated user
        
    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403, 
            detail="Admin permissions required"
        )
