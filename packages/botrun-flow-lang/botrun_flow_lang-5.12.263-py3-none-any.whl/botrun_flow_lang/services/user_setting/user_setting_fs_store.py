from typing import Union, List
from google.cloud.exceptions import GoogleCloudError
from botrun_flow_lang.constants import USER_SETTING_STORE_NAME
from botrun_hatch.models.user_setting import UserSetting
from botrun_flow_lang.services.base.firestore_base import FirestoreBase


class UserSettingFsStore(FirestoreBase):
    def __init__(self, env_name: str):
        super().__init__(f"{env_name}-{USER_SETTING_STORE_NAME}")

    async def get_user_setting(self, user_id: str) -> Union[UserSetting, None]:
        doc_ref = self.collection.document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            return UserSetting(**data)
        else:
            print(f">============Getting user setting for {user_id} not exists")
            return None

    async def set_user_setting(self, user_setting: UserSetting):
        try:
            doc_ref = self.collection.document(user_setting.user_id)
            doc_ref.set(user_setting.model_dump())
            return True, user_setting
        except GoogleCloudError as e:
            print(f"Error setting user setting for {user_setting.user_id}: {e}")
            return False, None

    async def delete_user_setting(self, user_id: str):
        try:
            doc_ref = self.collection.document(user_id)
            doc_ref.delete()
            return True
        except GoogleCloudError as e:
            print(f"Error deleting user setting for {user_id}: {e}")
            return False

    async def get_all_user_ids(self) -> List[str]:
        """Get all user IDs (document IDs) from the collection.

        Returns:
            List[str]: List of all user IDs
        """
        try:
            all_user_ids = []
            # Get first batch
            query = self.collection.limit(20)
            while True:
                docs = list(query.stream())
                if not docs:
                    break

                # Add document IDs from current batch
                all_user_ids.extend([doc.id for doc in docs])

                # Get last document from current batch
                last_doc = docs[-1]
                # Update query to start after the last document
                query = self.collection.limit(20).start_after(last_doc)

            return all_user_ids
        except GoogleCloudError as e:
            print(f"Error getting all user IDs: {e}")
            return []
