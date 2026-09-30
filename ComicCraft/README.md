# ComicCraft - AI Comic Story Creator

ComicCraft is an AI-powered comic story creator.

## Features

- Story prompt input
- Character configuration
- Setting selection
- Tone selection
- Art style selection
- Gemini outline generation
- Gemini story generation
- AI image generation
- Five comic panels
- Comic preview
- PDF export
- FastAPI backend
- Jinja2 frontend
- JSON API

## Project Flow

User Prompt
    ↓
Gemini Outline
    ↓
Detailed Comic Story
    ↓
Image Generation
    ↓
Comic Layout
    ↓
PDF Export

## Installation

Create a virtual environment:

python -m venv .venv

Activate it on Windows PowerShell:

.venv\Scripts\Activate.ps1

Install dependencies:

pip install -r requirements.txt

## Configuration

Copy:

.env.example

to:

.env

Add `GEMINI_API_KEY` for story and outline generation, and `HF_API_KEY` for
image generation. The image model is
`stabilityai/stable-diffusion-3-medium-diffusers`.

## Test With Placeholder Images

Set:

MOCK_MODE=true

and:

IMAGE_PROVIDER=placeholder

Text generation still uses Gemini.

Then run:

uvicorn app.main:app --reload

Open:

http://127.0.0.1:8000

## Real AI Mode

Set:

MOCK_MODE=false

IMAGE_PROVIDER=huggingface

Provide a Gemini API key as `GEMINI_API_KEY` and a Hugging Face token as
`HF_API_KEY`. Gemini creates the text; image generation calls the configured
Hugging Face model through `hf-inference`, retries transient errors up to three
times, and requests 1024x1024 images for Stable Diffusion 3 Medium.

## API

GET /

GET /health

POST /generate

POST /generate-comic/json

POST /test-image

GET /download/{filename}

GET /export-success

## API Documentation

When the application is running:

http://127.0.0.1:8000/docs