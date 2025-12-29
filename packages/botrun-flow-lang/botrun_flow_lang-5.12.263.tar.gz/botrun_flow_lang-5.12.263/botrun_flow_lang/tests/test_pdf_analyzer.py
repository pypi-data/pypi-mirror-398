import unittest
import os
from pathlib import Path
from botrun_flow_lang.langgraph_agents.agents.util.local_files import (
    upload_and_get_tmp_public_url,
)
from botrun_flow_lang.langgraph_agents.agents.util.pdf_analyzer import analyze_pdf


class TestPDFAnalyzer(unittest.TestCase):
    def setUp(self):
        # Get the path to the test PDF file
        current_dir = Path(__file__).parent
        self.pdf_path = (
            current_dir
            / "test_files"
            / "1120701A海廣離岸風力發電計畫環境影響說明書-C04.PDF"
        )

        # Ensure the test file exists
        self.assertTrue(
            os.path.exists(self.pdf_path), f"Test file not found at {self.pdf_path}"
        )

    def test_pdf_exists(self):
        """Test if the PDF file exists"""
        self.assertEqual(True, os.path.exists(self.pdf_path))

    def test_pdf_readable(self):
        """Test if the PDF file is readable"""
        self.assertEqual(True, os.access(self.pdf_path, os.R_OK))

    def test_pdf_not_empty(self):
        """Test if the PDF file is not empty"""
        self.assertEqual(True, os.path.getsize(self.pdf_path) > 0)

    def test_pdf_extension(self):
        """Test if the file has a PDF extension"""
        self.assertEqual(True, self.pdf_path.suffix.lower() == ".pdf")

    def test_analyze_table_4_3_1(self):
        """Test analyzing table 4.3-1 from the PDF"""
        query = "請你幫我找出在報告書中的「表 4.3-1 環境敏感地區調查表-第一級環境敏感地區」表格中的所有項目的「查詢結果及限制內容」幫我列出是或否？請全部列出來，不要遺漏"
        pdf_url = upload_and_get_tmp_public_url(
            self.pdf_path,
            "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
            "sebastian.hsu@gmail.com",
        )
        result = analyze_pdf(pdf_url, query)

        # Print the result for inspection
        print("\nAnalyze PDF Result:")
        print("-" * 50)
        print(result)
        print("-" * 50)

        # 確保結果不為空
        self.assertIsNotNone(result)
        self.assertNotEqual("", result)

        # 檢查每個項目的結果
        self.assertTrue(
            "活動斷層兩側一定範圍: 否" in result
            or "活動斷層兩側一定範圍：否" in result,
        )
        self.assertTrue(
            "特定水土保持區: 否" in result or "特定水土保持區：否" in result
        )
        self.assertTrue("河川區域: 否" in result or "河川區域：否" in result)
        self.assertTrue(
            "洪氾區一級管制區及洪水平原一級管制區: 否" in result
            or "洪氾區一級管制區及洪水平原一級管制區：否" in result
        )
        self.assertTrue(
            "區域排水設施範圍: 是" in result or "區域排水設施範圍：是" in result
        )
        self.assertTrue(
            "國家公園區內之特別景觀區、生態保護區: 否" in result
            or "國家公園區內之特別景觀區、生態保護區：否" in result
        )
        self.assertTrue("自然保留區: 否" in result or "自然保留區：否" in result)
        self.assertTrue(
            "野生動物保護區: 否" in result or "野生動物保護區：否" in result
        )
        self.assertTrue(
            "野生動物重要棲息環境: 是" in result or "野生動物重要棲息環境：是" in result
        )
        self.assertTrue("自然保護區: 否" in result or "自然保護區：否" in result)
        self.assertTrue(
            "一級海岸保護區: 是" in result or "一級海岸保護區：是" in result
        )
        self.assertTrue(
            "國際級重要濕地、國家級重要濕地之核心保育區及生態復育區: 否" in result
            or "國際級重要濕地、國家級重要濕地之核心保育區及生態復育區：否" in result
        )
        self.assertTrue("古蹟保存區: 否" in result or "古蹟保存區：否" in result)
        self.assertTrue("考古遺址: 否" in result or "考古遺址：否" in result)
        self.assertTrue(
            "重要聚落建築群: 否" in result or "重要聚落建築群：否" in result
        )


if __name__ == "__main__":
    unittest.main()
