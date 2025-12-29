from fastapi import APIRouter, HTTPException, Depends
from botrun_hatch.models.user_setting import UserSetting
from botrun_flow_lang.services.user_setting.user_setting_factory import (
    user_setting_store_factory,
)
from botrun_flow_lang.services.user_setting.user_setting_fs_store import (
    UserSettingFsStore,
)

router = APIRouter()


async def get_user_setting_store():
    return user_setting_store_factory()


@router.post("/user_setting", response_model=UserSetting)
async def create_user_setting(
    user_setting: UserSetting,
    store: UserSettingFsStore = Depends(get_user_setting_store),
):
    success, created_setting = await store.set_user_setting(user_setting)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create user setting")
    return created_setting


@router.put("/user_setting/{user_id}", response_model=UserSetting)
async def update_user_setting(
    user_id: str,
    user_setting: UserSetting,
    store: UserSettingFsStore = Depends(get_user_setting_store),
):
    existing_setting = await store.get_user_setting(user_id)
    if not existing_setting:
        raise HTTPException(status_code=404, detail="User setting not found")
    user_setting.user_id = user_id
    success, updated_setting = await store.set_user_setting(user_setting)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update user setting")
    return updated_setting


@router.delete("/user_setting/{user_id}")
async def delete_user_setting(
    user_id: str, store: UserSettingFsStore = Depends(get_user_setting_store)
):
    success = await store.delete_user_setting(user_id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": f"Failed to delete user setting for user {user_id}",
            },
        )
    return {
        "success": True,
        "message": f"User setting for user {user_id} deleted successfully",
    }


@router.get("/user_setting/{user_id}", response_model=UserSetting)
async def get_user_setting(
    user_id: str, store: UserSettingFsStore = Depends(get_user_setting_store)
):
    user_setting = await store.get_user_setting(user_id)
    if not user_setting:
        raise HTTPException(status_code=404, detail="User setting not found")
    return user_setting
