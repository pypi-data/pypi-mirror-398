import os
import re
from typing import List
from dotenv import load_dotenv

from botrun_flow_lang.llm_agent.llm_agent import LlmAgent

load_dotenv()

DEFAULT_APPEND_SYSTEM_PROMPT = os.getenv("DEFAULT_APPEND_SYSTEM_PROMPT", "")

AGENT_TEMPLATE = """
你會遵守以下 tag <你需要遵守的原則> 內的原則，來回應使用者的輸入，使用者的輸入使用 tag <使用者的輸入> 標籤表示。
<你需要遵守的原則>
{rules}
</你需要遵守的原則>

<使用者的輸入>
{context}
</使用者的輸入>
"""


def get_agents(xml_system_prompt: str) -> List[LlmAgent]:
    # 如果不是 XML 格式，返回空列表
    # if not xml_system_prompt.strip().startswith("<agents>"):
    #     return []

    agent_prompts = []
    # 使用正則表達式找出所有 <agent> 標籤及其內容
    agent_patterns = re.findall(r"<agent>(.*?)</agent>", xml_system_prompt, re.DOTALL)

    for agent_content in agent_patterns:
        # 提取 name, model, print-output（如果存在）
        name = re.search(r"<name>(.*?)</name>", agent_content)
        name = name.group(1) if name else ""

        model = re.search(r"<model>(.*?)</model>", agent_content)
        model = model.group(1) if model else os.getenv("MULTI_AGENT_DEFAULT_MODEL", "")

        print_output = re.search(r"<print-output>(.*?)</print-output>", agent_content)
        print_output = print_output.group(1).lower() == "true" if print_output else True

        print_plotly = re.search(r"<print-plotly>(.*?)</print-plotly>", agent_content)
        print_plotly = print_plotly.group(1).lower() == "true" if print_plotly else True

        gen_image = re.search(r"<gen-image>(.*?)</gen-image>", agent_content)
        gen_image = gen_image.group(1).lower() == "true" if gen_image else False

        include_in_history = re.search(
            r"<include-in-history>(.*?)</include-in-history>", agent_content
        )
        include_in_history = (
            include_in_history.group(1).lower() == "true"
            if include_in_history
            else True
        )

        max_system_prompt_length = re.search(
            r"<max-system-prompt-length>(.*?)</max-system-prompt-length>", agent_content
        )
        max_system_prompt_length = (
            int(max_system_prompt_length.group(1)) if max_system_prompt_length else None
        )

        # 整個 <agent> 標籤的內容（包括 <agent> 標籤本身）作為 system_prompt
        system_prompt = f"<agent>{agent_content}</agent>"
        if DEFAULT_APPEND_SYSTEM_PROMPT:
            system_prompt = f"{system_prompt} \n\n{DEFAULT_APPEND_SYSTEM_PROMPT}"

        agent_prompt = LlmAgent(
            name=name,
            model=model,
            system_prompt=system_prompt,
            print_output=print_output,
            print_plotly=print_plotly,
            gen_image=gen_image,
            include_in_history=include_in_history,
            max_system_prompt_length=max_system_prompt_length,
        )
        agent_prompts.append(agent_prompt)

    return agent_prompts
