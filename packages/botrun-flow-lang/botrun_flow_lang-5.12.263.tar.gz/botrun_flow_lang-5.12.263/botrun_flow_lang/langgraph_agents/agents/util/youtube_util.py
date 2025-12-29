from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
import re
import os

load_dotenv()


def get_video_id(url: str) -> str:
    """
    Extract video ID from various YouTube URL formats.
    Supports:
    - Standard watch URLs (youtube.com/watch?v=...)
    - Shortened URLs (youtu.be/...)
    - Embed URLs (youtube.com/embed/...)
    """
    # Try parsing as standard URL first
    parsed_url = urlparse(url)

    # Handle youtu.be URLs
    if parsed_url.netloc == "youtu.be":
        return parsed_url.path.lstrip("/")

    # Handle standard youtube.com URLs
    if parsed_url.netloc in ["www.youtube.com", "youtube.com"]:
        if parsed_url.path == "/watch":
            # Standard watch URL
            return parse_qs(parsed_url.query).get("v", [""])[0]
        elif "/embed/" in parsed_url.path:
            # Embed URL
            return parsed_url.path.split("/embed/")[-1]

    # Try extracting video ID using regex as fallback
    video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    if video_id_match:
        return video_id_match.group(1)

    raise ValueError(f"Could not extract video ID from URL: {url}")


def get_youtube_summary(url: str, prompt: str = None) -> str:
    # print("[get_youtube_summary]url============>", url)
    # print("[get_youtube_summary]prompt============>", prompt)
    from google import genai
    from google.genai.types import HttpOptions, Part
    from google.oauth2 import service_account
    from google.genai import types

    if prompt is None:
        prompt = "Write a short and engaging blog post based on this video."

    try:
        credentials = service_account.Credentials.from_service_account_file(
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS_FOR_FASTAPI"),
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        client = genai.Client(
            # http_options=HttpOptions(api_version="v1"),
            credentials=credentials,
            project="scoop-386004",
            location="us-central1",
        )
        model_id = "gemini-2.5-flash"
        # model_id = "gemini-2.5-pro"

        response = client.models.generate_content(
            model=model_id,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part(
                            file_data=types.FileData(
                                mime_type="video/mp4", file_uri=url
                            )
                        ),
                        types.Part(text=prompt),
                    ],
                )
            ],
        )

        # print(response.text)
        return response.text
    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"Error getting YouTube summary: {e}")
        return f"Error: Failed to get YouTube summary: {e}"
