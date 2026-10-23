"""Doctor Assistant - local image-analysis chatbot powered by Ollama (Qwen-VL).

Run:
    uvicorn backend.app:app --reload --port 8000
"""

import json
import os
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5vl:3b")
STATIC_DIR = Path(__file__).resolve().parent.parent / "frontend"

SYSTEM_PROMPT = """You are an experienced clinical decision-support assistant talking to a physician.
The physician gives you medical images (X-ray, CT, MRI, dermatology photo, ECG, etc.) and patient information.

Your task:
1. Carefully examine the image and describe the findings you observe.
2. Based on the findings and patient information, list possible differential diagnoses in order of likelihood.
3. Suggest additional tests that could help clarify the diagnosis.
4. Suggest possible treatment approaches found in the literature and clinical guidelines.
5. If there is any emergency (red-flag) finding, state it clearly at the very top.

Answer in English using these headings:
## Image Findings
## Possible Differential Diagnoses
## Recommended Further Tests
## Possible Treatment Approaches
## Points of Caution

Rules:
- Clearly mark anything you're unsure about as "uncertain" — never make things up.
- If image quality is insufficient or the image isn't medical, say so.
- The final decision always belongs to the physician; you only provide support.
- For follow-up questions, take the prior conversation and image into account."""

app = FastAPI(title="Doctor Assistant")


class Message(BaseModel):
    role: str
    content: str
    images: list[str] | None = None  # base64 (without the data: prefix)


class ChatRequest(BaseModel):
    messages: list[Message]
    model: str | None = None


@app.get("/api/health")
async def health():
    """Check whether Ollama is reachable and the model is available."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{OLLAMA_HOST}/api/tags")
            r.raise_for_status()
            models = [m["name"] for m in r.json().get("models", [])]
    except httpx.HTTPError as e:
        return {"ollama": False, "error": str(e), "model": OLLAMA_MODEL, "models": []}
    return {
        "ollama": True,
        "model": OLLAMA_MODEL,
        "model_available": OLLAMA_MODEL in models,
        "models": models,
    }


@app.post("/api/chat")
async def chat(req: ChatRequest):
    if not req.messages:
        raise HTTPException(400, "Message cannot be empty")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in req.messages:
        msg = {"role": m.role, "content": m.content}
        if m.images:
            msg["images"] = m.images
        messages.append(msg)

    payload = {
        "model": req.model or OLLAMA_MODEL,
        "messages": messages,
        "stream": True,
        # keep_alive: avoid reloading the (large) vision model between requests
        "keep_alive": "30m",
        "options": {
            "temperature": 0.2,
            # repeat_penalty: stops small (3b) models from looping the same sentence
            "repeat_penalty": 1.15,
            "repeat_last_n": 256,
            # num_ctx: smaller context leaves more VRAM for GPU layer offload on small GPUs
            "num_ctx": 2048,
            # num_predict: cap generation length so replies finish faster
            "num_predict": 700,
        },
    }

    async def stream():
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", f"{OLLAMA_HOST}/api/chat", json=payload) as r:
                    if r.status_code != 200:
                        body = (await r.aread()).decode(errors="replace")
                        yield f"\n\n**Error:** Ollama returned {r.status_code}: {body}"
                        return
                    async for line in r.aiter_lines():
                        if not line:
                            continue
                        chunk = json.loads(line)
                        if "error" in chunk:
                            yield f"\n\n**Error:** {chunk['error']}"
                            return
                        yield chunk.get("message", {}).get("content", "")
        except httpx.HTTPError as e:
            yield (
                f"\n\n**Error:** Could not connect to Ollama ({OLLAMA_HOST}). "
                f"Is `ollama serve` running? Details: {e}"
            )

    return StreamingResponse(stream(), media_type="text/plain; charset=utf-8")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")
