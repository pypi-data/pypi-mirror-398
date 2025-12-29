import inspect
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from typing import get_type_hints, Any
import sys

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from botrun_flow_lang.langgraph_agents.agents.langgraph_react_agent import (
    chat_with_pdf,
    chat_with_imgs,
    current_date_time,
    scrape,
    web_search,
    # deep_research,
    create_mermaid_diagram,
    create_plotly_chart,
    generate_image,
    generate_tmp_public_url,
    create_html_page,
)

# List of tool functions to document
TOOLS = sorted(
    [
        chat_with_imgs,
        chat_with_pdf,
        create_mermaid_diagram,
        create_plotly_chart,
        current_date_time,
        generate_image,
        generate_tmp_public_url,
        scrape,
        web_search,
        # deep_research,
        create_html_page,
    ],
    key=lambda x: x.name,
)


def get_tool_info(tool):
    """Extract documentation information from a tool function."""
    # 處理 LangChain 工具
    if hasattr(tool, "name"):
        func_name = tool.name
    else:
        func_name = tool.__name__

    # 獲取文檔字符串
    if hasattr(tool, "description"):
        doc = tool.description
    else:
        doc = inspect.getdoc(tool) or "No documentation available."

    # 獲取簽名
    if hasattr(tool, "func"):
        sig = inspect.signature(tool.func)
    else:
        sig = inspect.signature(tool)

    # Get parameters info
    parameters = []
    for name, param in sig.parameters.items():
        annotation = (
            str(param.annotation)
            if param.annotation != inspect.Parameter.empty
            else "Any"
        )
        if "Annotated" in annotation:
            # 簡化 Annotated 類型
            annotation = annotation.split("[")[1].split(",")[0]
        parameters.append(
            {
                "name": name,
                "annotation": annotation,
                "default": (
                    None
                    if param.default == inspect.Parameter.empty
                    else str(param.default)
                ),
            }
        )

    # Get return annotation
    return_annotation = (
        str(sig.return_annotation)
        if sig.return_annotation != inspect.Signature.empty
        else "Any"
    )
    if "Annotated" in return_annotation:
        # 簡化 Annotated 類型
        return_annotation = return_annotation.split("[")[1].split(",")[0]

    return {
        "name": func_name,
        "doc": doc,
        "parameters": parameters,
        "return_annotation": return_annotation,
    }


def generate_html_docs():
    """Generate HTML documentation for all tool functions."""
    # Setup Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates"))
    )
    template = env.get_template("tools.html")

    # Get documentation for all tools
    tools_info = [get_tool_info(tool) for tool in TOOLS]

    # Render the template
    html_content = template.render(tools=tools_info)

    # Ensure the output directory exists
    output_dir = Path(project_root) / "botrun_flow_lang" / "static" / "docs" / "tools"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write the HTML file
    output_file = output_dir / "index.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Documentation generated at: {output_file}")


if __name__ == "__main__":
    generate_html_docs()
