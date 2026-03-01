# giraf-ai

Shared AI microservice for the GIRAF platform. Provides image generation and text-to-speech behind provider-agnostic interfaces.

## Stack

- Python 3.12+, FastAPI, uv
- Stateless — no database

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/generate/image` | Generate image from prompt |
| POST | `/api/v1/tts` | Text-to-speech synthesis |
| GET | `/api/v1/tts/voices` | List available voices |
| GET | `/api/v1/health` | Provider health status |

All endpoints except `/health` require a Core-issued JWT (`Authorization: Bearer <token>`).

## Providers

Configured via environment variables. Falls back to mock adapters when no keys are set.

| Capability | Provider | Env var |
|------------|----------|---------|
| Image | OpenAI DALL-E | `IMAGE_PROVIDER=openai_dalle`, `OPENAI_API_KEY` |
| Image | Google Gemini | `IMAGE_PROVIDER=gemini`, `GEMINI_API_KEY` |
| TTS | Google Cloud TTS | `TTS_PROVIDER=google_tts`, `GOOGLE_TTS_CREDENTIALS` |
| TTS | Google Gemini TTS | `TTS_PROVIDER=gemini_tts`, `GEMINI_API_KEY` |

## Running

```bash
uv sync
uv run python main.py          # http://localhost:8100
```

Or with Docker:

```bash
docker compose up
```

## Tests

```bash
uv sync --all-extras
uv run pytest
```

## Prompt Templates

Prompt templates live in `prompts/` as plain markdown files. They are loaded once at startup — edit and restart to apply changes.

```
prompts/
├── image/
│   ├── pictogram.md    # style="pictogram" (default)
│   ├── realistic.md    # style="realistic"
│   └── cartoon.md      # style="cartoon"
└── tts/
    └── default.md      # applied to all TTS requests
```

- **Image**: filename stem maps to the `style` parameter. Use `{prompt}` as the placeholder for the user's input. Drop in a new `.md` file to add a style.
- **TTS**: `default.md` wraps all TTS text. Use `{text}` as the placeholder. Currently a passthrough.

## Environment

| Variable | Required | Default |
|----------|----------|---------|
| `JWT_SECRET` | Yes | — |
| `IMAGE_PROVIDER` | No | `mock` |
| `TTS_PROVIDER` | No | `mock` |
| `OPENAI_API_KEY` | If using DALL-E | — |
| `GEMINI_API_KEY` | If using Gemini | — |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` |
| `GEMINI_TTS_MODEL` | No | `gemini-2.5-flash-preview-tts` |
| `GOOGLE_TTS_CREDENTIALS` | If using Google TTS | — |
| `HOST` | No | `0.0.0.0` |
| `PORT` | No | `8100` |
