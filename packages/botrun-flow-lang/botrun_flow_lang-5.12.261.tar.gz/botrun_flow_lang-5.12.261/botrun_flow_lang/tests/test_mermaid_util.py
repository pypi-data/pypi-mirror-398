import unittest
import requests
from botrun_flow_lang.langgraph_agents.agents.util.mermaid_util import (
    generate_mermaid_files,
)


class TestMermaidUtil(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.botrun_flow_lang_url = (
            "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app"
        )
        self.user_id = "sebastian.hsu@gmail.com"

    def verify_mermaid_content(self, html_url: str):
        """Helper method to verify the mermaid HTML content"""
        # Verify URL format
        self.assertTrue(html_url.endswith(".html"), "URL should end with .html")

        # Get the HTML content
        response = requests.get(html_url)
        self.assertEqual(response.status_code, 200, "Failed to fetch HTML content")

        html_content = response.text

        # Check if it's a mermaid diagram
        self.assertTrue(
            "mermaid" in html_content, "HTML content should contain 'mermaid'"
        )

        # Check if it contains the required elements
        self.assertTrue(
            '<div class="mermaid"' in html_content,
            "HTML content should contain mermaid div",
        )
        self.assertTrue(
            "mermaid.min.js" in html_content,
            "HTML content should contain mermaid.js script",
        )

    def test_generate_flowchart(self):
        """Test generating a flowchart"""
        # Test data for flowchart
        flowchart_data = """
        graph TD
            A[開始] --> B{是否有資料?}
            B -->|是| C[處理資料]
            B -->|否| D[取得資料]
            C --> E[結束]
            D --> B
        """

        # Execute test
        html_url = generate_mermaid_files(
            mermaid_data=flowchart_data,
            botrun_flow_lang_url=self.botrun_flow_lang_url,
            user_id=self.user_id,
            title="互動式流程圖",
        )

        # Verify results
        self.verify_mermaid_content(html_url)

    def test_generate_sequence_diagram(self):
        """Test generating a sequence diagram"""
        # Test data for sequence diagram
        sequence_data = """
        sequenceDiagram
            participant 使用者
            participant 系統
            participant 資料庫
            使用者->>系統: 請求資料
            系統->>資料庫: 查詢資料
            資料庫-->>系統: 返回結果
            系統-->>使用者: 顯示資料
        """

        # Execute test
        html_url = generate_mermaid_files(
            mermaid_data=sequence_data,
            botrun_flow_lang_url=self.botrun_flow_lang_url,
            user_id=self.user_id,
            title="互動式序列圖",
        )

        # Verify results
        self.verify_mermaid_content(html_url)

    def test_generate_mermaid_files_error(self):
        """Test error handling with invalid data"""
        result = generate_mermaid_files(
            mermaid_data="invalid mermaid syntax",
            botrun_flow_lang_url=self.botrun_flow_lang_url,
            user_id=self.user_id,
        )
        self.assertFalse(
            result.startswith("Error:")
        )  # Mermaid will handle syntax errors client-side


if __name__ == "__main__":
    unittest.main()
