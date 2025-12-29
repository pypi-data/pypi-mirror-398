import os
from tempfile import NamedTemporaryFile
from typing import Dict, Any, Optional
from .local_files import upload_and_get_tmp_public_url, upload_html_and_get_public_url


async def generate_mermaid_files(
    mermaid_data: str,
    botrun_flow_lang_url: str,
    user_id: str,
    title: Optional[str] = None,
) -> str:
    """
    Generate mermaid HTML file from mermaid definition and upload it to GCS.

    Args:
        mermaid_data: Mermaid diagram definition string
        botrun_flow_lang_url: URL for the botrun flow lang API
        user_id: User ID for file upload
        title: Optional title for the diagram

    Returns:
        str: URL for the HTML file or error message starting with "Error: "
    """
    try:
        # Create HTML content with mermaid
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>{title if title else 'Mermaid Diagram'}</title>
    <style>
        body {{
            font-family: "Microsoft JhengHei", "微軟正黑體", "Heiti TC", "黑體-繁", sans-serif;
        }}
        .mermaid {{
            margin: 20px;
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{ 
            startOnLoad: true,
            theme: 'default',
            themeVariables: {{
                fontFamily: '"Microsoft JhengHei", "微軟正黑體", "Heiti TC", "黑體-繁", sans-serif'
            }}
        }});
    </script>
</head>
<body>
    <h1>{title if title else 'Mermaid Diagram'}</h1>
    <div class="mermaid">
{mermaid_data}
    </div>
</body>
</html>
"""

        # Create temporary file
        with NamedTemporaryFile(
            suffix=".html", mode="w", encoding="utf-8", delete=False
        ) as html_temp:
            try:
                # Save HTML content
                html_temp.write(html_content)
                html_temp.flush()

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

    except Exception as e:
        return f"Error: {str(e)}"
