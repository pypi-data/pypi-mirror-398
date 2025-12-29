import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from uvicorn.config import LOGGING_CONFIG

# Configure custom logging with timestamp
LOGGING_CONFIG["formatters"]["default"][
    "fmt"
] = "%(asctime)s [%(name)s] %(levelprefix)s %(message)s"
LOGGING_CONFIG["formatters"]["access"][
    "fmt"
] = '%(asctime)s [%(name)s] %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'


app = FastAPI(
    title="Botrun Flow Language Fast API",
    description="A lightweight FastAPI server",
    version="0.1.0",
)


# Add custom logging middleware

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/fast_hello")
async def fast_hello():
    return {
        "status": "success",
        "message": "Hello from fast API!",
        "service": "botrun-flow-lang-fastapi-fast",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Add this if you want to run the app directly with python
if __name__ == "__main__":
    uvicorn.run("main_fast:app", host="0.0.0.0", port=8081, log_config=LOGGING_CONFIG)
