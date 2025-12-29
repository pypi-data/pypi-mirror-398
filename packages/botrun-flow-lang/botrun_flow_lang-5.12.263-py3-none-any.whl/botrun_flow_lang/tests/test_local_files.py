import unittest
import asyncio
import os
from pathlib import Path
from botrun_flow_lang.langgraph_agents.agents.util.local_files import (
    generate_tmp_text_file,
    read_tmp_text_file,
)


class TestLocalFiles(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        # Test configuration
        self.test_text_content = (
            "This is a test text file content.\n\nLine 2\nLine 3\n測試中文內容"
        )
        self.user_id = "sebastian.hsu@gmail.com"

    def test_generate_tmp_text_file(self):
        """Test generate_tmp_text_file function"""
        # Run the async function
        result = asyncio.run(
            generate_tmp_text_file(self.test_text_content, self.user_id)
        )

        # Print the result for manual verification
        print("\nTest Result:")
        print(f"Generated storage path: {result}")

        # Basic validation
        if result.startswith("Error:"):
            print(f"Test failed with error: {result}")
            self.fail(f"Test failed with error: {result}")
        else:
            print("Test successful - storage path generated")
            # Validate storage path format
            expected_path_prefix = f"tmp/{self.user_id}/"
            self.assertTrue(
                result.startswith(expected_path_prefix),
                f"Expected storage path to start with '{expected_path_prefix}', got: {result}",
            )
            
            # Verify content by reading back the file
            read_content = asyncio.run(read_tmp_text_file(result))
            if read_content.startswith("Error:"):
                self.fail(f"Failed to read back content: {read_content}")
            else:
                self.assertEqual(
                    read_content, 
                    self.test_text_content, 
                    "Read content doesn't match original content"
                )
                print("Content verification successful - read content matches original")

    def test_generate_tmp_text_file_with_unicode(self):
        """Test generate_tmp_text_file function with unicode content"""
        unicode_content = "Unicode test: 你好世界 🌍 ñáéíóú âêîôû àèìòù"

        result = asyncio.run(
            generate_tmp_text_file(unicode_content, self.user_id)
        )

        print(f"\nUnicode Test Result: {result}")

        if result.startswith("Error:"):
            print(f"Unicode test failed: {result}")
            self.fail(f"Unicode test failed: {result}")
        else:
            print("Unicode test successful - storage path generated")
            
            # Verify content by reading back the file
            read_content = asyncio.run(read_tmp_text_file(result))
            if read_content.startswith("Error:"):
                self.fail(f"Failed to read back unicode content: {read_content}")
            else:
                self.assertEqual(
                    read_content, 
                    unicode_content, 
                    "Unicode read content doesn't match original content"
                )
                print("Unicode content verification successful - read content matches original")

    def test_generate_tmp_text_file_with_empty_content(self):
        """Test generate_tmp_text_file function with empty content"""
        empty_content = ""

        result = asyncio.run(
            generate_tmp_text_file(empty_content, self.user_id)
        )

        print(f"\nEmpty Content Test Result: {result}")

        if result.startswith("Error:"):
            print(f"Empty content test failed: {result}")
            self.fail(f"Empty content test failed: {result}")
        else:
            print("Empty content test successful - storage path generated")
            
            # Verify content by reading back the file
            read_content = asyncio.run(read_tmp_text_file(result))
            if read_content.startswith("Error:"):
                self.fail(f"Failed to read back empty content: {read_content}")
            else:
                self.assertEqual(
                    read_content, 
                    empty_content, 
                    "Empty read content doesn't match original content"
                )
                print("Empty content verification successful - read content matches original")


if __name__ == "__main__":
    unittest.main()
