import logging
from typing import Union, List, Tuple
from datetime import datetime, timezone
from google.cloud.exceptions import GoogleCloudError
from botrun_flow_lang.constants import HATCH_SHARING_STORE_NAME, HATCH_STORE_NAME
from botrun_flow_lang.services.base.firestore_base import FirestoreBase
from botrun_hatch.models.hatch import Hatch
from botrun_hatch.models.hatch_sharing import HatchSharing
from google.cloud import firestore


class HatchFsStore(FirestoreBase):
    def __init__(self, env_name: str):
        super().__init__(f"{env_name}-{HATCH_STORE_NAME}")
        self.sharing_collection = self.db.collection(
            f"{env_name}-{HATCH_SHARING_STORE_NAME}"
        )

    async def get_hatch(self, item_id: str) -> Union[Hatch, None]:
        doc_ref = self.collection.document(item_id)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            return Hatch(**data)
        else:
            print(f">============Getting hatch {item_id} not exists")
            return None

    async def set_hatch(self, item: Hatch):
        try:
            # Update updated_at timestamp with current UTC time
            item.updated_at = datetime.now(timezone.utc).isoformat()

            # Proceed with saving the hatch
            doc_ref = self.collection.document(str(item.id))
            doc_ref.set(item.model_dump())
            return True, item

        except GoogleCloudError as e:
            logging.error(f"Error setting hatch {item.id}: {e}")
            return False, None
        except Exception as e:
            logging.error(f"Unexpected error setting hatch {item.id}: {e}")
            return False, None

    async def delete_hatch(self, item_id: str):
        try:
            doc_ref = self.collection.document(item_id)
            doc_ref.delete()
            return True
        except GoogleCloudError as e:
            print(f"Error deleting hatch {item_id}: {e}")
            return False

    async def get_hatches(
        self,
        user_id: str,
        offset: int = 0,
        limit: int = 20,
        sort_by: str = "updated_at",
        order: str = "desc",
    ) -> Tuple[List[Hatch], str]:
        try:
            # Build base query
            query = self.collection.where(
                filter=firestore.FieldFilter("user_id", "==", user_id)
            )

            # Add sorting
            # Firestore direction: DESCENDING or ASCENDING
            direction = (
                firestore.Query.DESCENDING if order == "desc" else firestore.Query.ASCENDING
            )
            query = query.order_by(sort_by, direction=direction)

            # Add pagination
            query = query.offset(offset).limit(limit)

            docs = query.stream()
            hatches = [Hatch(**doc.to_dict()) for doc in docs]
            return hatches, ""
        except GoogleCloudError as e:
            import traceback

            traceback.print_exc()
            print(f"Error getting hatches for user {user_id}: {e}")
            return [], f"Error getting hatches for user {user_id}: {e}"
        except Exception as e:
            import traceback

            traceback.print_exc()
            print(f"Error getting hatches for user {user_id}: {e}")
            return [], f"Error getting hatches for user {user_id}: {e}"

    async def get_default_hatch(self, user_id: str) -> Union[Hatch, None]:
        try:
            query = (
                self.collection.where(
                    filter=firestore.FieldFilter("user_id", "==", user_id)
                )
                .where(filter=firestore.FieldFilter("is_default", "==", True))
                .limit(1)
            )
            docs = query.stream()
            for doc in docs:
                return Hatch(**doc.to_dict())
            return None
        except GoogleCloudError as e:
            print(f"Error getting default hatch for user {user_id}: {e}")
            return None

    async def set_default_hatch(self, user_id: str, hatch_id: str) -> Tuple[bool, str]:
        try:
            # 获取当前的默认 hatch
            current_default = await self.get_default_hatch(user_id)

            # 获取要设置为默认的 hatch
            new_default = await self.get_hatch(hatch_id)
            if not new_default or new_default.user_id != user_id:
                return (
                    False,
                    f"Hatch with id {hatch_id} not found or does not belong to user {user_id}",
                )

            # 更新当前默认 hatch（如果存在）
            if current_default and current_default.id != hatch_id:
                current_default.is_default = False
                success, _ = await self.set_hatch(current_default)
                if not success:
                    return (
                        False,
                        f"Failed to update current default hatch {current_default.id}",
                    )

            # 设置新的默认 hatch
            new_default.is_default = True
            success, _ = await self.set_hatch(new_default)
            if not success:
                return False, f"Failed to set hatch {hatch_id} as default"

            return (
                True,
                f"Successfully set hatch {hatch_id} as default for user {user_id}",
            )
        except Exception as e:
            print(f"Error setting default hatch: {e}")
            return False, f"An error occurred: {str(e)}"

    async def share_hatch(
        self, hatch_id: str, owner_id: str, target_user_id: str
    ) -> Tuple[bool, str]:
        """Share a hatch with another user.

        Args:
            hatch_id: The ID of the hatch to share
            owner_id: The ID of the user who owns the hatch
            target_user_id: The ID of the user to share the hatch with

        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Verify hatch exists and belongs to owner
            hatch = await self.get_hatch(hatch_id)
            if not hatch:
                return False, f"Hatch with id {hatch_id} not found"

            if hatch.user_id != owner_id:
                return (
                    False,
                    f"Hatch with id {hatch_id} does not belong to user {owner_id}",
                )

            # Check if sharing already exists
            query = (
                self.sharing_collection.where(
                    filter=firestore.FieldFilter("hatch_id", "==", hatch_id)
                )
                .where(
                    filter=firestore.FieldFilter("shared_with_id", "==", target_user_id)
                )
                .limit(1)
            )

            docs = list(query.stream())
            if docs:
                return (
                    True,
                    f"Hatch {hatch_id} is already shared with user {target_user_id}",
                )

            # Create sharing record
            sharing = HatchSharing(
                hatch_id=hatch_id, owner_id=owner_id, shared_with_id=target_user_id
            )

            # Store in Firestore
            doc_ref = self.sharing_collection.document()
            doc_ref.set(sharing.model_dump())

            return (
                True,
                f"Successfully shared hatch {hatch_id} with user {target_user_id}",
            )

        except Exception as e:
            import traceback

            traceback.print_exc()
            print(f"Error sharing hatch {hatch_id} with user {target_user_id}: {e}")
            return False, f"Error sharing hatch: {str(e)}"

    async def unshare_hatch(
        self, hatch_id: str, owner_id: str, target_user_id: str
    ) -> Tuple[bool, str]:
        """Remove sharing of a hatch with a user.

        Args:
            hatch_id: The ID of the hatch to unshare
            owner_id: The ID of the user who owns the hatch
            target_user_id: The ID of the user to remove sharing from

        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Verify hatch exists and belongs to owner
            hatch = await self.get_hatch(hatch_id)
            if not hatch:
                return False, f"Hatch with id {hatch_id} not found"

            if hatch.user_id != owner_id:
                return (
                    False,
                    f"Hatch with id {hatch_id} does not belong to user {owner_id}",
                )

            # Find sharing record
            query = self.sharing_collection.where(
                filter=firestore.FieldFilter("hatch_id", "==", hatch_id)
            ).where(
                filter=firestore.FieldFilter("shared_with_id", "==", target_user_id)
            )

            # Delete all matching sharing records
            deleted = False
            for doc in query.stream():
                doc.reference.delete()
                deleted = True

            if not deleted:
                return (
                    False,
                    f"Hatch {hatch_id} is not shared with user {target_user_id}",
                )

            return (
                True,
                f"Successfully unshared hatch {hatch_id} from user {target_user_id}",
            )

        except Exception as e:
            import traceback

            traceback.print_exc()
            print(f"Error unsharing hatch {hatch_id} from user {target_user_id}: {e}")
            return False, f"Error unsharing hatch: {str(e)}"

    async def get_shared_hatches(
        self, user_id: str, offset: int = 0, limit: int = 20
    ) -> Tuple[List[Hatch], str]:
        """Get all hatches shared with a user.

        Args:
            user_id: The ID of the user to get shared hatches for
            offset: Pagination offset
            limit: Maximum number of results to return

        Returns:
            Tuple[List[Hatch], str]: List of shared hatches and error message if any
        """
        try:
            # Find all sharing records for this user
            query = (
                self.sharing_collection.where(
                    filter=firestore.FieldFilter("shared_with_id", "==", user_id)
                )
                .limit(limit)
                .offset(offset)
            )

            # Get all sharing records
            sharing_docs = list(query.stream())

            # If no sharing records, return empty list
            if not sharing_docs:
                return [], ""

            # Get shared hatches
            shared_hatches = []
            for doc in sharing_docs:
                sharing_data = doc.to_dict()
                hatch_id = sharing_data.get("hatch_id")
                if hatch_id:
                    hatch = await self.get_hatch(hatch_id)
                    if hatch:
                        shared_hatches.append(hatch)

            return shared_hatches, ""

        except Exception as e:
            import traceback

            traceback.print_exc()
            print(f"Error getting shared hatches for user {user_id}: {e}")
            return [], f"Error getting shared hatches: {str(e)}"

    async def is_hatch_shared_with_user(
        self, hatch_id: str, user_id: str
    ) -> Tuple[bool, str]:
        """Check if a hatch is shared with a specific user.

        Args:
            hatch_id: The ID of the hatch to check
            user_id: The ID of the user to check sharing with

        Returns:
            Tuple[bool, str]: Whether the hatch is shared with the user and a message
        """
        try:
            # Find sharing record for this hatch and user
            query = (
                self.sharing_collection.where(
                    filter=firestore.FieldFilter("hatch_id", "==", hatch_id)
                )
                .where(filter=firestore.FieldFilter("shared_with_id", "==", user_id))
                .limit(1)
            )

            # Check if any sharing records exist
            docs = list(query.stream())
            if docs:
                return True, f"Hatch {hatch_id} is shared with user {user_id}"
            else:
                return False, f"Hatch {hatch_id} is not shared with user {user_id}"

        except Exception as e:
            import traceback

            traceback.print_exc()
            print(
                f"Error checking if hatch {hatch_id} is shared with user {user_id}: {e}"
            )
            return False, f"Error checking sharing status: {str(e)}"

    async def delete_all_hatch_sharing(self, hatch_id: str) -> Tuple[bool, str]:
        """Delete all sharing records for a hatch.

        Args:
            hatch_id: The ID of the hatch to remove all sharing for

        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Find all sharing records for this hatch
            query = self.sharing_collection.where(
                filter=firestore.FieldFilter("hatch_id", "==", hatch_id)
            )

            # Delete all matching sharing records
            deleted_count = 0
            for doc in query.stream():
                doc.reference.delete()
                deleted_count += 1

            return (
                True,
                f"Successfully deleted {deleted_count} sharing records for hatch {hatch_id}",
            )

        except Exception as e:
            import traceback

            traceback.print_exc()
            print(f"Error deleting sharing records for hatch {hatch_id}: {e}")
            return False, f"Error deleting sharing records: {str(e)}"
