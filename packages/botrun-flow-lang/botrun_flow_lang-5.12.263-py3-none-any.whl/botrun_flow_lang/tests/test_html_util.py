import unittest
import asyncio
from pathlib import Path
import os
from botrun_flow_lang.langgraph_agents.agents.util.html_util import modify_gcs_html


class TestHtmlUtil(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.gcs_url = "https://storage.googleapis.com/hatch-botrun-hatch-dev/html/sebastian.hsu%40gmail.com/tmp_euvrg5j.html"
        self.modification_instruction = (
            "Increase the number at the top of the page by 1"
        )

    def test_modify_gcs_html(self):
        """Test modify_gcs_html function with real parameters"""
        # Run the async function with real parameters
        result = asyncio.run(
            modify_gcs_html(self.gcs_url, self.modification_instruction)
        )

        # Print the result for manual verification
        print("\nTest Result:")
        print(f"Success: {result[0]}")
        print(f"URL: {result[1]}")
        print(f"Error (if any): {result[2]}")


if __name__ == "__main__":
    unittest.main()
