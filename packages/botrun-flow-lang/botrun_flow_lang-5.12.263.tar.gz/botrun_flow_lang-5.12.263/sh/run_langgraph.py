from botrun_flow_lang.api.langgraph_api import (
    CUSTOM_WEB_RESEARCH_AGENT,
    PERPLEXITY_SEARCH_AGENT,
    LangGraphRequest,
    run_langgraph,
)
import uuid
import asyncio
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    uuid = str(uuid.uuid4())
    user_input = (
        "我們是新北市政府想要增加環保工作業務人手和資源，請問有相關的辦理計畫可以申請嗎"
    )
    graph_name = PERPLEXITY_SEARCH_AGENT
    config = {
        "domain_filter": ["*.gov.tw", "-*.gov.cn"],
        "search_prompt": "",
        "search_vendor": "perplexity",
    }

    graph_name = CUSTOM_WEB_RESEARCH_AGENT
    config = {
        "domain_filter": ["*.gov.tw", "-*.gov.cn"],
        "search_prompt": "",
        "model": "openai",
    }
    request = LangGraphRequest(
        graph_name=graph_name,
        thread_id=uuid,
        user_input=user_input,
        config=config,
    )
    response = asyncio.run(run_langgraph(request))
    print(response)
