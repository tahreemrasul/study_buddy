from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ADK_BASE = "http://127.0.0.1:8000"

@app.post("/apps/{path:path}")
async def proxy_post(path: str, request: Request):
    body = await request.body()
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