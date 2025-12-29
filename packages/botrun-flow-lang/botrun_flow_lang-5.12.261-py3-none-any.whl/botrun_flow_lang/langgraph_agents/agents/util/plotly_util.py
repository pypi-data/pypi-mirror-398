import plotly.graph_objects as go
import os
from tempfile import NamedTemporaryFile
from typing import Dict, Any, Optional
from .local_files import upload_and_get_tmp_public_url, upload_html_and_get_public_url


async def generate_plotly_files(
    figure_data: Dict[str, Any],
    botrun_flow_lang_url: str,
    user_id: str,
    title: Optional[str] = None,
) -> str:
    """
    Generate plotly HTML file from figure data and upload it to GCS.

    Args:
        figure_data: Dictionary containing plotly figure data and layout
        botrun_flow_lang_url: URL for the botrun flow lang API
        user_id: User ID for file upload
        title: Optional title for the plot

    Returns:
        str: URL for the HTML file or error message starting with "Error: "
    """
    try:
        # Create plotly figure from data and layout
        data = figure_data.get("data", [])
        layout = figure_data.get("layout", {})

        # If title is provided, add it to the layout before creating the figure
        if title:
            layout["title"] = {"text": title}

        # Create figure with data and layout
        fig = go.Figure(data=data, layout=layout)

    except Exception as e:
        return f"Error: {str(e)}"

    # Create temporary file
    with NamedTemporaryFile(suffix=".html", delete=False) as html_temp:
        try:
            # Save HTML with plotly.js included
            fig.write_html(html_temp.name, include_plotlyjs=True, full_html=True)

            # Upload file to GCS
            html_url = await upload_html_and_get_public_url(
                html_temp.name, botrun_flow_lang_url, user_id
            )

            # Clean up temporary file
            os.unlink(html_temp.name)

            return html_url
        except Exception as e:
            # Clean up temporary file in case of error
            os.unlink(html_temp.name)
            return f"Error: {str(e)}"
