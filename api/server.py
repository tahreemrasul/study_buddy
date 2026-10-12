import base64
import io
import json

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import httpx
from pypdf import PdfReader

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ADK_BASE = "http://127.0.0.1:8000"

# Max characters of PDF text placed in session state (it is injected into several agent prompts)
MAX_SOURCE_CHARS = 100_000


def pdf_to_state(name: str, data_b64: str) -> dict:
    """Extract a PDF's text with pypdf and return it as initial session state.

    Sub-agents read this state through {source_material?} in their prompts.
    """
    def error_state(message: str) -> dict:
        return {
            "source_error": message,
            "source_note": (
                f"The user attached '{name}', but it could not be read. Tell the user, then "
                "continue with the topic they gave. If they gave no topic, ask them for one."
            ),
        }

    try:
        reader = PdfReader(io.BytesIO(base64.b64decode(data_b64)))
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception as e:
        return error_state(f"Could not read {name} ({type(e).__name__})")

    if not text:
        return error_state(f"No extractable text in {name} (scanned PDF?)")

    truncated = len(text) > MAX_SOURCE_CHARS
    return {
        "source_name": name,
        "source_material": text[:MAX_SOURCE_CHARS],
        "source_truncated": truncated,
        "source_note": (
            f"The user attached a document named '{name}'. Its text is already available "
            "to every sub-agent, so do not paste it into tool requests. "
            "If the user gave no explicit topic, use the document's main subject as the topic."
        ),
    }


@app.post("/apps/{path:path}")
async def proxy_post(path: str, request: Request):
    body = await request.body()

    # Session creation may carry a PDF: parse it here and create the ADK session
    # with the text already in state, so it never enters the conversation.
    # (ADK's create-session endpoint takes the whole JSON body as the initial state.)
    if body:
        payload = json.loads(body)
        source_pdf = payload.pop("source_pdf", None)
        if source_pdf:
            payload.update(pdf_to_state(source_pdf.get("name", "uploaded document"), source_pdf["data"]))
            body = json.dumps(payload).encode()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ADK_BASE}/apps/{path}",
            content=body,
            headers={"Content-Type": "application/json"},
        )
    return response.json()

@app.post("/run_sse")
async def proxy_sse(request: Request):
    body = await request.body()

    async def stream():
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=10.0,
                    read=600.0,
                    write=10.0,
                    pool=10.0
                )
            ) as client:
                async with client.stream(
                    "POST",
                    f"{ADK_BASE}/run_sse",
                    content=body,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    async for chunk in response.aiter_text():
                        yield chunk
        except Exception as e:
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )