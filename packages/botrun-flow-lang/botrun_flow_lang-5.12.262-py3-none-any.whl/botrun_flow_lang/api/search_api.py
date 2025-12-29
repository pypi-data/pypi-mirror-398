from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict
import requests
import os
from dotenv import load_dotenv

router = APIRouter()

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")


class SearchRequest(BaseModel):
    query: str
    num: int = 10


def google_search(search_request: SearchRequest) -> Dict:
    query = f"{search_request.query}"
    url = (
        f"https://www.googleapis.com/customsearch/v1"
        f"?key={GOOGLE_API_KEY}"
        f"&cx={GOOGLE_CSE_ID}"
        f"&q={query}"
        f"&num={search_request.num}"
        f"&lr=lang_zh-TW"  # 設定語言為繁體中文
        f"&cr=countryTW"  # 設定地區為台灣
        f"&fileType=-pdf,-doc,-docx,-xls,-xlsx,-ppt,-pptx"
    )

    response = requests.get(url)
    search_results = response.json()

    return search_results


@router.post("/search")
async def search(search_request: SearchRequest):
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        raise HTTPException(
            status_code=500, detail="Google API credentials are not set"
        )

    try:
        results = google_search(search_request)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred during the search: {str(e)}"
        )
