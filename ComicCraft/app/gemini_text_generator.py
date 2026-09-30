import json

from google import genai
from google.genai import types
from pydantic import BaseModel

from .config import settings
from .schemas import ComicOutline, ComicStory


def _generate_structured_response(
    prompt: str,
    response_model: type[BaseModel],
    stage: str,
) -> BaseModel:
    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add a Gemini API key to .env."
        )

    client = genai.Client(api_key=settings.gemini_api_key)
    interaction = client.interactions.create(
        model=settings.gemini_text_model,
        input=prompt,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": response_model.model_json_schema(),
        },
        generation_config={"temperature": 0.7},
        store=False,
    )

    if interaction.output_text:
        try:
            return response_model.model_validate(
                json.loads(interaction.output_text)
            )
        except (json.JSONDecodeError, ValueError) as error:
            raise RuntimeError(
                f"Gemini returned invalid structured output for {stage}."
            ) from error

    raise RuntimeError(f"Gemini returned an empty response for {stage}.")


def generate_outline(
    story_prompt: str,
    character: str = "",
    setting: str = "",
    tone: str = "",
    art_style: str = "",
) -> ComicOutline:
    prompt = f"""
Create a complete 5-panel comic story outline.

STORY IDEA:
{story_prompt}

MAIN CHARACTER:
{character}

SETTING:
{setting}

TONE:
{tone}

ART STYLE:
{art_style}

Requirements:
- Create exactly 5 panels.
- Each panel must contain a clear scene and useful image description.
- Keep the same main character throughout the story.
- Create a logical beginning, middle, and ending.
- Make the story interesting, easy to understand, and suitable for a college project.
- Return only the JSON object matching the provided schema.
"""

    return _generate_structured_response(
        prompt,
        ComicOutline,
        "comic outline",
    )


def generate_detailed_story(
    outline: ComicOutline,
    character: str = "",
    setting: str = "",
    tone: str = "",
    art_style: str = "",
) -> ComicStory:
    prompt = f"""
Convert this outline into a complete 5-panel comic story.

MAIN CHARACTER:
{character}

SETTING:
{setting}

TONE:
{tone}

ART STYLE:
{art_style}

OUTLINE:
{outline.model_dump_json(indent=2)}

Requirements:
- Keep exactly 5 panels and keep the main character consistent.
- Every panel must have a scene description, caption, narration, dialogue, and image prompt.
- Keep dialogue natural and narration short and meaningful.
- Make all panels connect as one story with a complete ending.
- Avoid unnecessary characters; make the comic suitable for a college project.
- Return only the JSON object matching the provided schema.
"""

    return _generate_structured_response(
        prompt,
        ComicStory,
        "detailed comic story",
    )