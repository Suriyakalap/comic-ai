from pathlib import Path

from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    Request,
)

from fastapi.responses import (
    FileResponse,
    HTMLResponse,
)

from fastapi.templating import (
    Jinja2Templates,
)

from .config import (
    EXPORTS_DIR,
    TEMPLATES_DIR,
    settings,
)

from .exporters import save_pdf
from .gemini_text_generator import (
    generate_detailed_story,
    generate_outline,
)
from .image_generator import generate_image
from .layout_builder import build_comic_layout
from .schemas import PromptRequest


router = APIRouter()

templates = Jinja2Templates(
    directory=str(TEMPLATES_DIR)
)


def generate_complete_comic(
    data: PromptRequest
):

    # STEP 1
    outline = generate_outline(
        data.story_prompt,
        data.character_name,
        data.setting,
        data.tone,
        data.art_style,
    )

    # STEP 2
    story = generate_detailed_story(
        outline,
        data.character_name,
        data.setting,
        data.tone,
        data.art_style,
    )

    # STEP 3
    image_paths = []

    for panel in story.panels:

        image_path = generate_image(
            panel.image_prompt,
            panel.panel_number
        )

        image_paths.append(
            image_path
        )

    # STEP 4
    layout = build_comic_layout(
        story,
        image_paths
    )

    # STEP 5
    title = (
        f"{data.character_name}'s Comic"
    )

    pdf_filename, pdf_url = save_pdf(
        layout,
        title=title
    )

    return {
        "outline": outline,
        "story": story,
        "layout": layout,
        "pdf_filename": pdf_filename,
        "pdf_url": pdf_url,
        "title": title,
    }


@router.get(
    "/",
    response_class=HTMLResponse
)
async def home(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "panel_count":
                settings.panel_count,

            "mock_mode":
                settings.mock_mode,
        },
    )


@router.post(
    "/generate",
    response_class=HTMLResponse
)
async def generate(
    request: Request,

    story_prompt: str = Form(...),

    character_name: str = Form(...),

    setting: str = Form(...),

    tone: str = Form(...),

    art_style: str = Form(...),
):

    data = PromptRequest(
        story_prompt=story_prompt,
        character_name=character_name,
        setting=setting,
        tone=tone,
        art_style=art_style,
    )

    try:

        result = (
            generate_complete_comic(
                data
            )
        )

    except Exception as exc:

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "panel_count":
                    settings.panel_count,

                "mock_mode":
                    settings.mock_mode,

                "error":
                    str(exc),

                "form":
                    data.model_dump(),
            },
            status_code=500,
        )

    return templates.TemplateResponse(
        request=request,
        name="comic_preview.html",
        context=result,
    )


@router.post(
    "/generate-comic/json"
)
async def generate_comic_json(
    data: PromptRequest
):

    try:

        result = (
            generate_complete_comic(
                data
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        ) from exc

    return {
        "title":
            result["title"],

        "outline":
            result["outline"].model_dump(),

        "story":
            result["story"].model_dump(),

        "layout":
            result["layout"],

        "pdf": {
            "filename":
                result["pdf_filename"],

            "url":
                result["pdf_url"],
        },
    }


@router.post(
    "/test-image"
)
async def test_image(
    payload: dict
):

    prompt = str(
        payload.get(
            "prompt",
            ""
        )
    ).strip()

    if not prompt:

        raise HTTPException(
            status_code=400,
            detail="Prompt is required."
        )

    try:

        image_url = generate_image(
            prompt,
            0
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        ) from exc

    return {
        "image_url":
            image_url
    }


@router.get(
    "/download/{filename}"
)
async def download(
    filename: str
):

    safe_name = Path(
        filename
    ).name

    if (
        safe_name != filename
        or not safe_name.endswith(".pdf")
    ):

        raise HTTPException(
            status_code=400,
            detail="Invalid PDF filename."
        )

    file_path = (
        EXPORTS_DIR / safe_name
    )

    if not file_path.is_file():

        raise HTTPException(
            status_code=404,
            detail="PDF not found."
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=safe_name,
    )


@router.get(
    "/export-success",
    response_class=HTMLResponse
)
async def export_success(
    request: Request,
    filename: str = ""
):

    safe_name = (
        Path(filename).name
        if filename
        else ""
    )

    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "filename":
                safe_name
        }
    )