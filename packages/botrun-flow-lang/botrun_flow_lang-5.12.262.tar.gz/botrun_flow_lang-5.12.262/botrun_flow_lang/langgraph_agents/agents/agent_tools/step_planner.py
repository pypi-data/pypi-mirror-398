from langchain_core.tools import tool
import litellm
import json

SYSTEM_PROMPT = """你是一個專業的研究規劃助手。你的工作是：
1. 分析使用者的研究需求
2. 規劃完整的研究步驟
3. 如果使用者指定特定步驟，你要規劃如何執行這些步驟

你必須嚴格按照以下 JSON 格式回覆，不要加入任何其他文字：
{
    "analysis": "對使用者需求的分析",
    "steps": [
        {
            "step": "步驟1",
            "description": "詳細說明",
            "expected_outcome": "預期結果"
        }
    ]
}"""

JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "analysis": {"type": "string", "description": "對使用者需求的分析"},
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "step": {"type": "string"},
                    "description": {"type": "string"},
                    "expected_outcome": {"type": "string"},
                },
                "required": ["step", "description", "expected_outcome"],
            },
        },
    },
    "required": ["analysis", "steps"],
}


@tool
def step_planner(user_input: str) -> str:
    """
    研究規劃工具 - 負責規劃研究步驟和執行計劃

    這個工具會：
    1. 分析使用者的研究需求
    2. 根據現有工具規劃完整的研究步驟
    3. 處理使用者指定的執行步驟

    Args:
        user_input (str): 使用者的研究需求或指定步驟

    Returns:
        str: JSON 格式的研究計劃，包含分析和詳細步驟
    """

    print("step_planner user_input============>", user_input)
    response = litellm.completion(
        model="o3-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ],
        response_format={"type": "json_object", "schema": JSON_SCHEMA},
        reasoning_effort="high",
    )

    try:
        # 確保回應是有效的 JSON 格式
        plan = json.loads(response.choices[0].message.content)
        return json.dumps(plan, ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        # 如果無法解析 JSON，直接返回原始回應
        return response.choices[0].message.content
