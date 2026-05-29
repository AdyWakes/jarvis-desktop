# Jarvis Backend

FastAPI service that powers the Jarvis desktop assistant.

## Highlights

- Modular agent orchestrator with OpenAI tool-calling
- Regex-based command router for fast deterministic intents
- Pluggable tools: app launcher, browser automation, file summarizer, task memory, system info
- Drop-in plugin loader (`app/plugins/*.py`)
- Whisper transcription endpoint
- WebSocket streaming for live UI updates
- SQLite-backed conversation and task memory

## Local development

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium      # required for the browse_web tool
cp ../.env.example ../.env       # then add your OPENAI_API_KEY
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` for the OpenAPI explorer.

## Tests

```bash
pytest
```

## Project layout

```
backend/
├── app/
│   ├── core/          # agent, router, registry, memory, schemas
│   ├── tools/         # built-in tools (one module each)
│   ├── plugins/       # drop-in third-party tools
│   ├── routers/       # FastAPI routers (chat, stt, tasks, tools, system)
│   ├── services/      # external integrations (OpenAI, Whisper)
│   ├── config.py      # pydantic-settings
│   └── main.py        # FastAPI app factory + lifespan
└── tests/
```

## Writing a plugin

Create `app/plugins/my_plugin.py`:

```python
from pydantic import BaseModel, Field
from app.tools.base import Tool

class WeatherArgs(BaseModel):
    city: str = Field(description="City to look up.")

class WeatherTool(Tool):
    name = "get_weather"
    description = "Return the current weather for a city."
    parameters_model = WeatherArgs

    async def run(self, city: str) -> dict:
        ...
```

Restart the server. The tool is now visible at `GET /tools` and callable by the agent.
