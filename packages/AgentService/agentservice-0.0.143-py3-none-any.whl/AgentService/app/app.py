
import fastapi
from fastapi.middleware.cors import CORSMiddleware

import uvicorn
from contextlib import asynccontextmanager

from AgentService.config import Config
from AgentService.types import setup_database

from .routes import (
    chat_router,
    storage_router,
    meta_router
)


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    await setup_database(Config().db_uri, Config().db_name)

    yield

    return


app = fastapi.FastAPI(lifespan=lifespan)
app.include_router(chat_router)
app.include_router(storage_router)
app.include_router(meta_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


def start_app():
    config = Config()
    uvicorn.run(app, host=config.app_host, port=config.app_port)
