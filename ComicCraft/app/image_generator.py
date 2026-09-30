from pathlib import Path
import time

import httpx
from PIL import Image, ImageDraw, ImageFont
from huggingface_hub import InferenceClient

from .config import PANELS_DIR, settings
from .utils import unique_id


def _is_retryable_inference_error(error: Exception) -> bool:
    response = getattr(error, "response", None)
    status_code = getattr(response, "status_code", None)

    return (
        status_code in {408, 425, 429, 500, 502, 503, 504}
        or isinstance(
            error,
            (
                ConnectionError,
                TimeoutError,
                httpx.TimeoutException,
                httpx.TransportError,
            ),
        )
    )


def _retry_delay(error: Exception, attempt: int) -> float:
    response = getattr(error, "response", None)
    try:
        estimated_time = response.json().get("estimated_time")
        if estimated_time is not None:
            return min(max(float(estimated_time), 1.0), 30.0)
    except (AttributeError, TypeError, ValueError):
        pass

    return float(2 ** attempt)


def _request_image(client: InferenceClient, prompt: str):
    for attempt in range(1, 4):
        try:
            return client.text_to_image(
                prompt=prompt,
                model=settings.hf_image_model,
                negative_prompt=(
                    "blurry, low quality, distorted face, "
                    "extra limbs, bad anatomy, "
                    "unreadable text, watermark"
                ),
                width=1024,
                height=1024,
                num_inference_steps=25,
                guidance_scale=7.0,
            )
        except Exception as error:
            if attempt == 3 or not _is_retryable_inference_error(error):
                raise

            delay = _retry_delay(error, attempt)
            print(
                f"[ComicCraft] Hugging Face image inference failed "
                f"transiently; retrying in {delay:g}s "
                f"(attempt {attempt + 1}/3)."
            )
            time.sleep(delay)


def create_placeholder_image(
    prompt: str,
    panel_number: int,
    output_path: Path,
) -> None:

    image = Image.new(
        "RGB",
        (1024, 1024),
        "white"
    )

    draw = ImageDraw.Draw(image)

    try:

        font = ImageFont.truetype(
            "arial.ttf",
            42
        )

        small_font = ImageFont.truetype(
            "arial.ttf",
            24
        )

    except OSError:

        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    draw.rectangle(
        (40, 40, 984, 984),
        outline="black",
        width=5
    )

    draw.text(
        (80, 90),
        f"ComicCraft - Panel {panel_number}",
        fill="black",
        font=font
    )

    draw.ellipse(
        (250, 260, 774, 784),
        outline="black",
        width=8
    )

    draw.text(
        (80, 830),
        "Test image - enable Hugging Face "
        "for AI artwork.",
        fill="black",
        font=small_font
    )

    image.save(
        output_path,
        format="PNG"
    )


def generate_image(
    prompt: str,
    panel_number: int,
) -> str:

    filename = (
        f"panel_{panel_number}_"
        f"{unique_id()}.png"
    )

    output_path = PANELS_DIR / filename

    # --------------------------------------------------------
    # TEST MODE
    # --------------------------------------------------------

    if (
        settings.mock_mode
        or settings.image_provider.lower()
        == "placeholder"
    ):

        create_placeholder_image(
            prompt,
            panel_number,
            output_path
        )

        return (
            f"/static/panels/{filename}"
        )

    # --------------------------------------------------------
    # REAL IMAGE GENERATION
    # --------------------------------------------------------

    if not settings.hf_api_key:

        raise RuntimeError(
            "HF_API_KEY is missing. "
            "Add it to .env or use "
            "IMAGE_PROVIDER=placeholder."
        )

    client = InferenceClient(
        api_key=settings.hf_api_key,
        provider="hf-inference"
    )

    image = _request_image(client, prompt)

    image.save(
        output_path,
        format="PNG"
    )

    return (
        f"/static/panels/{filename}"
    )