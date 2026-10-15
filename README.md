# study_buddy

Enter a topic and/or attach a PDF and get a generated study guide plus Q&A, produced by a pipeline of Google ADK agents
(topic overview → search queries → search → outline → study guide → Q&A).

When a PDF is attached, it becomes the primary source. The proxy extracts its text with `pypdf` and creates the ADK
session with that text already in state (`source_material`), so the document never enters the conversation.
The overview, query, outline and study guide agents read it through `{source_material?}` in their prompts,
and web search only fills gaps.

## Workshop notebook

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/tahreemrasul/study_buddy/blob/main/workshop/study_buddy_workshop.ipynb)

[`workshop/study_buddy_workshop.ipynb`](workshop/study_buddy_workshop.ipynb) builds the backend agents step by step in Colab,
from a single root agent to the full grounded pipeline served with `adk api_server`. It only needs a Gemini API key
from Google AI Studio. The sample PDF it uses lives in `workshop/data/`.

## Architecture

| Component | Location | Port | Role |
|-----------|----------|------|------|
| ADK agent server | `api/study_guide/` | 8000 | Runs the agent pipeline (`adk api_server`) |
| CORS proxy | `api/server.py` | 8001 | FastAPI proxy that adds CORS headers, streams SSE from the ADK server, and parses uploaded PDFs into session state |
| Frontend | `web/` | 3000 | Next.js UI; talks to the proxy at `http://localhost:8001` |

## Prerequisites

- Conda (with Python 3.x) and Node.js / npm
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

### One-time setup

```bash
# Python environment
conda create -n study_buddy python=3.11
conda activate study_buddy
pip install -r api/requirements.txt

# Frontend dependencies
cd web && npm install
```

Create `api/.env`:

```
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GEMINI_API_KEY=<your-ai-studio-api-key>
```

The model is set in `api/study_guide/config/config.py` (`MODEL = "gemini-3.8-flash"`).

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

A full run of the pipeline takes about 1.5–3 minutes.

## Using a PDF

Click **+ Attach PDF** next to **Generate guide** (PDF only, up to 10 MB). You can attach a PDF on its own or together with a topic.
The Progress tab shows a **Source** card, and the study guide's Resources section lists the document first.

- Only the PDF's text layer is used: scanned PDFs have none and are reported as "No extractable text".
- Text beyond 100,000 characters is cut off (`MAX_SOURCE_CHARS` in `api/server.py`); the Source card says "truncated" when this happens.
