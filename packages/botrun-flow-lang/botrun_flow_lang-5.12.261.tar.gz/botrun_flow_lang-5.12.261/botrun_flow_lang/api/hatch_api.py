from fastapi import APIRouter, HTTPException, Depends, Query, Body
import logging
from datetime import datetime, timezone

from botrun_flow_lang.api.auth_utils import (
    CurrentUser,
    verify_admin_permission,
    verify_hatch_access,
    verify_hatch_owner,
    verify_jwt_token,
    verify_user_permission,
)
from botrun_flow_lang.api.user_setting_api import get_user_setting_store

from botrun_flow_lang.services.hatch.hatch_factory import hatch_store_factory

from botrun_flow_lang.services.hatch.hatch_fs_store import HatchFsStore

from botrun_hatch.models.hatch import Hatch

from typing import List
from pydantic import BaseModel

from botrun_flow_lang.services.user_setting.user_setting_fs_store import (
    UserSettingFsStore,
)

from botrun_flow_lang.utils.google_drive_utils import fetch_google_doc_content

router = APIRouter()


class HatchResponse(BaseModel):
    hatch: Hatch
    gdoc_update_success: bool = False


async def get_hatch_store():
    return hatch_store_factory()


@router.post("/hatch", response_model=HatchResponse)
async def create_hatch(
    hatch: Hatch,
    current_user: CurrentUser = Depends(verify_jwt_token),
    store: HatchFsStore = Depends(get_hatch_store),
):
    # Verify user permission to create hatch for the specified user_id
    verify_user_permission(current_user, hatch.user_id)

    hatch.last_sync_gdoc_success = False
    # Process Google Doc logic if enabled
    if (
        hatch.enable_google_doc_link
        and hatch.google_doc_link
        and hatch.google_doc_link.strip()
    ):
        logging.info(
            f"Processing Google Doc link for hatch {hatch.id}: {hatch.google_doc_link}"
        )

        # Fetch content from Google Doc
        fetched_content = await fetch_google_doc_content(hatch.google_doc_link.strip())

        if fetched_content:
            # Update prompt_template with fetched content
            hatch.prompt_template = fetched_content
            # Update last_sync_gdoc_time with current UTC time
            hatch.last_sync_gdoc_time = datetime.now(timezone.utc).isoformat()
            hatch.last_sync_gdoc_success = True
            logging.info(
                f"Successfully updated prompt_template for hatch {hatch.id} from Google Doc"
            )
        else:
            # Log warning but continue with the operation
            logging.warning(
                f"Failed to fetch Google Doc content for hatch {hatch.id}, keeping existing prompt_template"
            )
    else:
        # If Google Doc link is disabled, clear last_sync_gdoc_time
        if not hatch.enable_google_doc_link:
            hatch.last_sync_gdoc_time = ""

    # Save to Firestore
    success, created_hatch = await store.set_hatch(hatch)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create hatch")

    return HatchResponse(
        hatch=created_hatch, gdoc_update_success=created_hatch.last_sync_gdoc_success
    )


@router.put("/hatch/{hatch_id}", response_model=HatchResponse)
async def update_hatch(
    hatch_id: str,
    hatch: Hatch,
    current_user: CurrentUser = Depends(verify_jwt_token),
    store: HatchFsStore = Depends(get_hatch_store),
):
    # Verify user is owner of the hatch
    await verify_hatch_owner(current_user, hatch_id, store)

    existing_hatch = await store.get_hatch(hatch_id)
    if not existing_hatch:
        raise HTTPException(status_code=404, detail="Hatch not found")

    hatch.id = hatch_id
    hatch.last_sync_gdoc_success = False

    # Process Google Doc logic if enabled
    if (
        hatch.enable_google_doc_link
        and hatch.google_doc_link
        and hatch.google_doc_link.strip()
    ):
        logging.info(
            f"Processing Google Doc link for hatch {hatch.id}: {hatch.google_doc_link}"
        )

        # Fetch content from Google Doc
        fetched_content = await fetch_google_doc_content(hatch.google_doc_link.strip())

        if fetched_content:
            # Update prompt_template with fetched content
            hatch.prompt_template = fetched_content
            # Update last_sync_gdoc_time with current UTC time
            hatch.last_sync_gdoc_time = datetime.now(timezone.utc).isoformat()
            hatch.last_sync_gdoc_success = True
            logging.info(
                f"Successfully updated prompt_template for hatch {hatch.id} from Google Doc"
            )
        else:
            # Log warning but continue with the operation
            # Keep existing last_sync_gdoc_time from the original hatch
            hatch.last_sync_gdoc_time = existing_hatch.last_sync_gdoc_time
            logging.warning(
                f"Failed to fetch Google Doc content for hatch {hatch.id}, keeping existing prompt_template and last_sync_gdoc_time"
            )
    else:
        # If Google Doc link is disabled, clear last_sync_gdoc_time
        if not hatch.enable_google_doc_link:
            hatch.last_sync_gdoc_time = ""

    # Save to Firestore
    success, updated_hatch = await store.set_hatch(hatch)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update hatch")

    return HatchResponse(
        hatch=updated_hatch, gdoc_update_success=updated_hatch.last_sync_gdoc_success
    )


@router.delete("/hatch/{hatch_id}")
async def delete_hatch(
    hatch_id: str,
    current_user: CurrentUser = Depends(verify_jwt_token),
    store: HatchFsStore = Depends(get_hatch_store),
):
    # Verify user is owner of the hatch
    await verify_hatch_owner(current_user, hatch_id, store)

    # Get the hatch to verify it exists
    hatch = await store.get_hatch(hatch_id)
    if not hatch:
        raise HTTPException(status_code=404, detail="Hatch not found")

    # Delete all sharing relationships for this hatch
    sharing_success, sharing_message = await store.delete_all_hatch_sharing(hatch_id)
    if not sharing_success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete hatch sharing relationships: {sharing_message}",
        )

    # Delete the hatch itself
    success = await store.delete_hatch(hatch_id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": f"Failed to delete hatch {hatch_id}"},
        )
    return {
        "success": True,
        "message": f"Hatch {hatch_id} and all sharing relationships deleted successfully",
    }


@router.get("/hatch/{hatch_id}", response_model=Hatch)
async def get_hatch(
    hatch_id: str,
    current_user: CurrentUser = Depends(verify_jwt_token),
    store: HatchFsStore = Depends(get_hatch_store),
):
    # Verify user has access to the hatch (owner or shared)
    await verify_hatch_access(current_user, hatch_id, store)

    hatch = await store.get_hatch(hatch_id)
    if not hatch:
        raise HTTPException(status_code=404, detail="Hatch not found")
    return hatch


@router.post("/hatch/{hatch_id}/reload-template")
async def reload_template_from_doc(
    hatch_id: str,
    current_user: CurrentUser = Depends(verify_jwt_token),
    store: HatchFsStore = Depends(get_hatch_store),
):
    """
    Reload prompt_template from linked Google Doc.

    This endpoint fetches the latest content from the Google Doc specified
    in the hatch's google_doc_link field and updates the prompt_template.

    Args:
        hatch_id: ID of the hatch to reload template for

    Returns:
        dict: Success status and message

    Raises:
        HTTPException:
            - 404 if hatch not found
            - 400 if Google Doc link feature is not enabled or no link configured
            - 500 if failed to fetch content or save hatch
    """
    try:
        # Verify user is owner of the hatch
        await verify_hatch_owner(current_user, hatch_id, store)

        # 1. Get the hatch
        hatch = await store.get_hatch(hatch_id)
        if not hatch:
            raise HTTPException(status_code=404, detail="Hatch not found")

        # 2. Check Google Doc configuration
        if not hatch.enable_google_doc_link:
            raise HTTPException(
                status_code=400,
                detail="Google Doc link feature is not enabled for this Hatch",
            )

        if not hatch.google_doc_link or not hatch.google_doc_link.strip():
            raise HTTPException(
                status_code=400, detail="No Google Doc link configured for this Hatch"
            )

        # 3. Fetch content from Google Doc
        fetched_content = await fetch_google_doc_content(hatch.google_doc_link.strip())

        if not fetched_content:
            raise HTTPException(
                status_code=500, detail="Failed to fetch content from Google Doc"
            )

        # 4. Update and save hatch
        hatch.prompt_template = fetched_content
        # Update last_sync_gdoc_time with current UTC time
        hatch.last_sync_gdoc_time = datetime.now(timezone.utc).isoformat()
        success, _ = await store.set_hatch(hatch)

        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to save Hatch after reloading template"
            )

        return {
            "success": True,
            "message": "Prompt template successfully reloaded from Google Doc",
        }

    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except Exception as e:
        logging.error(f"Error reloading prompt template for hatch {hatch_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"An error occurred while reloading: {str(e)}"
        )


@router.get("/hatches", response_model=List[Hatch])
async def get_hatches(
    user_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("updated_at", description="Field to sort by (name, updated_at)"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Sort order: asc or desc"),
    current_user: CurrentUser = Depends(verify_jwt_token),
    hatch_store=Depends(get_hatch_store),
):
    """Get hatches for a user with sorting options.

    Args:
        user_id: User ID to get hatches for
        offset: Pagination offset
        limit: Maximum number of results (1-100)
        sort_by: Field to sort by - only 'name' or 'updated_at' are supported (default: updated_at)
        order: Sort order - 'asc' or 'desc' (default: desc for newest first)

    Returns:
        List of hatches sorted by the specified field

    Raises:
        HTTPException: 400 if sort_by field is not supported
    """
    # Verify user permission to access hatches for the specified user_id
    verify_user_permission(current_user, user_id)

    # Validate sort_by field - only allow fields with Firestore indexes
    allowed_sort_fields = ["name", "updated_at"]
    if sort_by not in allowed_sort_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by field '{sort_by}'. Allowed fields: {', '.join(allowed_sort_fields)}",
        )

    hatches, error = await hatch_store.get_hatches(
        user_id, offset, limit, sort_by, order
    )
    if error:
        raise HTTPException(status_code=500, detail=error)
    return hatches


@router.get("/hatch/default/{user_id}", response_model=Hatch)
async def get_default_hatch(
    user_id: str,
    current_user: CurrentUser = Depends(verify_jwt_token),
    store: HatchFsStore = Depends(get_hatch_store),
):
    # Verify user permission to access default hatch for the specified user_id
    verify_user_permission(current_user, user_id)

    default_hatch = await store.get_default_hatch(user_id)
    if not default_hatch:
        raise HTTPException(status_code=404, detail="Default hatch not found")
    return default_hatch


@router.post("/hatch/set_default")
async def set_default_hatch(
    user_id: str = Body(...),
    hatch_id: str = Body(...),
    current_user: CurrentUser = Depends(verify_jwt_token),
    store: HatchFsStore = Depends(get_hatch_store),
):
    # Verify user permission to set default hatch for the specified user_id
    verify_user_permission(current_user, user_id)

    success, message = await store.set_default_hatch(user_id, hatch_id)
    if not success:
        raise HTTPException(status_code=500, detail=message)
    return {"success": True, "message": message}


@router.get("/hatches/statistics")
async def get_hatches_statistics(
    current_user: CurrentUser = Depends(verify_jwt_token),
    user_setting_store: UserSettingFsStore = Depends(get_user_setting_store),
    hatch_store: HatchFsStore = Depends(get_hatch_store),
):
    """Get statistics about hatches across all users.

    Returns:
        dict: Contains total hatch count and per-user hatch counts
    """
    # Verify admin permission
    verify_admin_permission(current_user)

    try:
        # Get all user IDs
        user_ids = await user_setting_store.get_all_user_ids()

        # Initialize statistics
        all_hatches = []
        total_count = 0

        # Get hatch counts for each user
        for user_id in user_ids:
            hatches, _ = await hatch_store.get_hatches(user_id)
            count = len(hatches)
            if count > 0:  # Only include users who have hatches
                all_hatches.append({"user_id": user_id, "hatches_count": count})
                total_count += count

        return {"all_hatches_count": total_count, "all_hatches": all_hatches}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch hatch statistics: {str(e)}"
        )


@router.post("/hatch/{hatch_id}/share")
async def share_hatch(
    hatch_id: str,
    user_id: str = Body(..., embed=True),
    store: HatchFsStore = Depends(get_hatch_store),
):
    """Share a hatch with another user.

    Args:
        hatch_id: ID of the hatch to share
        user_id: ID of the user to share the hatch with (in request body)

    Returns:
        dict: Success status and message
    """

    # Get the hatch to verify it exists and to get owner_id
    hatch = await store.get_hatch(hatch_id)
    if not hatch:
        raise HTTPException(status_code=404, detail="Hatch not found")

    # Share the hatch
    success, message = await store.share_hatch(hatch_id, hatch.user_id, user_id)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {"success": True, "message": message}


@router.delete("/hatch/{hatch_id}/share/{target_user_id}")
async def unshare_hatch(
    hatch_id: str,
    target_user_id: str,
    store: HatchFsStore = Depends(get_hatch_store),
):
    """Remove sharing of a hatch with a user.

    Args:
        hatch_id: ID of the hatch to unshare
        target_user_id: ID of the user to remove sharing from

    Returns:
        dict: Success status and message
    """

    # Get the hatch to verify it exists and to get owner_id
    hatch = await store.get_hatch(hatch_id)
    if not hatch:
        raise HTTPException(status_code=404, detail="Hatch not found")

    # Unshare the hatch
    success, message = await store.unshare_hatch(
        hatch_id, hatch.user_id, target_user_id
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {"success": True, "message": message}


@router.get("/hatches/shared", response_model=List[Hatch])
async def get_shared_hatches(
    user_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(verify_jwt_token),
    store: HatchFsStore = Depends(get_hatch_store),
):
    """Get all hatches shared with a user.

    Args:
        user_id: ID of the user to get shared hatches for
        offset: Pagination offset
        limit: Maximum number of results to return

    Returns:
        List[Hatch]: List of shared hatches
    """
    # Verify user permission to access shared hatches for the specified user_id
    verify_user_permission(current_user, user_id)

    hatches, error = await store.get_shared_hatches(user_id, offset, limit)
    if error:
        raise HTTPException(status_code=500, detail=error)

    return hatches


@router.get("/hatch/{hatch_id}/share/{user_id}")
async def is_hatch_shared_with_user(
    hatch_id: str,
    user_id: str,
    store: HatchFsStore = Depends(get_hatch_store),
):
    """Check if a hatch is shared with a specific user.

    Args:
        hatch_id: ID of the hatch to check
        user_id: ID of the user to check sharing with

    Returns:
        dict: Whether the hatch is shared with the user and a message
    """

    # Get the hatch to verify it exists
    hatch = await store.get_hatch(hatch_id)
    if not hatch:
        raise HTTPException(status_code=404, detail="Hatch not found")

    # Check if the hatch is shared with the user
    is_shared, message = await store.is_hatch_shared_with_user(hatch_id, user_id)

    return {"is_shared": is_shared, "message": message}
