# Contributing to VTU Diary Automation

## Project Structure

```
VTU-sel/
├── frontend/          # React frontend (Vite + TypeScript)
├── backend/           # Python backend (FastAPI)
├── static/            # Built frontend assets
├── .env.example       # Server-side config (optional)
├── docker-compose.yml # Full-stack Docker setup
└── Dockerfile         # Backend container
```

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### First Time Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd VTU-sel

# 2. Setup backend
cd backend
python -m venv ../.venv
source ../.venv/bin/activate  # Windows: ..\.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# 3. Setup frontend
cd ../frontend
npm install

# 4. Configure environment
cp .env.example .env
# Edit .env with your credentials and API keys

# 5. Build frontend
npm run build

# 6. Run backend
cd ../backend
python app.py
```

## Development Workflow

### Backend Development

```bash
cd backend
python app.py

# The server will auto-reload on file changes
```

**Backend structure:**
- `backend/app.py` - Main FastAPI app
- `backend/src/api/` - API routes and models
- `backend/src/ai/` - LLM integration
- `backend/src/automation/` - Browser automation
- `backend/src/input/` - File processors

### Frontend Development

```bash
# Terminal 1: Frontend dev server with HMR
cd frontend
npm run dev
# Opens at http://localhost:3000

# Terminal 2: Backend API
cd backend
python app.py
# Runs at http://localhost:5000
```

**Frontend structure:**
- `frontend/src/pages/` - Page components
- `frontend/src/components/` - Reusable components
- `frontend/src/lib/` - API client and utilities

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Backend: Edit files in `backend/src/`
   - Frontend: Edit files in `frontend/src/`

3. **Test your changes**
   ```bash
   # Backend tests
   cd backend
   pytest tests/

   # Frontend tests
   cd frontend
   npm test
   ```

4. **Build and verify**
   ```bash
   # Build frontend
   cd frontend
   npm run build

   # Run full app
   cd ..
   python run.py
   ```

5. **Commit and push**
   ```bash
   git add .
   git commit -m "feat: your feature description"
   git push origin feature/your-feature-name
   ```

## Code Style

### Python (Backend)
- Follow PEP 8
- Use type hints
- Keep functions focused and small
- Add docstrings for public functions

### TypeScript (Frontend)
- Use TypeScript for all new code
- Follow React best practices
- Use functional components with hooks
- Keep components focused and reusable

## Adding New Features

### Backend API Endpoint

1. Add route in `backend/src/api/routes.py`
2. Add Pydantic models in `backend/src/api/models.py`
3. Implement logic in appropriate `backend/src/` module
4. Update API documentation

### Frontend Page/Component

1. Create component in `frontend/src/components/` or page in `frontend/src/pages/`
2. Add route if needed in `frontend/src/App.tsx`
3. Connect to backend via `frontend/src/lib/api.ts`
4. Style with Tailwind CSS

## Environment Variables

Add new environment variables in:
1. `.env.example` (template)
2. `backend/config.py` (with defaults)
3. Document in README.md

## Testing

### Backend
```bash
cd backend
pytest tests/ -v
```

### Frontend
```bash
cd frontend
npm test
npm run type-check
```

## Deployment

### Docker

```bash
# Build and run
cd backend
docker-compose up --build

# Production build
docker build -t vtu-diary .
docker run -p 5000:5000 --env-file .env vtu-diary
```

## Common Tasks

### Update Python dependencies
```bash
cd backend
pip install <package>
pip freeze > requirements.txt
```

### Update npm dependencies
```bash
cd frontend
npm install <package>
npm update
```

### Database migrations
```bash
cd backend
# Add migration logic here
```

### Update AI prompts
Edit `backend/system_prompts/god_mode_system.txt`

## Getting Help

- Check [README.md](README.md) for setup instructions
- Review [backend/README.md](backend/README.md) for backend details
- Open an issue for bugs or feature requests

## License

MIT
