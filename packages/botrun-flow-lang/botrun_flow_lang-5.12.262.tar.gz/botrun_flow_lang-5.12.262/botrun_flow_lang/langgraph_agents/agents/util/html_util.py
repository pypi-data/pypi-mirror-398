import os
from tempfile import NamedTemporaryFile
from typing import Dict, Any, Optional, Tuple
import re
from urllib.parse import urlparse, urlunparse, unquote, parse_qs, urlencode
import time
from io import BytesIO
import requests

from botrun_flow_lang.constants import MODIFY_GCS_HTML_MODEL
from .local_files import upload_html_and_get_public_url
from botrun_flow_lang.services.storage.storage_factory import storage_store_factory


async def generate_html_file(
    html_content: str,
    botrun_flow_lang_url: str,
    user_id: str,
    title: Optional[str] = None,
) -> str:
    """
    Generate HTML file from complete HTML content (including JS and CSS) and upload it to GCS.

    This function accepts complete HTML documents with JavaScript, CSS, and other elements.
    You can pass either:
    1. A complete HTML document (<!DOCTYPE html><html>...<head>...</head><body>...</body></html>)
    2. HTML fragment that will be wrapped in a basic HTML structure if needed

    The function preserves all JavaScript, CSS, and other elements in the HTML content.

    Args:
        html_content: Complete HTML content string, including head/body tags, JavaScript, CSS, etc.
        botrun_flow_lang_url: URL for the botrun flow lang API
        user_id: User ID for file upload
        title: Optional title for the HTML page (used only if the HTML doesn't already have a title)

    Returns:
        str: URL for the HTML file or error message starting with "Error: "
    """
    try:
        # Check if the content is already a complete HTML document
        is_complete_html = html_content.strip().lower().startswith(
            "<!doctype html"
        ) or html_content.strip().lower().startswith("<html")

        # Only process HTML content if it's not already a complete document
        if not is_complete_html:
            # If not a complete HTML document, check if it has a head tag
            if "<head>" in html_content.lower():
                # Has head tag but not complete doc, add title if needed and provided
                if title and "<title>" not in html_content.lower():
                    html_content = html_content.replace(
                        "<head>", f"<head>\n    <title>{title}</title>", 1
                    )
            else:
                # No head tag, wrap the content in a basic HTML structure
                html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>{title if title else 'HTML Page'}</title>
    <style>
        body {{
            font-family: "Microsoft JhengHei", "微軟正黑體", "Heiti TC", "黑體-繁", sans-serif;
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""
        # If we have complete HTML but title is provided and no title exists
        elif title and "<title>" not in html_content.lower():
            # Try to insert title into the head tag
            if "<head>" in html_content.lower():
                html_content = html_content.replace(
                    "<head>", f"<head>\n    <title>{title}</title>", 1
                )

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


# todo 還沒改完，我的測試案例測到 3 之後，就不會再增加了
async def modify_gcs_html(
    html_url: str,
    modification_instruction: str,
) -> Tuple[bool, str, Optional[str]]:
    """
    Modify HTML file stored in Google Cloud Storage using Gemini 2.0 Flash LLM.

    The function parses the GCS URL, fetches the HTML content, sends it to Gemini with
    the modification instruction, executes the generated Python code to modify the HTML,
    and updates the original file in GCS.

    Args:
        html_url: GCS URL pointing to an HTML file
                 (format: https://storage.googleapis.com/[bucket-name]/[doc-path])
        modification_instruction: Natural language instruction for how to modify the HTML

    Returns:
        Tuple[bool, str, Optional[str]]: (success, original_url, error_message)
    """
    try:
        # 1. Parse the GCS URL to extract bucket name and document path
        url_parts = urlparse(html_url)

        # Strip query parameters from the URL for processing
        clean_url_parts = url_parts._replace(query="")
        clean_url = urlunparse(clean_url_parts)

        if not url_parts.netloc.startswith("storage.googleapis.com"):
            return False, html_url, "Error: URL must be a Google Cloud Storage URL"

        # Extract bucket name and document path correctly
        path_segments = url_parts.path.strip("/").split("/", 1)
        if len(path_segments) < 2:
            return False, html_url, "Error: Invalid GCS URL format"

        bucket_name = path_segments[0]
        document_path = path_segments[1]

        # URL decode the document path to handle encoded characters like %40
        decoded_document_path = unquote(document_path)

        # 2. Fetch the HTML content from GCS
        try:
            # First try to get the HTML directly via the URL
            response = requests.get(clean_url)
            if response.status_code != 200:
                # If direct access fails, use the storage client
                storage = storage_store_factory()
                # Use the original (non-decoded) path for retrieval since that's how it's stored in GCS
                file_object = await storage.retrieve_file(document_path)
                if not file_object:
                    return (
                        False,
                        html_url,
                        "Error: Could not retrieve HTML file from GCS",
                    )
                # Explicitly decode with UTF-8 to properly handle non-ASCII characters
                html_content = file_object.getvalue().decode("utf-8")
            else:
                # Set encoding for response text (use UTF-8 or detect from content)
                if "charset=" in response.headers.get("content-type", ""):
                    # Extract charset from content-type header
                    charset = (
                        response.headers.get("content-type")
                        .split("charset=")[1]
                        .split(";")[0]
                    )
                    response.encoding = charset
                else:
                    # Default to UTF-8 if not specified
                    response.encoding = "utf-8"
                html_content = response.text
        except Exception as e:
            return False, html_url, f"Error retrieving HTML content: {str(e)}"

        # 3. Call Gemini API to generate Python code for HTML modification
        try:
            # Import here to avoid loading time and potential circular imports
            import google.generativeai as genai
            from google.generativeai.types import HarmCategory, HarmBlockThreshold

            # Initialize Gemini client
            api_key = os.getenv("GEMINI_API_KEY", "")
            if not api_key:
                return (
                    False,
                    html_url,
                    "Error: GEMINI_API_KEY environment variable not set",
                )

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(MODIFY_GCS_HTML_MODEL)

            # Create prompt for Gemini
            prompt = f"""You are an expert HTML and Python developer. 
Your task is to modify an HTML document according to the following instruction:
"{modification_instruction}"

Here is the HTML code to modify:
```html
{html_content}
```

Please provide minimal Python code that makes these modifications to the HTML. 
Your code must:
1. Use BeautifulSoup4 to parse and modify the HTML
2. Return the modified HTML as a string
3. Use a function called 'modify_html' that takes the original HTML as input and returns the modified HTML
4. Only include essential code to make the exact change requested - no explanations or verbose comments
5. Ensure you preserve the character encoding for non-ASCII characters
6. Use BeautifulSoup with features='html.parser'

Only provide the Python code, nothing else. Keep the code minimal and direct."""

            # Generate the Python code
            response = model.generate_content(prompt)
            generated_code = response.text

            # Extract Python code if it's wrapped in ```python ... ```
            if "```python" in generated_code:
                python_code_match = re.search(
                    r"```python(.*?)```", generated_code, re.DOTALL
                )
                if python_code_match:
                    generated_code = python_code_match.group(1).strip()
            elif "```" in generated_code:
                python_code_match = re.search(r"```(.*?)```", generated_code, re.DOTALL)
                if python_code_match:
                    generated_code = python_code_match.group(1).strip()

            # 4. Execute the generated Python code
            # Create a safe execution environment
            try:
                local_vars = {"original_html": html_content}
                # Make sure we have BeautifulSoup available
                exec("from bs4 import BeautifulSoup", local_vars)

                # Execute the generated code
                exec(generated_code, local_vars)

                # Call the modify_html function
                if "modify_html" in local_vars:
                    modified_html = local_vars["modify_html"](html_content)
                else:
                    return (
                        False,
                        html_url,
                        "Error: Generated code does not contain a modify_html function",
                    )

                if not modified_html or not isinstance(modified_html, str):
                    return (
                        False,
                        html_url,
                        "Error: Generated code did not produce valid HTML",
                    )

                # Check if the model actually made changes to the HTML
                if modified_html.strip() == html_content.strip():
                    return (
                        False,
                        html_url,
                        "Error: The model didn't make any changes to the HTML. It might not understand how to perform the requested modification.",
                    )

            except Exception as e:
                return False, html_url, f"Error executing generated code: {str(e)}"

            # 5. Update the original HTML file in GCS
            try:
                storage = storage_store_factory()
                # Explicitly encode with UTF-8 to preserve non-ASCII characters
                file_object = BytesIO(modified_html.encode("utf-8"))

                # Store the modified file back to the same location using the decoded path
                # This ensures proper handling of special characters like @ in the path
                success, _ = await storage.store_file(
                    decoded_document_path,
                    file_object,
                    public=True,
                    content_type="text/html; charset=utf-8",  # Explicitly set UTF-8 charset
                )

                if not success:
                    return (
                        False,
                        html_url,
                        "Error: Failed to update the HTML file in GCS",
                    )

                # Add timestamp as query parameter to the URL to bypass cache
                timestamp = int(time.time())
                url_with_timestamp = urlparse(clean_url)
                new_query = urlencode({"t": timestamp})
                final_url = urlunparse(url_with_timestamp._replace(query=new_query))

                return True, final_url, None

            except Exception as e:
                return False, html_url, f"Error updating HTML file: {str(e)}"

        except Exception as e:
            return False, html_url, f"Error generating modification code: {str(e)}"

    except Exception as e:
        return False, html_url, f"Error: {str(e)}"
