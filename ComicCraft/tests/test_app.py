from fastapi.testclient import TestClient
from types import SimpleNamespace
import json
from pathlib import Path

import pytest

from app.main import app


client = TestClient(app)


def test_health():

    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    assert response.json()[
        "status"
    ] == "ok"


def test_homepage():

    response = client.get("/")

    assert response.status_code == 200

    assert "COMICCRAFT" in response.text


def test_api_validation():

    response = client.post(
        "/generate-comic/json",
        json={
            "story_prompt": "x"
        }
    )

    assert response.status_code == 422


def test_gemini_outline_uses_configured_model(monkeypatch):
    from app import gemini_text_generator

    calls = {}

    class FakeInteractions:
        def create(self, **kwargs):
            calls["request"] = kwargs
            return SimpleNamespace(
                output_text=json.dumps({
                    "panels": [
                        {
                            "panel_number": 1,
                            "title": "A beginning",
                            "scene_description": "The hero finds a map.",
                            "image_prompt": "A hero holding a map.",
                        }
                    ]
                }),
            )

    class FakeGeminiClient:
        def __init__(self, api_key):
            calls["api_key"] = api_key
            self.interactions = FakeInteractions()

    monkeypatch.setattr(
        gemini_text_generator.settings,
        "gemini_api_key",
        "test-gemini-key",
    )
    monkeypatch.setattr(
        gemini_text_generator.settings,
        "gemini_text_model",
        "test-gemini-model",
    )
    monkeypatch.setattr(
        gemini_text_generator.genai,
        "Client",
        FakeGeminiClient,
    )

    result = gemini_text_generator.generate_outline("A hero finds a map.")

    assert result.panels[0].title == "A beginning"
    assert calls["api_key"] == "test-gemini-key"
    assert calls["request"]["model"] == "test-gemini-model"
    assert calls["request"]["response_format"]["mime_type"] == "application/json"
    assert calls["request"]["store"] is False


def test_hugging_face_image_uses_serverless_provider_and_retries(
    monkeypatch,
    tmp_path,
):
    from app import image_generator

    calls = {"requests": [], "sleeps": []}

    class TransientServerError(Exception):
        response = SimpleNamespace(
            status_code=503,
            json=lambda: {"estimated_time": 0},
        )

    class FakeImage:
        def save(self, path, format):
            Path(path).write_bytes(b"test-image")

    class FakeInferenceClient:
        def __init__(self, **kwargs):
            calls["client"] = kwargs

        def text_to_image(self, **kwargs):
            calls["requests"].append(kwargs)
            if len(calls["requests"]) < 3:
                raise TransientServerError("Model is loading")
            return FakeImage()

    monkeypatch.setattr(image_generator.settings, "hf_api_key", "test-token")
    monkeypatch.setattr(
        image_generator.settings,
        "hf_image_model",
        "stabilityai/stable-diffusion-3-medium-diffusers",
    )
    monkeypatch.setattr(image_generator.settings, "mock_mode", False)
    monkeypatch.setattr(
        image_generator.settings,
        "image_provider",
        "huggingface",
    )
    monkeypatch.setattr(image_generator, "PANELS_DIR", tmp_path)
    monkeypatch.setattr(
        image_generator,
        "InferenceClient",
        FakeInferenceClient,
    )
    monkeypatch.setattr(
        image_generator.time,
        "sleep",
        lambda delay: calls["sleeps"].append(delay),
    )

    image_url = image_generator.generate_image("A fox explores a forest", 1)

    assert calls["client"] == {
        "api_key": "test-token",
        "provider": "hf-inference",
    }
    assert len(calls["requests"]) == 3
    assert calls["requests"][0]["model"] == (
        "stabilityai/stable-diffusion-3-medium-diffusers"
    )
    assert calls["requests"][0]["width"] == 1024
    assert calls["requests"][0]["height"] == 1024
    assert calls["sleeps"] == [1.0, 1.0]
    assert image_url.startswith("/static/panels/panel_1_")