import unittest
import requests
import json
import time
import uuid


class TestHatchSharing(unittest.TestCase):
    """Test class for Hatch sharing functionality tests"""

    def setUp(self):
        """Setup method that runs before each test"""
        # Default base URL, can be overridden by setting the class attribute
        if not hasattr(self, "base_url"):
            self.base_url = "http://localhost:8080"

        # Common headers
        self.headers = {"Content-Type": "application/json"}

        # Test data - create unique IDs for each test run
        self.owner_id = f"owner_{uuid.uuid4().hex[:8]}@example.com"
        self.shared_user_id = f"shared_{uuid.uuid4().hex[:8]}@example.com"
        self.hatch_id = f"test_hatch_{uuid.uuid4().hex[:8]}"

        # Create a test hatch for the owner
        self.create_test_hatch()

    def tearDown(self):
        """Cleanup method that runs after each test"""
        # Delete the test hatch
        self.delete_test_hatch()

    def create_test_hatch(self):
        """Helper method to create a test hatch"""
        url = f"{self.base_url}/api/hatch"
        payload = {
            "user_id": self.owner_id,
            "id": self.hatch_id,
            "model_name": "test-model",
            "prompt_template": "This is a test prompt template for sharing functionality testing",
            "name": "Test Hatch for Sharing Tests",
        }

        response = requests.post(url, headers=self.headers, json=payload)
        self.assertEqual(
            response.status_code, 200, f"Failed to create test hatch: {response.text}"
        )
        print(f"Created test hatch with ID: {self.hatch_id} for owner: {self.owner_id}")
        return response.json()

    def delete_test_hatch(self):
        """Helper method to delete the test hatch"""
        url = f"{self.base_url}/api/hatch/{self.hatch_id}"
        response = requests.delete(url, headers=self.headers)
        self.assertEqual(
            response.status_code, 200, f"Failed to delete test hatch: {response.text}"
        )
        print(f"Deleted test hatch with ID: {self.hatch_id}")

    def test_share_hatch_workflow(self):
        """Test the complete hatch sharing workflow:
        1. Share a hatch with another user
        2. Verify the hatch is shared
        3. Unshare the hatch
        4. Verify the hatch is no longer shared
        """
        # 1. Share the hatch
        self.share_hatch_with_user()

        # 2. Verify the hatch is shared
        shared_hatches = self.get_shared_hatches()
        self.assertEqual(len(shared_hatches), 1, "Expected exactly one shared hatch")
        self.assertEqual(
            shared_hatches[0]["id"], self.hatch_id, "Shared hatch ID doesn't match"
        )

        # 3. Unshare the hatch
        self.unshare_hatch_from_user()

        # 4. Verify the hatch is no longer shared
        shared_hatches = self.get_shared_hatches()
        self.assertEqual(
            len(shared_hatches), 0, "Expected no shared hatches after unsharing"
        )

    def test_is_hatch_shared_with_user(self):
        """Test checking if a hatch is shared with a specific user"""
        # Initially the hatch should not be shared
        result = self.check_is_hatch_shared_with_user()
        self.assertFalse(result["is_shared"], "Hatch should not be shared initially")

        # Share the hatch
        self.share_hatch_with_user()

        # Verify the hatch is now shared
        result = self.check_is_hatch_shared_with_user()
        self.assertTrue(result["is_shared"], "Hatch should be shared after sharing")

        # Unshare the hatch
        self.unshare_hatch_from_user()

        # Verify the hatch is no longer shared
        result = self.check_is_hatch_shared_with_user()
        self.assertFalse(
            result["is_shared"], "Hatch should not be shared after unsharing"
        )

    def check_is_hatch_shared_with_user(self):
        """Helper method to check if a hatch is shared with a user"""
        url = f"{self.base_url}/api/hatch/{self.hatch_id}/share/{self.shared_user_id}"

        response = requests.get(url, headers=self.headers)
        self.assertEqual(
            response.status_code,
            200,
            f"Failed to check if hatch is shared: {response.text}",
        )
        return response.json()

    def share_hatch_with_user(self):
        """Helper method to share a hatch with another user"""
        url = f"{self.base_url}/api/hatch/{self.hatch_id}/share"
        payload = {"user_id": self.shared_user_id}

        response = requests.post(url, headers=self.headers, json=payload)
        self.assertEqual(
            response.status_code, 200, f"Failed to share hatch: {response.text}"
        )
        result = response.json()
        self.assertTrue(
            result["success"], f"Share operation failed: {result.get('message', '')}"
        )
        print(f"Shared hatch {self.hatch_id} with user {self.shared_user_id}")
        return result

    def unshare_hatch_from_user(self):
        """Helper method to unshare a hatch from a user"""
        url = f"{self.base_url}/api/hatch/{self.hatch_id}/share/{self.shared_user_id}"

        response = requests.delete(url, headers=self.headers)
        self.assertEqual(
            response.status_code, 200, f"Failed to unshare hatch: {response.text}"
        )
        result = response.json()
        self.assertTrue(
            result["success"], f"Unshare operation failed: {result.get('message', '')}"
        )
        print(f"Unshared hatch {self.hatch_id} from user {self.shared_user_id}")
        return result

    def get_shared_hatches(self):
        """Helper method to get all hatches shared with a user"""
        url = f"{self.base_url}/api/hatches/shared?user_id={self.shared_user_id}"

        response = requests.get(url, headers=self.headers)
        self.assertEqual(
            response.status_code, 200, f"Failed to get shared hatches: {response.text}"
        )
        return response.json()

    def test_share_nonexistent_hatch(self):
        """Test sharing a non-existent hatch"""
        url = f"{self.base_url}/api/hatch/nonexistent-hatch-id/share"
        payload = {"user_id": self.shared_user_id}

        response = requests.post(url, headers=self.headers, json=payload)
        self.assertEqual(
            response.status_code, 404, "Expected 404 for non-existent hatch"
        )

    def test_unshare_nonexistent_hatch(self):
        """Test unsharing a non-existent hatch"""
        url = f"{self.base_url}/api/hatch/nonexistent-hatch-id/share/{self.shared_user_id}"

        response = requests.delete(url, headers=self.headers)
        self.assertEqual(
            response.status_code, 404, "Expected 404 for non-existent hatch"
        )

    def test_share_hatch_multiple_times(self):
        """Test sharing a hatch with the same user multiple times"""
        # First share
        self.share_hatch_with_user()

        # Second share (should be idempotent)
        result = self.share_hatch_with_user()
        self.assertTrue(result["success"], "Second share operation should succeed")

        # Verify only one share exists
        shared_hatches = self.get_shared_hatches()
        self.assertEqual(len(shared_hatches), 1, "Expected exactly one shared hatch")

        # Cleanup
        self.unshare_hatch_from_user()

    def test_share_with_multiple_users(self):
        """Test sharing a hatch with multiple users"""
        # Create another user ID
        second_user_id = f"user2_{uuid.uuid4().hex[:8]}@example.com"

        # Share with first user
        self.share_hatch_with_user()

        # Share with second user
        url = f"{self.base_url}/api/hatch/{self.hatch_id}/share"
        payload = {"user_id": second_user_id}

        response = requests.post(url, headers=self.headers, json=payload)
        self.assertEqual(
            response.status_code,
            200,
            f"Failed to share hatch with second user: {response.text}",
        )

        # Verify first user's shared hatches
        shared_hatches_1 = self.get_shared_hatches()
        self.assertEqual(
            len(shared_hatches_1), 1, "Expected exactly one shared hatch for first user"
        )

        # Verify second user's shared hatches
        url = f"{self.base_url}/api/hatches/shared?user_id={second_user_id}"
        response = requests.get(url, headers=self.headers)
        self.assertEqual(
            response.status_code,
            200,
            f"Failed to get shared hatches for second user: {response.text}",
        )
        shared_hatches_2 = response.json()
        self.assertEqual(
            len(shared_hatches_2),
            1,
            "Expected exactly one shared hatch for second user",
        )

        # Cleanup
        self.unshare_hatch_from_user()
        url = f"{self.base_url}/api/hatch/{self.hatch_id}/share/{second_user_id}"
        requests.delete(url, headers=self.headers)

    def test_manual_curl_commands(self):
        """Test the API using the same curl commands provided for manual testing"""
        # These tests follow the same pattern as the curl commands but programmatically

        # Create a new hatch with curl-like parameters
        curl_hatch_id = "123abc"
        url = f"{self.base_url}/api/hatch"
        payload = {
            "user_id": "sebastian.hsu@gmail.com",
            "id": curl_hatch_id,
            "prompt_template": "妳是臺灣人，回答要用臺灣繁體中文正式用語，需要的時候也可以用英文，可以親切、俏皮、幽默，但不能隨便輕浮。在使用者合理的要求下請盡量配合他的需求，不要隨便拒絕",
        }

        create_response = requests.post(url, headers=self.headers, json=payload)
        self.assertEqual(
            create_response.status_code,
            200,
            f"Failed to create curl test hatch: {create_response.text}",
        )

        # Get the hatch
        url = f"{self.base_url}/api/hatch/{curl_hatch_id}"
        get_response = requests.get(url, headers=self.headers)
        self.assertEqual(
            get_response.status_code,
            200,
            f"Failed to get curl test hatch: {get_response.text}",
        )
        self.assertEqual(
            get_response.json()["id"], curl_hatch_id, "Retrieved hatch ID doesn't match"
        )

        # Update the hatch
        url = f"{self.base_url}/api/hatch/{curl_hatch_id}"
        update_payload = {
            "user_id": "sebastian.hsu@gmail.com",
            "id": curl_hatch_id,
            "prompt_template": "You are a helpful agent",
        }

        update_response = requests.put(url, headers=self.headers, json=update_payload)
        self.assertEqual(
            update_response.status_code,
            200,
            f"Failed to update curl test hatch: {update_response.text}",
        )
        self.assertEqual(
            update_response.json()["prompt_template"],
            "You are a helpful agent",
            "Prompt template not updated",
        )

        # Share the hatch with another user
        url = f"{self.base_url}/api/hatch/{curl_hatch_id}/share"
        share_payload = {"user_id": self.shared_user_id}

        share_response = requests.post(url, headers=self.headers, json=share_payload)
        self.assertEqual(
            share_response.status_code,
            200,
            f"Failed to share curl test hatch: {share_response.text}",
        )

        # Get shared hatches
        url = f"{self.base_url}/api/hatches/shared?user_id={self.shared_user_id}"
        shared_response = requests.get(url, headers=self.headers)
        self.assertEqual(
            shared_response.status_code,
            200,
            f"Failed to get shared hatches: {shared_response.text}",
        )

        # Unshare the hatch
        url = f"{self.base_url}/api/hatch/{curl_hatch_id}/share/{self.shared_user_id}"
        unshare_response = requests.delete(url, headers=self.headers)
        self.assertEqual(
            unshare_response.status_code,
            200,
            f"Failed to unshare curl test hatch: {unshare_response.text}",
        )

        # Delete the hatch
        url = f"{self.base_url}/api/hatch/{curl_hatch_id}"
        delete_response = requests.delete(url, headers=self.headers)
        self.assertEqual(
            delete_response.status_code,
            200,
            f"Failed to delete curl test hatch: {delete_response.text}",
        )


if __name__ == "__main__":
    unittest.main()
