import asyncio
from botrun_flow_lang.models.botrun_app import BotrunApp
from botrun_flow_lang.models.workflow import WorkflowData
from botrun_flow_lang.models.nodes.start_node import StartNode, StartNodeData
from botrun_flow_lang.models.nodes.llm_node import LLMNode, LLMNodeData, LLMModelConfig
from botrun_flow_lang.models.nodes.end_node import EndNode, EndNodeData
from botrun_flow_lang.api.workflow.workflow_engine import run_workflow


async def test_run_workflow():
    # 创建 BotrunApp
    botrun_app = BotrunApp(name="波文件問答", description="給波文件問答用的app")

    # 创建 StartNode
    start_node = StartNode(
        data=StartNodeData(title="Start", user_input="告訴我一個小紅帽的故事")
    )

    # 创建 LLMNode
    model_config = LLMModelConfig(
        completion_params={
            "max_tokens": 4096,
            "temperature": 0.7,
        },
        mode="chat",
        name="gpt-4o-2024-08-06",
        provider="openai",
    )
    llm_node = LLMNode(
        data=LLMNodeData(
            title="LLM",
            model=model_config,
            prompt_template=[
                {
                    "role": "system",
                    "text": "妳是臺灣人，回答要用臺灣繁體中文正式用語，需要的時候也可以用英文，可以親切、俏皮、幽默，但不能隨便輕浮。在使用者合理的要求下請盡量配合他的需求，不要隨便拒絕",
                },
                {
                    "role": "user",
                    "text": "{user_input}",
                },
            ],
        )
    )

    # 创建 EndNode
    end_node = EndNode(data=EndNodeData(title="End", output="故事結束：{llm_output}"))

    # 创建 Workflow
    workflow = WorkflowData(nodes=[start_node, llm_node, end_node])

    # 运行工作流
    result = await run_workflow(workflow, {})

    # 打印结果
    print(result["final_output"])

    # 添加一些断言来验证结果
    assert "final_output" in result
    assert result["final_output"].startswith("故事結束：")
    assert "小紅帽" in result["final_output"]


if __name__ == "__main__":
    asyncio.run(test_run_workflow())
