from typing import AsyncGenerator
from google.generativeai import GenerativeModel
from google.generativeai.protos import Candidate

from pydantic import BaseModel


class GeminiGroundingEvent(BaseModel):
    chunk: str


async def respond_with_gemini_grounding(
    input_content, messages_for_llm
) -> AsyncGenerator[GeminiGroundingEvent, None]:
    model = GenerativeModel("models/gemini-1.5-pro-002")

    # 將 litellm 格式轉換為 Gemini 格式的對話歷史
    chat_history = []
    for message in messages_for_llm:
        role = "user" if message["role"] == "user" else "model"
        chat_history.append({"role": role, "parts": [message["content"]]})

    # 建立聊天實例
    chat = model.start_chat(history=chat_history)

    # 使用 chat.send() 替代 generate_content
    responses = chat.send_message(
        input_content,
        tools={"google_search_retrieval": {"dynamic_retrieval_config": {}}},
        stream=True,
    )

    # answer_message = await cl.Message(content="").send()
    full_response = ""
    for response in responses:
        if response.candidates[0].finish_reason != Candidate.FinishReason.STOP:
            # await answer_message.stream_token(response.text)
            yield GeminiGroundingEvent(chunk=response.text)
            full_response += response.text
            if response.candidates[0].grounding_metadata:
                if len(response.candidates[0].grounding_metadata.grounding_chunks) > 0:
                    references = f"\n\n{tr('Sources:')}\n"
                    for grounding_chunk in response.candidates[
                        0
                    ].grounding_metadata.grounding_chunks:
                        references += f"- [{grounding_chunk.web.title}]({grounding_chunk.web.uri})\n"
                    # await answer_message.stream_token(references)
                    yield GeminiGroundingEvent(chunk=references)
        else:
            if response.candidates[0].grounding_metadata:
                if len(response.candidates[0].grounding_metadata.grounding_chunks) > 0:
                    references = f"\n\n參考來源：\n"
                    for grounding_chunk in response.candidates[
                        0
                    ].grounding_metadata.grounding_chunks:
                        references += f"- [{grounding_chunk.web.title}]({grounding_chunk.web.uri})\n"
                    # await answer_message.stream_token(references)
                    yield GeminiGroundingEvent(chunk=references)

    # await answer_message.update()

    # chat_history = cl.user_session.get("chat_history", [])
    # chat_history.append({"role": "user", "content": input_content})
    # chat_history.append({"role": "assistant", "content": full_response})
    # cl.user_session.set("chat_history", chat_history)
    # return
