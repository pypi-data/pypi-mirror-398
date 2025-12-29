import unittest
import os
from pathlib import Path
from botrun_flow_lang.langgraph_agents.agents.util.local_files import (
    upload_and_get_tmp_public_url,
)
from botrun_flow_lang.langgraph_agents.agents.util.img_util import analyze_imgs


class TestImgAnalyzer(unittest.TestCase):
    def setUp(self):
        # Get the path to the test image file
        self.current_dir = Path(__file__).parent
        self.img_path = self.current_dir / "test_files" / "d5712343.jpg"

        # Ensure the test file exists
        self.assertTrue(
            os.path.exists(self.img_path), f"Test file not found at {self.img_path}"
        )

    def test_img_exists(self):
        """Test if the image file exists"""
        self.assertEqual(True, os.path.exists(self.img_path))

    def test_img_readable(self):
        """Test if the image file is readable"""
        self.assertEqual(True, os.access(self.img_path, os.R_OK))

    def test_img_not_empty(self):
        """Test if the image file is not empty"""
        self.assertEqual(True, os.path.getsize(self.img_path) > 0)

    def test_img_extension(self):
        """Test if the file has a JPG extension"""
        self.assertEqual(True, self.img_path.suffix.lower() in [".jpg", ".jpeg"])

    def test_analyze_1_image_content(self):
        """Test analyzing the content of the image"""
        query = "請描述這張圖片的內容，並列出主要可見的物件或人物，請使用繁體中文，臺灣用語進行回答。"
        img_url = upload_and_get_tmp_public_url(
            self.img_path,
            "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
            "sebastian.hsu@gmail.com",
        )
        result = analyze_imgs([img_url], query)  # Pass URL in a list

        # Print the result for inspection
        print("\ntest_analyze_1_image_content:")
        print("-" * 50)
        print(result)
        print("-" * 50)

        # 確保結果不為空
        self.assertIsNotNone(result)
        self.assertNotEqual("", result)

        # 確保結果不是錯誤訊息
        self.assertFalse(result.startswith("Error:"))

        # 確保回應內容包含描述性文字
        self.assertTrue(len(result) > 50)  # 確保回應有足夠的長度
        self.assertIn("佛教", result, "找不到回應中包含佛教，回應內容：" + result)

    def test_analyze_2_images_content(self):
        """Test analyzing the content of the image"""
        img1_path = self.current_dir / "test_files" / "spot_difference_1.png"
        img2_path = self.current_dir / "test_files" / "spot_difference_2.png"
        query = "幫我分析這兩張圖片裡的時鐘時間是否一樣？一樣回答「一樣」，不一樣回答「不一樣」"
        img_url1 = upload_and_get_tmp_public_url(
            img1_path,
            "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
            "sebastian.hsu@gmail.com",
        )
        img_url2 = upload_and_get_tmp_public_url(
            img2_path,
            "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
            "sebastian.hsu@gmail.com",
        )
        result = analyze_imgs([img_url1, img_url2], query)  # Pass URL in a list

        # Print the result for inspection
        print("\ntest_analyze_2_images_content_case_1:")
        print("-" * 50)
        print(result)
        print("-" * 50)

        # 確保結果不為空
        self.assertIsNotNone(result)
        self.assertNotEqual("", result)

        # 確保結果不是錯誤訊息
        self.assertFalse(result.startswith("Error:"))

        # 確保回應內容包含描述性文字
        self.assertIn("不一樣", result)

        img1_path = self.current_dir / "test_files" / "spot_difference_1.png"
        img2_path = self.current_dir / "test_files" / "spot_difference_1.png"
        query = "幫我分析這兩張圖片裡的時鐘時間是否一樣？一樣回答「一樣」，不一樣回答「不一樣」"
        img_url1 = upload_and_get_tmp_public_url(
            img1_path,
            "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
            "sebastian.hsu@gmail.com",
        )
        img_url2 = upload_and_get_tmp_public_url(
            img2_path,
            "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
            "sebastian.hsu@gmail.com",
        )
        result = analyze_imgs([img_url1, img_url2], query)  # Pass URL in a list

        # Print the result for inspection
        print("\ntest_analyze_2_images_content_case_2:")
        print("-" * 50)
        print(result)
        print("-" * 50)

        # 確保結果不為空
        self.assertIsNotNone(result)
        self.assertNotEqual("", result)

        # 確保結果不是錯誤訊息
        self.assertFalse(result.startswith("Error:"))

        # 確保回應內容包含描述性文字
        self.assertIn("一樣", result)

    def test_analyze_images_media_type_jpeg(self):
        """Test analyzing the content of the image"""
        img1_path = (
            self.current_dir / "test_files" / "ImportedPhoto.760363950.029251.jpeg"
        )
        img2_path = (
            self.current_dir / "test_files" / "ImportedPhoto.760363950.030446.jpeg"
        )
        img3_path = (
            self.current_dir / "test_files" / "ImportedPhoto.760363950.031127.jpeg"
        )
        query = "我該去哪個月台，為什麼？回答時要包含列車車號以及月台號。"
        img_url1 = upload_and_get_tmp_public_url(
            img1_path,
            "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
            "sebastian.hsu@gmail.com",
        )
        img_url2 = upload_and_get_tmp_public_url(
            img2_path,
            "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
            "sebastian.hsu@gmail.com",
        )
        img_url3 = upload_and_get_tmp_public_url(
            img3_path,
            "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
            "sebastian.hsu@gmail.com",
        )
        result = analyze_imgs(
            [img_url1, img_url2, img_url3], query
        )  # Pass URL in a list

        # Print the result for inspection
        print("\ntest_analyze_images_media_type_jpeg:")
        print("-" * 50)
        print(result)
        print("-" * 50)

        # 確保結果不為空
        self.assertIsNotNone(result)
        self.assertNotEqual("", result)

        # 確保結果不是錯誤訊息
        self.assertFalse(result.startswith("Error:"))

        # 確保回應內容包含描述性文字
        self.assertTrue(
            any(
                platform in result
                for platform in [
                    "5 A-C",
                    "5 D-F",
                    "5-A-C",
                    "5-A/C",
                    "5-D-F",
                    "5-D/F",
                ]
            ),
            "Result should contain either '5 A-C' or '5 D-F'",
        )


if __name__ == "__main__":
    unittest.main()
