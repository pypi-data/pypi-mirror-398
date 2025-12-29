from abc import ABC, abstractmethod
from typing import Optional, Tuple
from io import BytesIO


class StorageStore(ABC):

    @abstractmethod
    async def store_file(
        self,
        filepath: str,
        file_object: BytesIO,
        public: bool = False,
        content_type: str = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Store a file in the storage.

        :param filepath: The path where the file should be stored
        :param file_object: The file object to be stored (BytesIO)
        :param public: Whether the file should be publicly accessible
        :param content_type: The MIME type of the file
        :return: Tuple of (success, public_url if public=True else None)
        """
        pass

    @abstractmethod
    async def get_public_url(self, filepath: str) -> Optional[str]:
        """
        Get the public URL for a file.

        :param filepath: The path of the file
        :return: Public URL if the file exists and is public, None otherwise
        """
        pass

    @abstractmethod
    async def retrieve_file(self, filepath: str) -> Optional[BytesIO]:
        """
        Retrieve a file from the storage.

        :param filepath: The path of the file to retrieve
        :return: BytesIO object containing the file data if found, None otherwise
        """
        pass

    @abstractmethod
    async def delete_file(self, filepath: str) -> bool:
        """
        Delete a file from the storage.

        :param filepath: The path of the file to delete
        :return: True if the file was successfully deleted, False otherwise
        """
        pass

    @abstractmethod
    async def file_exists(self, filepath: str) -> bool:
        """
        Check if a file exists in the storage.

        :param filepath: The path of the file to check
        :return: True if the file exists, False otherwise
        """
        pass
