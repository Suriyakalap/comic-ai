from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import STATIC_DIR
from .routes import router


app = FastAPI(
    title="ComicCraft - AI Comic Story Creator",

    description=(
        "Generate five-panel AI comics "
        "using Hugging Face text and image models."
    ),

    version="1.0.0",
)


app.mount(
    "/static",
    StaticFiles(
        directory=str(STATIC_DIR)
    ),
    name="static",
)


app.include_router(
    router
)


@app.get("/health")
async def health():

    return {
        "status": "ok",
        "service": "ComicCraft"
    }