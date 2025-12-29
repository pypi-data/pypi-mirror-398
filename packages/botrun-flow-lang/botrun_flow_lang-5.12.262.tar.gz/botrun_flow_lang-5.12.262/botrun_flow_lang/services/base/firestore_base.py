from typing import Union
import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from google.cloud import firestore

load_dotenv()


class FirestoreBase:
    def __init__(self, collection_name: str):
        google_service_account_key_path = os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS_FOR_FASTAPI",
            "/app/keys/scoop-386004-d22d99a7afd9.json",
        )
        credentials = service_account.Credentials.from_service_account_file(
            google_service_account_key_path,
            scopes=["https://www.googleapis.com/auth/datastore"],
        )

        # 直接从环境变量获取项目 ID
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

        # 创建 Firestore 客户端，指定项目 ID（如果环境变量中有设置）
        if project_id:
            self.db = firestore.Client(project=project_id, credentials=credentials)
        else:
            self.db = firestore.Client(credentials=credentials)

        self.collection = self.db.collection(collection_name)
