
import fastapi
import subprocess

from loguru import logger

from importlib.metadata import version

from .models import (
    GetVersionResponse
)


meta_router = fastapi.APIRouter(prefix="/meta")


@meta_router.get("/version")
async def get_version() -> GetVersionResponse:
    try:
        outer_version = subprocess.run(
            "python3.11 -c \"from importlib.metadata import version; print(version('AgentService'))\"",
            shell=True,
            capture_output=True,
            text=True,
            cwd="."
        ).stdout.replace("\n", "")

    except Exception as err:
        logger.exception(err)

        outer_version = "N/A"

    return GetVersionResponse(
        data={
            "inner": version("AgentService"),
            "outer": outer_version,
        },
        status="ok"
    )
