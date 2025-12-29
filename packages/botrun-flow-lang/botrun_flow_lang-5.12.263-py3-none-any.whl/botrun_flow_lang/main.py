import contextlib
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from botrun_flow_lang.api.routes import router
from botrun_flow_lang.mcp_server import mcp

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path


# Create a lifespan manager for MCP server
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(mcp.session_manager.run())
        yield


app = FastAPI(lifespan=lifespan)

app.include_router(router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允許所有來源
    allow_credentials=True,
    allow_methods=["*"],  # 允許所有方法
    allow_headers=["*"],  # 允許所有頭
)

# 獲取專案根目錄的絕對路徑
project_root = Path(__file__).parent


@app.get("/docs/tools")  # 注意：移除了尾部的斜線
@app.get("/docs/tools/")
async def get_docs():
    return FileResponse(project_root / "static/docs/tools/index.html")


# 掛載靜態文件目錄
app.mount(
    "/docs/tools",
    StaticFiles(directory=str(project_root / "static/docs/tools")),
    name="tool_docs",
)

# Mount MCP server
app.mount("/mcp/default", mcp.streamable_http_app())


@app.get("/heartbeat")
async def heartbeat():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
