# 🩺 Doctor Assistant

A simple web UI + chatbot that analyzes a medical image uploaded by a physician (X-ray, CT, MRI,
dermatology photo, ECG…) using a **locally** running vision-language model (Qwen2.5-VL, via Ollama)
and suggests "this patient might have X, these tests could be ordered, this treatment could be
applied."

No data ever leaves the machine: the model and server run entirely on your own computer.

> ⚠️ This system is for **clinical decision support only**. The diagnosis and treatment decision
> always belong to the physician. It uses a general-purpose model, so outputs can be wrong; it has
> not been validated for clinical use.

## Architecture

```
Browser (frontend/)  ──►  FastAPI (backend/app.py)  ──►  Ollama (localhost:11434)  ──►  qwen2.5vl
   image + patient info        adds the system prompt          streams the response back
```

- `frontend/` — HTML/CSS/JS, no framework. Image upload, patient info, chat screen.
- `backend/app.py` — `/api/chat` (forwards to Ollama, streams the response back) and `/api/health`.
- The assistant's behavior is defined by `SYSTEM_PROMPT` in `backend/app.py`.

## Quick Start (one click)

1. Install [Ollama](https://ollama.com/download) and [Python 3.10+](https://www.python.org/downloads/).
2. In this folder, **Windows:** double-click `start.bat` · **Mac/Linux:** run `./start.sh`.

The script downloads the model (~3 GB the first time), installs packages, and opens
http://localhost:8000 in your browser.

## Manual Setup

### 1. Ollama and the model

```bash
# Install Ollama from https://ollama.com/download, then:
ollama pull qwen2.5vl:3b      # ~3 GB; qwen2.5vl:7b gives better results on a stronger machine
ollama serve                  # not needed if it's already running in the background
```

### 2. Web app

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.app:app --reload --port 8000
```

Open **http://localhost:8000** in your browser.

## Running with Docker

The entire system (Ollama + model + web app) runs inside Docker; the only requirement on your
machine is [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
docker compose up -d --build
```

| Container | Role |
|---|---|
| `ollama` | Runs the vision model (the model is stored in the `ollama-data` volume) |
| `model-pull` | Downloads `qwen2.5vl:3b` on first start (~3 GB), then exits |
| `app` | Web UI + FastAPI, **http://localhost:8000** |

The first start takes a few minutes while the model downloads; follow progress with
`docker compose logs -f model-pull`. Then open **http://localhost:8000** in your browser.

- Stop: `docker compose down` (keeps the model) · Also remove the model: `docker compose down -v`
- Different model: `OLLAMA_MODEL=qwen2.5vl:7b docker compose up -d`
- With an NVIDIA GPU: `docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build`

## Usage

1. Drag and drop the image, or click to select it.
2. Click **Analyze**. The assistant replies under these headings:
   Image Findings · Possible Differential Diagnoses · Recommended Further Tests ·
   Possible Treatment Approaches · Points of Caution
3. Ask follow-up questions in the box below (e.g. "Which antibiotic would you recommend?",
   "Is pneumothorax a possibility?").
4. Click **New Patient** to start over.

## Performance

- Images are downscaled client-side (max 1024px) before upload — large camera/scan photos are the
  single biggest cause of slow responses, and the model gains nothing past that resolution.
- Responses are capped (`num_predict`) and the model is kept loaded (`keep_alive`) between requests
  so it isn't reloaded from disk on every message.
- Response speed is otherwise bound by your GPU's free VRAM: run `ollama ps` to see the CPU/GPU
  split for the loaded model — the more of it sits on CPU, the slower generation will be. Closing
  other GPU-heavy apps, or switching to a smaller/more quantized model, both help.

## Settings

| Environment variable | Default | Description |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Address of the Ollama server |
| `OLLAMA_MODEL` | `qwen2.5vl:3b` | Vision model to use (e.g. `qwen2.5vl:7b`, `llava`, `llama3.2-vision`) |

```bash
OLLAMA_MODEL=qwen2.5vl:3b uvicorn backend.app:app --port 8000
```
