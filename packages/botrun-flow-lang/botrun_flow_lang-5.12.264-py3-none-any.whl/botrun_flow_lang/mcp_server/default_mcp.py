import os
import asyncio
import json
import pytz
from datetime import datetime
from typing import Dict, Any, Optional

# Import for web_search
from botrun_flow_lang.langgraph_agents.agents.util.perplexity_search import (
    respond_with_perplexity_search,
)

from mcp.server.fastmcp import FastMCP
from langchain_core.runnables import RunnableConfig

# Import necessary dependencies
from botrun_flow_lang.models.nodes.utils import scrape_single_url
from botrun_flow_lang.langgraph_agents.agents.util.pdf_analyzer import (
    analyze_pdf_async,
)
from botrun_flow_lang.langgraph_agents.agents.util.img_util import analyze_imgs
from botrun_flow_lang.langgraph_agents.agents.util.local_files import (
    upload_and_get_tmp_public_url,
)
from botrun_flow_lang.langgraph_agents.agents.util.html_util import generate_html_file
from botrun_flow_lang.langgraph_agents.agents.util.plotly_util import (
    generate_plotly_files,
)
from botrun_flow_lang.langgraph_agents.agents.util.mermaid_util import (
    generate_mermaid_files,
)
from botrun_flow_lang.utils.clients.rate_limit_client import RateLimitClient
from botrun_flow_lang.utils.botrun_logger import get_default_botrun_logger

# Import for generate_image
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from langchain_community.callbacks import get_openai_callback

# Initialize MCP server
mcp = FastMCP(name="BotrunFlowLangDefaultMCP", stateless_http=True)

# Initialize logger - reuse the default instance
logger = get_default_botrun_logger()


# Exception class for rate limit errors
class BotrunRateLimitException(Exception):
    """Exception that should be displayed directly to the user."""

    def __init__(self, message):
        self.message = f"[Please tell user error] {message}"
        super().__init__(self.message)


@mcp.tool()
async def scrape(url: str) -> dict:
    """
    Scrape a web page to extract its content.

    Args:
        url: The URL to scrape

    Returns:
        dict: A dictionary containing the scraped content or error message
    """
    try:
        logger.info(f"scrape {url}")
        return await scrape_single_url(url)
    except Exception as e:
        logger.error(f"scrape {url} error: {e}", error=str(e), exc_info=True)
        return {"url": url, "status": "error", "error": str(e)}


@mcp.tool()
async def chat_with_pdf(
    pdf_url: str, user_input: str, botrun_flow_lang_url: str, user_id: str
) -> str:
    """
    Analyze a PDF file and answer questions about its content.

    Supports intelligent processing based on file size:
    - Small files (< 5MB): Direct multimodal analysis
    - Large files (>= 5MB): Compress -> Split -> Parallel multimodal Q&A -> Merge results

    Args:
        pdf_url: The URL to the PDF file (can be generated using generate_tmp_public_url for local files)
        user_input: The user's question or instruction about the PDF content
        botrun_flow_lang_url: REQUIRED - URL for the botrun flow lang API (LLM can get this from system prompt)
        user_id: REQUIRED - User ID for file upload (LLM can get this from system prompt)

    Returns:
        str: Analysis result or Plotly-compatible data structure if visualization is needed
    """
    logger.info(f"chat_with_pdf pdf_url: {pdf_url} user_input: {user_input}")

    # Convert local file path to public URL if needed
    if not pdf_url.startswith("http"):
        pdf_url = upload_and_get_tmp_public_url(pdf_url, botrun_flow_lang_url, user_id)

    return await analyze_pdf_async(pdf_url, user_input)


@mcp.tool()
async def chat_with_imgs(
    img_urls: list[str],
    user_input: str,
    botrun_flow_lang_url: str,
    user_id: str,
) -> str:
    """
    Analyze multiple images and answer questions about their content.

    Args:
        img_urls: List of URLs to the image files (can be generated using generate_tmp_public_url for local files)
        user_input: Question or instruction about the image content(s)
        botrun_flow_lang_url: REQUIRED - URL for the botrun flow lang API (LLM can get this from system prompt)
        user_id: REQUIRED - User ID for file upload (LLM can get this from system prompt)

    Returns:
        str: Analysis result or Plotly-compatible data structure if visualization is needed
    """
    logger.info(f"chat_with_imgs img_urls: {img_urls} user_input: {user_input}")

    # Convert local file paths to public URLs if needed
    new_img_urls = []
    for img_url in img_urls:
        if not img_url.startswith("http"):
            img_url = upload_and_get_tmp_public_url(
                img_url, botrun_flow_lang_url, user_id
            )
        new_img_urls.append(img_url)

    return analyze_imgs(new_img_urls, user_input)


@mcp.tool()
async def generate_image(
    user_input: str, user_id: str = "", botrun_flow_lang_url: str = ""
) -> str:
    """
    Generate high-quality images using DALL-E 3 and store permanently in GCS.

    When using generate_image tool, you must include the image URL in your response.
    You MUST respond using this format (from @begin img to @end, including the image URL):
    @begin img("{image_url}") @end

    Capabilities:
    - Creates photorealistic images and art
    - Handles complex scenes and compositions
    - Maintains consistent styles
    - Follows detailed prompts with high accuracy
    - Supports various artistic styles and mediums

    Best practices for prompts:
    - Be specific about style, mood, lighting, and composition
    - Include details about perspective and setting
    - Specify artistic medium if desired (e.g., "oil painting", "digital art")
    - Mention color schemes or specific colors
    - Describe the atmosphere or emotion you want to convey

    Limitations:
    - Cannot generate images of public figures or celebrities
    - Avoids harmful, violent, or adult content
    - May have inconsistencies with hands, faces, or text
    - Cannot generate exact copies of existing artworks or brands
    - Limited to single image generation per request
    - Subject to daily usage limits

    Args:
        user_input: Detailed description of the image you want to generate.
                   Be specific about style, content, and composition.
        user_id: REQUIRED - User ID for rate limit and file storage (LLM can get this from system prompt)
        botrun_flow_lang_url: REQUIRED - URL for the botrun flow lang API (LLM can get this from system prompt)

    Returns:
        str: Permanent URL to the generated image stored in GCS, or error message if generation fails
    """
    try:
        logger.info(f"generate_image user_input: {user_input}")

        # 驗證必要參數
        if not user_id:
            logger.error("User ID not available")
            return "User ID not available"
        if not botrun_flow_lang_url:
            logger.error("botrun_flow_lang_url not available")
            return "botrun_flow_lang_url not available"

        # Check rate limit before generating image
        rate_limit_client = RateLimitClient()
        rate_limit_info = await rate_limit_client.get_rate_limit(user_id)

        # Check if user can generate an image
        drawing_info = rate_limit_info.get("drawing", {})
        can_use = drawing_info.get("can_use", False)

        if not can_use:
            daily_limit = drawing_info.get("daily_limit", 0)
            current_usage = drawing_info.get("current_usage", 0)
            logger.error(
                f"User {user_id} has reached daily limit of {daily_limit} image generations. "
                f"Current usage: {current_usage}. Please try again tomorrow."
            )
            return f"[Please tell user error] You have reached your daily limit of {daily_limit} image generations. " \
                f"Current usage: {current_usage}. Please try again tomorrow."
            # raise BotrunRateLimitException(
            #     f"You have reached your daily limit of {daily_limit} image generations. "
            #     f"Current usage: {current_usage}. Please try again tomorrow."
            # )

        # 2. 使用 DALL-E 生成圖片
        dalle_wrapper = DallEAPIWrapper(
            api_key=os.getenv("OPENAI_API_KEY"), model="dall-e-3"
        )

        # Generate image with token usage tracking
        with get_openai_callback() as cb:
            temp_image_url = dalle_wrapper.run(user_input)
            logger.info(
                f"DALL-E generated temporary URL: {temp_image_url}, "
                f"prompt tokens: {cb.prompt_tokens}, "
                f"completion tokens: {cb.completion_tokens}"
            )

        # 3. 下載並上傳到 GCS，取得永久 URL
        from botrun_flow_lang.langgraph_agents.agents.util.local_files import (
            upload_image_and_get_public_url,
        )

        try:
            permanent_url = await upload_image_and_get_public_url(
                temp_image_url, botrun_flow_lang_url, user_id
            )
            logger.info(f"Image uploaded to GCS: {permanent_url}")

            # 4. 更新使用計數
            await rate_limit_client.update_drawing_usage(user_id)

            return permanent_url
        except Exception as upload_error:
            logger.error(
                f"Failed to upload to GCS, returning temporary URL: {upload_error}"
            )
            # Fallback: 回傳臨時 URL
            await rate_limit_client.update_drawing_usage(user_id)
            return temp_image_url

    except Exception as e:
        logger.error(f"generate_image error: {e}", error=str(e), exc_info=True)

        # Check if this is a user-visible exception
        if str(e).startswith("[Please tell user error]"):
            return str(e)  # Return the error message as is
        return f"Error: {e}"


@mcp.tool()
async def generate_tmp_public_url(
    file_path: str, botrun_flow_lang_url: str, user_id: str
) -> str:
    """
    Create a temporary public URL for a local file.

    Args:
        file_path: The path to the local file you want to make publicly accessible
        botrun_flow_lang_url: REQUIRED - URL for the botrun flow lang API (LLM can get this from system prompt)
        user_id: REQUIRED - User ID for file upload (LLM can get this from system prompt)

    Returns:
        str: A public URL that can be used to access the file for 7 days

    Raises:
        FileNotFoundError: If the specified file does not exist
    """
    logger.info(f"generate_tmp_public_url file_path: {file_path}")

    if not os.path.exists(file_path):
        return f"File not found: {file_path}"
        # raise FileNotFoundError(f"File not found: {file_path}")

    return upload_and_get_tmp_public_url(file_path, botrun_flow_lang_url, user_id)


@mcp.tool()
async def create_html_page(
    html_content: str,
    title: str,
    botrun_flow_lang_url: str,
    user_id: str,
) -> str:
    """
    Create a custom HTML page and return its URL.

    This tool supports complete HTML documents, including JavaScript and CSS, which can be used to create
    complex interactive pages.

    Prioritize using the following frameworks for writing HTML:
    - DataTables for tables (include in header: <link rel="stylesheet" href="https://cdn.datatables.net/2.3.3/css/dataTables.dataTables.css" /> and <script src="https://cdn.datatables.net/2.3.3/js/dataTables.js"></script>)
    - Alpine.js for interactivity (include in header: <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>)
    - Tailwind CSS for styling (include in header: <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>)
    - daisyUI for UI components (include in header: <link href="https://cdn.jsdelivr.net/npm/daisyui@5" rel="stylesheet" type="text/css" />)
    - Chart.js for charts (include in header: <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>)
    - Animate.css for animations (include in header: <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css" />)

    Input Options:
    You can pass either:
    1. A complete HTML document with doctype, html, head, and body tags
    2. An HTML fragment that will be automatically wrapped in a basic HTML structure

    Args:
        html_content: Complete HTML document or fragment. Can include JavaScript, CSS, and other elements.
        title: Optional title for the HTML page
        botrun_flow_lang_url: REQUIRED - URL for the botrun flow lang API (LLM can get this from system prompt)
        user_id: REQUIRED - User ID for file upload (LLM can get this from system prompt)

    Returns:
        str: URL for the HTML page. This URL should be provided to the user,
             as they will need to access it to view the content in their web browser.
    """
    try:
        logger.info(f"create_html_page html_content: {html_content} title: {title}")

        html_url = await generate_html_file(
            html_content, botrun_flow_lang_url, user_id, title
        )

        logger.info(f"create_html_page generated============> {html_url}")
        return html_url

    except Exception as e:
        logger.error(f"create_html_page error: {e}", error=str(e), exc_info=True)
        return f"Error creating HTML page URL: {str(e)}"


@mcp.tool()
async def create_plotly_chart(
    figure_data: str | dict,
    title: str,
    botrun_flow_lang_url: str,
    user_id: str,
) -> str:
    """
    Create an interactive Plotly visualization and return its URL.
    This URL should be provided to the user,
    as they will need to access it to view the interactive chart in their web browser.

    Scenarios for using create_plotly_chart:
    - Need to create data visualizations and charts
    - Need to show data trends (line charts)
    - Need to compare values (bar charts, pie charts)
    - Need to show distributions (scatter plots, heat maps)
    - Need to display time series data (timeline charts)
    - Need to show geographic information (maps)
    - Need to perform multidimensional data analysis (3D charts, bubble charts)
    - Need to show statistical distributions (box plots)
    - Need to show cumulative trends (area charts)
    - Need interactive data exploration

    Integration with Other Tools:
    This function can be used in conjunction with chat_with_imgs and chat_with_pdf when they return data
    suitable for visualization. When those tools detect a need for visualization, they will return a JSON string
    with a "__plotly_data__" key, which can be directly passed to this function.

    Example workflow:
    1. User asks to analyze and visualize data from images/PDFs
    2. chat_with_imgs or chat_with_pdf returns JSON string with "__plotly_data__" key
    3. Pass that string to this function to get an interactive visualization URL

    Supported Chart Types:
    - Line charts: For showing trends and time series data
    - Bar charts: For comparing values across categories
    - Pie charts: For showing proportions of a whole
    - Scatter plots: For showing relationships between variables
    - Heat maps: For showing patterns in matrix data
    - Box plots: For showing statistical distributions
    - Geographic maps: For showing spatial data
    - 3D plots: For showing three-dimensional data
    - Bubble charts: For showing three variables in 2D
    - Area charts: For showing cumulative totals over time

    The figure_data can be either:
    1. A JSON string containing plotly figure specifications with 'data' and 'layout'
    2. A dictionary object with plotly figure specifications

    Example JSON string:
    '{"data": [{"type": "scatter", "x": [1, 2, 3, 4], "y": [10, 15, 13, 17]}], "layout": {"title": "My Plot"}}'

    Example dictionary:
    {
        'data': [{
            'type': 'scatter',
            'x': [1, 2, 3, 4],
            'y': [10, 15, 13, 17]
        }],
        'layout': {
            'title': 'My Plot'
        }
    }

    Args:
        figure_data: JSON string OR dictionary containing plotly figure specifications or output from chat_with_imgs/chat_with_pdf.
                    String inputs will be parsed using json.loads(), dictionary inputs will be used directly.
        title: Optional title for the plot.
        botrun_flow_lang_url: REQUIRED - URL for the botrun flow lang API (LLM can get this from system prompt)
        user_id: REQUIRED - User ID for file upload (LLM can get this from system prompt)

    Returns:
        str: URL for the interactive HTML visualization. This URL should be provided to the user,
             as they will need to access it to view the interactive chart in their web browser.
    """
    try:
        logger.info(f"create_plotly_chart figure_data: {figure_data} title: {title}")

        # Handle both string and dict inputs
        if isinstance(figure_data, str):
            figure_dict = json.loads(figure_data)
        else:
            figure_dict = figure_data

        # If the input is from chat_with_imgs or chat_with_pdf, extract the plotly data
        if "__plotly_data__" in figure_dict:
            figure_dict = figure_dict["__plotly_data__"]

        html_url = await generate_plotly_files(
            figure_dict,
            botrun_flow_lang_url,
            user_id,
            title,
        )

        logger.info(f"create_plotly_chart generated============> {html_url}")
        return html_url

    except json.JSONDecodeError as e:
        logger.error(
            f"create_plotly_chart JSON parsing error: {e}", error=str(e), exc_info=True
        )
        return f"Error parsing JSON figure_data: {str(e)}. Please ensure figure_data is a valid JSON string or dictionary."
    except KeyError as e:
        logger.error(
            f"create_plotly_chart missing key error: {e}", error=str(e), exc_info=True
        )
        return f"Error: Missing required key in figure data: {str(e)}. Please ensure figure_data contains 'data' and 'layout' keys."
    except Exception as e:
        logger.error(f"create_plotly_chart error: {e}", error=str(e), exc_info=True)
        return f"Error creating visualization URL: {str(e)}"


@mcp.tool()
async def create_mermaid_diagram(
    mermaid_data: str,
    title: str,
    botrun_flow_lang_url: str,
    user_id: str,
) -> str:
    """
    Create an interactive Mermaid diagram visualization and return its URL.
    This URL should be provided to the user,
    as they will need to access it to view the interactive diagram in their web browser.

    Scenarios for using create_mermaid_diagram:
    - Need to visualize flowcharts, architecture diagrams, or relationship diagrams
    - Need to show system architecture (flowchart)
    - Need to explain operational processes (flowchart)
    - Need to show sequence interactions (sequence diagram)
    - Need to show state transitions (state diagram)
    - Need to show class relationships (class diagram)
    - Need to show entity relationships (ER diagram)
    - Need to show project timelines (gantt chart)
    - Need to show user journeys (journey)
    - Need to show requirement relationships (requirement diagram)
    - Need to show resource allocation (pie chart)

    Supported Diagram Types:
    1. Flowcharts (graph TD/LR):
       - System architectures
       - Process flows
       - Decision trees
       - Data flows

    2. Sequence Diagrams (sequenceDiagram):
       - API interactions
       - System communications
       - User interactions
       - Message flows

    3. Class Diagrams (classDiagram):
       - Software architecture
       - Object relationships
       - System components
       - Code structure

    4. State Diagrams (stateDiagram-v2):
       - System states
       - Workflow states
       - Process states
       - State transitions

    5. Entity Relationship Diagrams (erDiagram):
       - Database schemas
       - Data relationships
       - System entities
       - Data models

    6. User Journey Diagrams (journey):
       - User experiences
       - Customer flows
       - Process steps
       - Task sequences

    7. Gantt Charts (gantt):
       - Project timelines
       - Task schedules
       - Resource allocation
       - Milestone tracking

    8. Pie Charts (pie):
       - Data distribution
       - Resource allocation
       - Market share
       - Component breakdown

    9. Requirement Diagrams (requirementDiagram):
       - System requirements
       - Dependencies
       - Specifications
       - Constraints

    Example Mermaid syntax for a simple flowchart:
    ```
    graph TD
        A[Start] --> B{Data Available?}
        B -->|Yes| C[Process Data]
        B -->|No| D[Get Data]
        C --> E[End]
        D --> B
    ```

    Args:
        mermaid_data: String containing the Mermaid diagram definition
        title: Optional title for the diagram
        botrun_flow_lang_url: REQUIRED - URL for the botrun flow lang API (LLM can get this from system prompt)
        user_id: REQUIRED - User ID for file upload (LLM can get this from system prompt)

    Returns:
        str: URL for the interactive HTML visualization. This URL should be provided to the user,
             as they will need to access it to view the interactive diagram in their web browser.
    """
    try:
        logger.info(
            f"create_mermaid_diagram mermaid_data: {mermaid_data} title: {title}"
        )

        html_url = await generate_mermaid_files(
            mermaid_data,
            botrun_flow_lang_url,
            user_id,
            title,
        )

        logger.info(f"create_mermaid_diagram generated============> {html_url}")
        return html_url

    except Exception as e:
        logger.error(f"create_mermaid_diagram error: {e}", error=str(e), exc_info=True)
        return f"Error creating diagram URL: {str(e)}"


@mcp.tool()
async def current_date_time() -> str:
    """
    Get the current date and time in local timezone (Asia/Taipei).

    Important: You MUST call this current_date_time function when:
    1. User's query contains time-related words such as:
       - today, now, current
       - this week, next week
       - this month, last month
       - this year, last year, next year
       - recent, lately
       - future, upcoming
       - past, previous
    2. User asks about current events or latest information
    3. User wants to know time-sensitive information
    4. Queries involving relative time expressions

    Examples of when to use current_date_time:
    - "What's the weather today?"
    - "This month's stock market performance"
    - "Any recent news?"
    - "Economic growth from last year until now"
    - "Upcoming events for next week"
    - "This month's sales data"

    Args:
        botrun_flow_lang_url: Optional URL for the botrun flow lang API (not used for this tool)
        user_id: Optional user ID (not used for this tool)

    Returns:
        str: Current date and time in format "YYYY-MM-DD HH:MM Asia/Taipei"
    """
    try:
        logger.info("current_date_time called")

        local_tz = pytz.timezone("Asia/Taipei")
        local_time = datetime.now(local_tz)
        result = local_time.strftime("%Y-%m-%d %H:%M %Z")

        logger.info(f"current_date_time============> {result}")
        return result

    except Exception as e:
        logger.error(f"current_date_time error: {e}", error=str(e), exc_info=True)
        return f"Error: {e}"


def format_dates(dt):
    """
    Format datetime for both Western and Taiwan formats
    Western format: yyyy-mm-dd hh:mm:ss
    Taiwan format: (yyyy-1911)-mm-dd hh:mm:ss
    """
    western_date = dt.strftime("%Y-%m-%d %H:%M:%S")
    taiwan_year = dt.year - 1911
    taiwan_date = f"{taiwan_year}-{dt.strftime('%m-%d %H:%M:%S')}"

    return {"western_date": western_date, "taiwan_date": taiwan_date}


@mcp.tool()
async def web_search(
    user_input: str,
    return_images: bool = False,
) -> dict:
    """
    Search the web for up-to-date information using Perplexity.
    This tool provides detailed answers with citations.

    Unless the user insists on multiple-round searches, this tool can search for multiple conditions at once, for example:
    - Good: web_search("Search for today's sports, financial, and political news")
    - Unnecessary: Making separate searches for sports, financial, and political news

    Time/Date Information Requirements:
    1. MUST preserve any specific dates or time periods mentioned in the user's query
    2. Include both the current time and any specific time references from the query

    Examples:
    - Basic query:
      User asks: "Population of Japan"
      web_search("Population of Japan")
      Returns: {
          "content": "According to the latest statistics, Japan's population is about 125 million...",
          "citations": [
              {"title": "Statistics Bureau of Japan", "url": "https://www.stat.go.jp/..."},
              {"title": "World Bank Data", "url": "https://data.worldbank.org/..."}
          ]
      }

    - Query with specific date:
      User asks: "Look up news from January 15, 2023"
      web_search("Look up news from January 15, 2023")
      Returns: {
          "content": "News from January 15, 2023 includes...",
          "citations": [
              {"title": "BBC News", "url": "https://www.bbc.com/..."},
              {"title": "Reuters", "url": "https://www.reuters.com/..."}
          ]
      }

    - Location-specific query:
      User asks: "Weather in Paris today"
      web_search("Weather in Paris today")
      Returns: {
          "content": "Today's weather in Paris shows...",
          "citations": [
              {"title": "Weather Service", "url": "https://www.weather.com/..."},
              {"title": "Meteorological Office", "url": "https://www.metoffice.gov.uk/..."}
          ]
      }

    Args:
        user_input: The search query or question you want to find information about.
                   MUST include any specific time periods or dates from the original query.
                   Examples of time formats to preserve:
                   - Specific dates: "2025/1/1", "2023-12-31", "January 15, 2023"
                   - Years: "2023"
                   - Quarters/Months: "Q1", "January", "First quarter"
                   - Time periods: "past three years", "next five years"
                   - Relative time: "yesterday", "next week", "last month"
        return_images: Whether to include images in search results. Set to True when you need to search for and return images along with text content.
        botrun_flow_lang_url: Optional URL for the botrun flow lang API (not used for this tool)
        user_id: Optional user ID (not used for this tool)

    Returns:
        dict: A dictionary containing:
              - content (str): The detailed answer based on web search results
              - citations (list): A list of URLs, citations are important to provide to the user
              - images (list): A list of image URLs (only when return_images is True)
    """
    try:
        logger.info(f"web_search user_input: {user_input}")

        now = datetime.now()
        dates = format_dates(now)
        western_date = dates["western_date"]
        taiwan_date = dates["taiwan_date"]

        logger.info(f"western_date: {western_date} taiwan_date: {taiwan_date}")

        # Format input with current time context (English only)
        final_input = (
            f"The current date: {western_date}\nThe user's question is: {user_input}"
        )

        # Process search using async generator
        search_result = {
            "content": "",
            "citations": [],
        }

        async for event in respond_with_perplexity_search(
            final_input,
            user_prompt_prefix="",
            messages_for_llm=[],
            domain_filter=[],
            stream=False,
            structured_output=True,
            return_images=return_images,
        ):
            if event and isinstance(event.chunk, str):
                search_result = json.loads(event.chunk)

        logger.info(
            f"web_search completed============> {len(search_result.get('content', ''))}"
        )
        return (
            search_result
            if search_result
            else {"content": "No results found.", "citations": []}
        )

    except Exception as e:
        logger.error(f"web_search error: {e}", error=str(e), exc_info=True)
        return {"content": f"Error during web search: {str(e)}", "citations": []}
