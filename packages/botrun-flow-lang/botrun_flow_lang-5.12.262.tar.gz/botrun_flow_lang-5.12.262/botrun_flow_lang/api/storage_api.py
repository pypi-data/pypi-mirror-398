from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    UploadFile as FastAPIUploadFile,
    File,
    HTTPException,
    Form,
    Depends,
)
from typing import Optional
from io import BytesIO
import json

from botrun_hatch.models.upload_file import UploadFile
from botrun_flow_lang.services.storage.storage_factory import storage_store_factory
from fastapi.responses import StreamingResponse
from botrun_flow_lang.api.auth_utils import (
    verify_jwt_token,
    verify_user_permission,
    verify_admin_permission,
    CurrentUser,
)

router = APIRouter()
load_dotenv()


@router.post("/files/{user_id}")
async def upload_file(
    user_id: str,
    file: FastAPIUploadFile = File(...),
    file_info: str = Form(...),
    current_user: CurrentUser = Depends(verify_jwt_token),
) -> dict:
    """
    儲存檔案到 GCS
    """
    # Verify user permission
    verify_user_permission(current_user, user_id)

    try:
        # 解析 file_info JSON 字串
        file_info_dict = json.loads(file_info)
        file_info_obj = UploadFile(**file_info_dict)

        storage = storage_store_factory()

        # 讀取上傳的檔案內容
        contents = await file.read()
        file_object = BytesIO(contents)

        # 構建存儲路徑
        storage_path = f"{user_id}/{file_info_obj.id}"

        # 存儲檔案
        success = await storage.store_file(storage_path, file_object)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to store file")

        return {"message": "File uploaded successfully", "success": True}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for file_info")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{user_id}/{file_id}", response_class=StreamingResponse)
async def get_file(
    user_id: str, file_id: str, current_user: CurrentUser = Depends(verify_jwt_token)
):
    """
    從 GCS 取得檔案
    """
    # Verify user permission
    verify_user_permission(current_user, user_id)

    try:
        storage = storage_store_factory()
        storage_path = f"{user_id}/{file_id}"

        file_object = await storage.retrieve_file(storage_path)
        if not file_object:
            raise HTTPException(status_code=404, detail="File not found")

        return StreamingResponse(
            iter([file_object.getvalue()]), media_type="application/octet-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/files/{user_id}/{file_id}")
async def delete_file(
    user_id: str, file_id: str, current_user: CurrentUser = Depends(verify_jwt_token)
):
    """
    從 GCS 刪除檔案
    """
    # Verify user permission
    verify_user_permission(current_user, user_id)

    try:
        storage = storage_store_factory()
        storage_path = f"{user_id}/{file_id}"

        success = await storage.delete_file(storage_path)
        if not success:
            raise HTTPException(
                status_code=404, detail="File not found or could not be deleted"
            )

        return {"message": "File deleted successfully", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tmp-files/{user_id}")
async def upload_tmp_file(
    user_id: str,
    file: FastAPIUploadFile = File(...),
    file_name: str = Form(...),
    content_type: str = Form(None),
    # current_user: CurrentUser = Depends(verify_jwt_token),
) -> dict:
    """
    儲存暫存檔案到 GCS，檔案會是公開可存取且有 7 天的生命週期

    Args:
        user_id: 使用者 ID
        file: 上傳的檔案
        file_name: 檔案名稱
        content_type: 檔案的 MIME type，如果沒有提供則使用檔案的 content_type
    """
    # Verify user permission
    # verify_user_permission(current_user, user_id)

    try:
        storage = storage_store_factory()

        # 讀取上傳的檔案內容
        contents = await file.read()
        file_object = BytesIO(contents)

        # 如果沒有提供 content_type，使用檔案的 content_type
        if not content_type:
            content_type = file.content_type

        # 構建存儲路徑 - 使用 tmp 目錄來區分暫存檔案
        storage_path = f"tmp/{user_id}/{file_name}"

        # 存儲檔案，設定為公開存取，並傳入 content_type
        success, public_url = await storage.store_file(
            storage_path, file_object, public=True, content_type=content_type
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to store file")

        return {
            "message": "Temporary file uploaded successfully",
            "success": True,
            "url": public_url,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _upload_html_file_internal(
    user_id: str, file_content: bytes, file_name: str, content_type: str = "text/html"
) -> str:
    """
    Internal function to upload HTML file to GCS
    
    Args:
        user_id: User ID
        file_content: File content as bytes
        file_name: File name
        content_type: MIME type of the file
        
    Returns:
        str: Public URL of the uploaded file
        
    Raises:
        Exception: If upload fails
    """
    storage = storage_store_factory()

    # Create file object from bytes
    file_object = BytesIO(file_content)

    # Build storage path - use html directory
    storage_path = f"html/{user_id}/{file_name}"

    # Store file with public access and content type
    success, public_url = await storage.store_file(
        storage_path, file_object, public=True, content_type=content_type
    )

    if not success:
        raise Exception("Failed to store file")

    return public_url


async def _upload_img_file_internal(
    user_id: str, file_content: bytes, file_name: str, content_type: str = "image/png"
) -> str:
    """
    Internal function to upload image file to GCS

    Args:
        user_id: User ID
        file_content: File content as bytes
        file_name: File name
        content_type: MIME type of the file

    Returns:
        str: Public URL of the uploaded file

    Raises:
        Exception: If upload fails
    """
    storage = storage_store_factory()

    # Create file object from bytes
    file_object = BytesIO(file_content)

    # Build storage path - use img directory for permanent storage
    storage_path = f"img/{user_id}/{file_name}"

    # Store file with public access and content type
    success, public_url = await storage.store_file(
        storage_path, file_object, public=True, content_type=content_type
    )

    if not success:
        raise Exception("Failed to store image file")

    return public_url


@router.post("/html-files/{user_id}")
async def upload_html_file(
    user_id: str,
    file: FastAPIUploadFile = File(...),
    file_name: str = Form(...),
    content_type: str = Form(None),
    # current_user: CurrentUser = Depends(verify_jwt_token)
) -> dict:
    """
    儲存 HTML 檔案到 GCS，檔案會是公開可存取

    Args:
        user_id: 使用者 ID
        file: 上傳的檔案
        file_name: 檔案名稱
        content_type: 檔案的 MIME type，如果沒有提供則使用檔案的 content_type
    """
    # Verify user permission
    # verify_user_permission(current_user, user_id)

    try:
        # 讀取上傳的檔案內容
        contents = await file.read()

        # 如果沒有提供 content_type，使用檔案的 content_type
        if not content_type:
            content_type = file.content_type

        # Use internal function to upload file
        public_url = await _upload_html_file_internal(
            user_id, contents, file_name, content_type
        )

        return {
            "message": "HTML file uploaded successfully",
            "success": True,
            "url": public_url,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/img-files/{user_id}")
async def upload_img_file(
    user_id: str,
    file: FastAPIUploadFile = File(...),
    file_name: str = Form(...),
    content_type: str = Form(None),
    # current_user: CurrentUser = Depends(verify_jwt_token)
) -> dict:
    """
    儲存圖片檔案到 GCS，檔案會是公開可存取且永久保存

    Args:
        user_id: 使用者 ID
        file: 上傳的檔案
        file_name: 檔案名稱
        content_type: 檔案的 MIME type，如果沒有提供則使用檔案的 content_type
    """
    # Verify user permission
    # verify_user_permission(current_user, user_id)

    try:
        # 讀取上傳的檔案內容
        contents = await file.read()

        # 如果沒有提供 content_type，使用檔案的 content_type
        if not content_type:
            content_type = file.content_type

        # Use internal function to upload file
        public_url = await _upload_img_file_internal(
            user_id, contents, file_name, content_type
        )

        return {
            "message": "Image file uploaded successfully",
            "success": True,
            "url": public_url,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/directory-sizes")
async def get_directory_sizes(current_user: CurrentUser = Depends(verify_jwt_token)):
    """
    取得 GCS bucket 中每個目錄的總檔案大小與檔案數量，排除 tmp 目錄

    Returns:
        dict: 包含每個目錄資訊的字典，包括檔案大小(bytes和人類可讀版本)和檔案數量，
              並包含所有目錄的總大小和檔案總數加總在 "total" 鍵中
    """
    # Verify admin permission
    verify_admin_permission(current_user)

    try:
        storage = storage_store_factory()
        directory_info = await storage.get_directory_sizes()

        # 計算所有目錄的總大小和總檔案數量
        total_size_bytes = sum(info["size"] for info in directory_info.values())
        total_file_count = sum(info["file_count"] for info in directory_info.values())

        # 將結果轉換為更有用的格式，包含大小的人類可讀版本
        result = {}
        for directory, info in directory_info.items():
            size_bytes = info["size"]
            file_count = info["file_count"]

            # 轉換為適當的單位（KB, MB, GB）
            size_display = size_bytes
            unit = "bytes"

            if size_bytes >= 1024 * 1024 * 1024:
                size_display = round(size_bytes / (1024 * 1024 * 1024), 2)
                unit = "GB"
            elif size_bytes >= 1024 * 1024:
                size_display = round(size_bytes / (1024 * 1024), 2)
                unit = "MB"
            elif size_bytes >= 1024:
                size_display = round(size_bytes / 1024, 2)
                unit = "KB"

            result[directory] = {
                "size_bytes": size_bytes,
                "size_display": f"{size_display} {unit}",
                "file_count": file_count,
            }

        # 添加總大小的人類可讀版本
        total_display = total_size_bytes
        total_unit = "bytes"

        if total_size_bytes >= 1024 * 1024 * 1024:
            total_display = round(total_size_bytes / (1024 * 1024 * 1024), 2)
            total_unit = "GB"
        elif total_size_bytes >= 1024 * 1024:
            total_display = round(total_size_bytes / (1024 * 1024), 2)
            total_unit = "MB"
        elif total_size_bytes >= 1024:
            total_display = round(total_size_bytes / 1024, 2)
            total_unit = "KB"

        # 添加總大小和總檔案數到結果中
        result["total"] = {
            "size_bytes": total_size_bytes,
            "size_display": f"{total_display} {total_unit}",
            "file_count": total_file_count,
        }

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
