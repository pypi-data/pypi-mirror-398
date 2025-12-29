from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional

from botrun_flow_lang.langgraph_agents.agents.util.youtube_util import (
    get_youtube_summary,
)


router = APIRouter(prefix="/youtube")


class YouTubeSummaryRequest(BaseModel):
    url: HttpUrl
    prompt: Optional[str] = None


@router.post("/summary")
async def get_summary(request_body: YouTubeSummaryRequest):
    try:
        summary = get_youtube_summary(str(request_body.url), request_body.prompt)
        if summary.startswith("Error:"):
            raise HTTPException(status_code=400, detail=summary)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
