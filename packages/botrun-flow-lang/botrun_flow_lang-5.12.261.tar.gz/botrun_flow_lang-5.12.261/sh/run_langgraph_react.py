from botrun_flow_lang.api.langgraph_api import (
    CUSTOM_WEB_RESEARCH_AGENT,
    PERPLEXITY_SEARCH_AGENT,
    LangGraphRequest,
    run_langgraph,
)
import uuid
import asyncio
from dotenv import load_dotenv
from botrun_flow_lang.langgraph_agents.agents.agent_runner import agent_runner
from botrun_flow_lang.langgraph_agents.agents.search_agent_graph import graph


load_dotenv()


async def run_langgraph_react():
    running_graph = graph
    id = str(uuid.uuid4())
    user_input = "我們是新北市政府想要增加環保工作業務人手和資源，請問有相關的辦理計畫可以申請嗎？"
    async for chunk in agent_runner(id, {"messages": [user_input]}, running_graph):
        print(chunk)
    print("done")


if __name__ == "__main__":
    asyncio.run(run_langgraph_react())
