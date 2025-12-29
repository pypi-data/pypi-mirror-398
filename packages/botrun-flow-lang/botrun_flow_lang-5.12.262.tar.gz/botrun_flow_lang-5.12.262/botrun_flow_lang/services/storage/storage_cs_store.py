from google.cloud import storage
from google.cloud.exceptions import NotFound
from google.oauth2 import service_account
from io import BytesIO
import os
from typing import Optional, Tuple
from datetime import datetime, timedelta, UTC

from botrun_flow_lang.constants import HATCH_BUCKET_NAME
from botrun_flow_lang.services.storage.storage_store import StorageStore
from botrun_flow_lang.utils.botrun_logger import get_default_botrun_logger

logger = get_default_botrun_logger()


class StorageCsStore(StorageStore):
    def __init__(self, env_name: str):
        google_service_account_key_path = os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS_FOR_FASTAPI",
            "/app/keys/scoop-386004-d22d99a7afd9.json",
        )
        credentials = service_account.Credentials.from_service_account_file(
            google_service_account_key_path,
            scopes=["https://www.googleapis.com/auth/devstorage.full_control"],
        )

        self.storage_client = storage.Client(credentials=credentials)
        self.bucket_name = f"{HATCH_BUCKET_NAME}-{env_name}"
        self.bucket = self.create_bucket(self.bucket_name)
        if not self.bucket:
            raise Exception(f"Failed to create or get bucket: {self.bucket_name}")

    def create_bucket(self, bucket_name: str) -> Optional[storage.Bucket]:
        """創建新的 bucket，如果已存在則返回現有的，並確保 lifecycle rules 正確設定"""
        try:
            bucket = self.storage_client.bucket(bucket_name)

            desired_rules = [
                {
                    "action": {"type": "Delete"},
                    "condition": {"age": 365, "matchesPrefix": ["tmp/"]},
                },
                {
                    "action": {"type": "Delete"},
                    "condition": {"age": 7, "matchesPrefix": ["pdf-cache/"]},
                },
            ]

            if not bucket.exists():
                logger.info(f"Creating new bucket: {bucket_name}")
                # 設定 lifecycle rules
                bucket.lifecycle_rules = desired_rules
                # 創建 bucket
                bucket = self.storage_client.create_bucket(
                    bucket, location="asia-east1"
                )
                logger.info(
                    f"Created bucket {bucket_name} in asia-east1 and set lifecycle rules."
                )
            else:
                logger.info(
                    f"Bucket {bucket_name} already exists. Checking lifecycle rules."
                )
                bucket.reload()  # 獲取最新的 bucket metadata

                # google-cloud-storage 回傳的 rule 是 frozenset of dicts，需要轉換
                current_rules = [dict(rule) for rule in bucket.lifecycle_rules]

                if current_rules != desired_rules:
                    logger.info(f"Updating lifecycle rules for bucket {bucket_name}")
                    bucket.lifecycle_rules = desired_rules
                    bucket.patch()
                    logger.info(
                        f"Successfully updated lifecycle rules for bucket {bucket_name}"
                    )
                else:
                    logger.info(
                        f"Lifecycle rules for bucket {bucket_name} are already up-to-date."
                    )

            return bucket
        except Exception as e:
            logger.error(f"Error creating or updating bucket {bucket_name}: {str(e)}")
            return None

    async def get_directory_sizes(self) -> dict:
        """
        計算 bucket 中每個目錄的總檔案大小 (bytes) 與檔案數量，排除 tmp, html 目錄

        Returns:
            dict: 包含每個目錄資訊的字典，格式為 {directory_name: {"size": total_size_in_bytes, "file_count": count}}
        """
        try:
            # 初始化結果字典
            directory_info = {}

            # 列出所有 blobs
            blobs = list(self.bucket.list_blobs())

            # 計算每個目錄的大小和檔案數量
            for blob in blobs:
                # 跳過 tmp 目錄
                if blob.name.startswith("tmp/"):
                    continue
                # 跳過 html 目錄
                if blob.name.startswith("html/"):
                    continue

                # 從 blob 名稱中提取目錄名稱 (第一層目錄)
                parts = blob.name.split("/")
                if len(parts) >= 1:
                    directory = parts[0]

                    # 如果這是一個新目錄，初始化其資訊
                    if directory not in directory_info:
                        directory_info[directory] = {"size": 0, "file_count": 0}

                    # 加上此 blob 的大小
                    directory_info[directory]["size"] += blob.size
                    # 增加檔案計數
                    directory_info[directory]["file_count"] += 1

            return directory_info
        except Exception as e:
            logger.error(f"Error calculating directory sizes: {e}")
            return {}

    async def store_file(
        self,
        filepath: str,
        file_object: BytesIO,
        public: bool = False,
        content_type: str = None,
    ) -> Tuple[bool, Optional[str]]:
        try:
            blob = self.bucket.blob(filepath)

            # 設定 content_type 和其他 metadata
            if content_type:
                blob.content_type = content_type
                # 如果是圖片，設定為 inline 顯示並加入 cache control
                if content_type.startswith("image/"):
                    blob.content_disposition = (
                        'inline; filename="' + filepath.split("/")[-1] + '"'
                    )
                    blob.cache_control = "public, max-age=3600, no-transform"

            # 上傳檔案
            blob.upload_from_file(file_object, rewind=True)

            # 確保 metadata 更新
            blob.patch()

            # 如果需要公開存取
            if public:
                blob.make_public()
                return True, blob.public_url

            return True, None
        except Exception as e:
            logger.error(f"Error storing file in Cloud Storage: {e}")
            return False, None

    async def get_public_url(self, filepath: str) -> Optional[str]:
        try:
            blob = self.bucket.blob(filepath)
            if blob.exists():
                return blob.public_url
            return None
        except Exception as e:
            logger.error(f"Error getting public URL: {e}")
            return None

    async def retrieve_file(self, filepath: str) -> Optional[BytesIO]:
        try:
            blob = self.bucket.blob(filepath)
            file_object = BytesIO()
            blob.download_to_file(file_object)
            file_object.seek(0)  # Rewind the file object to the beginning
            return file_object
        except NotFound:
            logger.error(f"File not found in Cloud Storage: {filepath}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving file from Cloud Storage: {e}")
            return None

    async def delete_file(self, filepath: str) -> bool:
        try:
            blob = self.bucket.blob(filepath)
            blob.delete()
            return True
        except NotFound:
            logger.error(f"File not found in Cloud Storage: {filepath}")
            return False
        except Exception as e:
            logger.error(f"Error deleting file from Cloud Storage: {e}")
            return False

    async def file_exists(self, filepath: str) -> bool:
        try:
            blob = self.bucket.blob(filepath)
            return blob.exists()
        except Exception as e:
            logger.error(f"Error checking file existence in Cloud Storage: {e}")
            return False
