import sys
import os


from botrun_flow_lang.langgraph_agents.agents.util.youtube_util import (
    get_youtube_summary,
)

if __name__ == "__main__":
    # You can change this URL or pass it as a command-line argument
    # For now, it uses the example URL from the original get_youtube_summary function
    video_url = "https://www.youtube.com/watch?v=3KtWfp0UopM"
    print(f"Getting summary for YouTube video: {video_url}")
    summary = get_youtube_summary(video_url)
    print("\nSummary:")
    print(summary)
