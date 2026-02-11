# Deployment Guide

This project is optimized for a hybrid deployment: **Frontend on Vercel** and **Backend on Render/Railway** (or any Docker-supporting host).

## 🚀 Frontend (Vercel)

The frontend is a React + Vite application. It is ready to be deployed to Vercel.

1. **Connect Repository**: Connect your GitHub repository to Vercel.
2. **Framework Preset**: Select **Vite**.
3. **Root Directory**: Select `frontend/` (or keep root and let `vercel.json` handle it).
4. **Environment Variables**:
   - `VITE_API_URL`: Your backend URL (e.g., `https://your-backend.onrender.com`). If not set, it defaults to `/api` (which assumes a proxy or monolithic setup).

## 🛠️ Backend (Render / Docker)

The backend is a FastAPI application with heavy dependencies (Playwright, Selenium, Torch, OpenCV). It **cannot** run on Vercel Serverless Functions.

### Using Render (Recommended)
1. Use the provided `render.yaml` to create a new Blueprint service.
2. Render will automatically detect the `Dockerfile` and deploy it.

### Manual Docker Deployment
```bash
docker build -t vtu-backend .
docker run -p 5000:5000 --env-file .env vtu-backend
```

## 🏗️ Monolithic Deployment (Single VPS)

If you are deploying to a single VPS (like DigitalOcean or AWS EC2):
1. Build the frontend locally: `cd frontend && npm run build`.
2. The build output will be moved to `backend/static`.
3. Run the FastAPI app: `python app.py`. It will serve both the API and the React frontend.
