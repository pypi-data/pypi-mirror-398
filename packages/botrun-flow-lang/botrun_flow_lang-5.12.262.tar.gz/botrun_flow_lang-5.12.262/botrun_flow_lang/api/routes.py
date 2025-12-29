import os
from fastapi import APIRouter
from dotenv import load_dotenv
from google.oauth2 import service_account

# Include hatch routes
from botrun_flow_lang.api import (
    auth_api,
    botrun_back_api,
    hatch_api,
    langgraph_api,
    storage_api,
    subsidy_api,
    user_setting_api,
    search_api,
    rate_limit_api,
    line_bot_api,
    version_api,
    youtube_api,
    model_api,
)

load_dotenv()

router = APIRouter(prefix="/api")
router.include_router(
    auth_api.router,
)
router.include_router(
    hatch_api.router,
)
router.include_router(
    user_setting_api.router,
)
router.include_router(
    search_api.router,
)
router.include_router(
    langgraph_api.router,
)
router.include_router(
    storage_api.router,
)
router.include_router(
    subsidy_api.router,
)
router.include_router(
    rate_limit_api.router,
)
router.include_router(
    line_bot_api.router,
)
router.include_router(
    botrun_back_api.router,
)
router.include_router(
    version_api.router,
)
router.include_router(
    youtube_api.router,
)
router.include_router(
    model_api.router,
)


@router.get("/hello")
async def hello():
    env_name = os.getenv("ENV_NAME")
    google_service_account_key_path = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS_FOR_FASTAPI",
        "/app/keys/scoop-386004-d22d99a7afd9.json",
    )
    credentials = service_account.Credentials.from_service_account_file(
        google_service_account_key_path,
        scopes=["https://www.googleapis.com/auth/datastore"],
    )

    return {"message": f"Hello World {env_name}"}
