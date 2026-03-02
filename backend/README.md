# VTU Diary Automation - Backend

FastAPI backend for VTU Diary Automation.

## Structure

```
backend/
├── app.py                  # Main FastAPI application
├── config.py               # Env var config + get_effective_setting()
├── requirements.txt        # Python dependencies
├── src/
│   ├── ai/                 # AI/LLM integration
│   ├── api/
│   │   └── routes.py       # Endpoints + extract_credentials()
│   ├── automation/         # Browser automation (Playwright)
│   ├── input/              # File processing (CSV, audio, PDF)
│   ├── db/                 # Database models & session
│   └── utils/              # Logging
├── system_prompts/         # AI prompt templates
├── data/                   # Runtime data
├── logs/                   # Application logs
└── tests/                  # Tests
```

## Running

```bash
cd backend
python app.py               # http://localhost:5000
```

## Credential Flow

The backend is **stateless** for credentials. It reads them from request headers (sent by the browser) with env var fallback:

| Header | Config Fallback | Used By |
|--------|----------------|---------|
| `X-Groq-Key` | `GROQ_API_KEY` | LLM client |
| `X-Gemini-Key` | `GEMINI_API_KEY` | LLM client |
| `X-Cerebras-Key` | `CEREBRAS_API_KEY` | LLM client |
| `X-Openai-Key` | `OPENAI_API_KEY` | LLM client |
| `X-LLM-Provider` | `LLM_PROVIDER` | LLM client |
| `X-Portal-User` | `VTU_EMAIL` | Submission engine |
| `X-Portal-Pass` | `VTU_PASSWORD` | Submission engine |

Priority: **Header > Environment variable**

This allows each user to bring their own API keys without sharing credentials on the server.

## API Endpoints

- `GET /` - Serve React SPA
- `GET /health` - Health check
- `POST /api/upload-file` - Upload file for processing
- `POST /api/upload-text` - Upload raw text
- `POST /api/generate-preview` - Generate diary entries (reads LLM credential headers)
- `POST /api/approve-and-submit` - Submit to portal (reads portal credential headers)
- `GET /api/progress/{id}` - Submission progress
- `GET /api/history` - Submission history
- `WS /ws/progress/{id}` - WebSocket progress
- `GET /docs` - Swagger API docs

## Configuration

1. Request headers (from browser localStorage)
2. `.env` file in project root
3. `config.py` defaults

See [../.env.example](../.env.example) for server-side options.

## Development

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
python app.py
```
