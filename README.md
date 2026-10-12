# study_buddy

Enter a topic and get a generated study guide plus Q&A, produced by a pipeline of Google ADK agents
(topic overview → search queries → search → outline → study guide → Q&A).

## Architecture

| Component | Location | Port | Role |
|-----------|----------|------|------|
| ADK agent server | `api/study_guide/` | 8000 | Runs the agent pipeline (`adk api_server`) |
| CORS proxy | `api/server.py` | 8001 | FastAPI proxy that adds CORS headers and streams SSE from the ADK server |
| Frontend | `web/` | 3000 | Next.js UI; talks to the proxy at `http://localhost:8001` |

## Prerequisites

- Conda (with Python 3.x) and Node.js / npm
- A Google Cloud project with Vertex AI enabled, and the gcloud CLI

### One-time setup

```bash
# Python environment
conda create -n study_buddy python=3.11
conda activate study_buddy
pip install -r api/requirements.txt

# Google Cloud credentials (Vertex AI)
gcloud auth application-default login

# Frontend dependencies
cd web && npm install
```

Create `api/.env`:

```
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=<your-gcp-project-id>
GOOGLE_CLOUD_LOCATION=<region, e.g. global or us-central1>
MODEL=<model name>
```

## Running

Use three terminals, starting from the repo root:

**Terminal 1: ADK agent server (port 8000)**
```bash
cd api
conda activate study_buddy
adk api_server
```

**Terminal 2: CORS proxy (port 8001)**
```bash
cd api
conda activate study_buddy
uvicorn server:app --port 8001 --reload
```

**Terminal 3: Next.js frontend (port 3000)**
```bash
cd web
npm run dev
```

Then open http://localhost:3000.

### Quick health check

```bash
curl localhost:8000/list-apps   # should print ["study_guide"]
curl -o /dev/null -w "%{http_code}\n" localhost:8001/docs   # 200
```

A full run of the pipeline takes about 1–2 minutes per topic.
