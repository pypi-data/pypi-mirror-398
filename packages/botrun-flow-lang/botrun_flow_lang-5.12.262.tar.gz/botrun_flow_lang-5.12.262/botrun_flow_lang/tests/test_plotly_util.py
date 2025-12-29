import unittest
import requests
from botrun_flow_lang.langgraph_agents.agents.util.plotly_util import (
    generate_plotly_files,
)


class TestPlotlyUtil(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.botrun_flow_lang_url = (
            "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app"
        )
        self.user_id = "sebastian.hsu@gmail.com"

    def verify_plotly_content(self, html_url: str, expected_title: str):
        """Helper method to verify the plotly HTML content"""
        # Verify URL format
        self.assertTrue(html_url.endswith(".html"), "URL should end with .html")

        # Get the HTML content
        response = requests.get(html_url)
        self.assertEqual(response.status_code, 200, "Failed to fetch HTML content")

        html_content = response.text.lower()

        # Debug print
        print("\nHTML Content (first 500 chars):", html_content[:500])
        print("\nExpected title:", expected_title.lower())

        # Check if it's a plotly chart (case insensitive)
        self.assertTrue(
            "plotly" in html_content, "HTML content should contain 'plotly'"
        )

        # Check if it contains the expected title (case insensitive)
        # expected_title_lower = expected_title.lower()
        # self.assertTrue(
        #     expected_title_lower in html_content,
        #     f"HTML content should contain title '{expected_title}'",
        # )

        # Check if it contains the required plotly elements
        self.assertTrue(
            "<div" in html_content, "HTML content should contain div elements"
        )
        self.assertTrue(
            "<script" in html_content, "HTML content should contain script elements"
        )

    def test_generate_scatter_plot(self):
        """Test generating a scatter plot"""
        # Test data for scatter plot
        scatter_data = {
            "data": [
                {
                    "type": "scatter",
                    "x": [1, 2, 3, 4, 5],
                    "y": [10, 11, 13, 8, 15],
                    "mode": "markers+lines",
                    "name": "樣本數據",
                }
            ],
            "layout": {
                "title": "散點圖範例",
                "xaxis": {"title": "X軸"},
                "yaxis": {"title": "Y軸"},
            },
        }

        # Execute test
        html_url = generate_plotly_files(
            figure_data=scatter_data,
            botrun_flow_lang_url=self.botrun_flow_lang_url,
            user_id=self.user_id,
            title="互動式散點圖",
        )

        # Verify results
        self.verify_plotly_content(html_url, "互動式散點圖")

    def test_generate_bar_chart(self):
        """Test generating a bar chart"""
        # Test data for bar chart
        bar_data = {
            "data": [
                {
                    "type": "bar",
                    "x": ["甲", "乙", "丙", "丁"],
                    "y": [20, 14, 23, 25],
                    "name": "長條圖數據",
                }
            ],
            "layout": {
                "title": "長條圖範例",
                "xaxis": {"title": "類別"},
                "yaxis": {"title": "數值"},
            },
        }

        # Execute test
        html_url = generate_plotly_files(
            figure_data=bar_data,
            botrun_flow_lang_url=self.botrun_flow_lang_url,
            user_id=self.user_id,
            title="互動式長條圖",
        )

        # Verify results
        self.verify_plotly_content(html_url, "互動式長條圖")

    def test_generate_pie_chart(self):
        """Test generating a pie chart"""
        # Test data for pie chart
        pie_data = {
            "data": [
                {
                    "type": "pie",
                    "values": [35, 25, 20, 20],
                    "labels": ["甲部門", "乙部門", "丙部門", "丁部門"],
                    "hole": 0.4,
                }
            ],
            "layout": {"title": "圓餅圖範例", "showlegend": True},
        }

        # Execute test
        html_url = generate_plotly_files(
            figure_data=pie_data,
            botrun_flow_lang_url=self.botrun_flow_lang_url,
            user_id=self.user_id,
            title="互動式圓餅圖",
        )

        # Verify results
        self.verify_plotly_content(html_url, "互動式圓餅圖")

    def test_generate_plotly_files_error(self):
        """Test error handling with invalid data"""
        result = generate_plotly_files(
            figure_data={
                "data": [{"type": "invalid_type"}]
            },  # Invalid plot type will cause an error
            botrun_flow_lang_url=self.botrun_flow_lang_url,
            user_id=self.user_id,
        )
        self.assertTrue(result.startswith("Error:"))


if __name__ == "__main__":
    unittest.main()
