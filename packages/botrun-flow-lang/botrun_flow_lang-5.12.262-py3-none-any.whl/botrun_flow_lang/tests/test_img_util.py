import unittest
from pathlib import Path
import os
from botrun_flow_lang.langgraph_agents.agents.util.img_util import get_img_content_type


class TestImgUtil(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.current_dir = Path(__file__).parent
        self.test_files_dir = self.current_dir / "test_files"

    def test_get_content_type_png_1(self):
        """Test get_content_type with PNG file"""
        img_path = self.test_files_dir / "ImportedPhoto.760363950.029251.jpeg"
        content_type = get_img_content_type(img_path)
        self.assertEqual(content_type, "image/png")

    def test_get_content_type_png_2(self):
        """Test get_content_type with PNG file"""
        img_path = self.test_files_dir / "spot_difference_1.png"
        content_type = get_img_content_type(img_path)
        self.assertEqual(content_type, "image/png")

    def test_get_content_type_jpeg_1(self):
        """Test get_content_type with PNG file"""
        img_path = self.test_files_dir / "ImportedPhoto.760363950.030446.jpeg"
        content_type = get_img_content_type(img_path)
        self.assertEqual(content_type, "image/jpeg")

    def test_get_content_type_jpeg_2(self):
        """Test get_content_type with PNG file"""
        img_path = self.test_files_dir / "d5712343.jpg"
        content_type = get_img_content_type(img_path)
        self.assertEqual(content_type, "image/jpeg")


if __name__ == "__main__":
    unittest.main()
