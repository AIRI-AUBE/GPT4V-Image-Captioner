# GPT4V-Image-Captioner

A Gradio-based image captioning and dataset tooling app that works with multiple vision-language providers:
- OpenAI GPT-4o (Vision)
- Google Vertex AI (Gemini via Vertex)
- Google Gemini (via google-generativeai)
- Alibaba Qwen-VL (DashScope)
- Optional local backends (Moondream, CogVLM, MiniCPM)

It supports single-image captioning, batch captioning to sidecar .txt files, optional image pre-processing, watermark detection, rule-based image classification, tag analysis/clean-up (word cloud, co-occurrence network), and simple image segmentation.

## Quick start (one click on Windows)

- Double-click `start.ps1` (or run the two lines below in PowerShell if execution policy blocks scripts):

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\start.ps1
```

This will:
- Create a virtual environment `.venv`
- Install minimal dependencies from `requirements.txt`
- Launch the Gradio UI in your default browser at http://127.0.0.1:8848

Want all optional features (tag visualization, local model helpers, provider SDKs)? Install extras as well:

```powershell
.\start.ps1 -Full
```

You can pass through server flags as needed:
- `-Port 8848` choose another port
- `-Listen` bind to 0.0.0.0 (allow LAN access)
- `-Share` enable Gradio share link
- `-NoBrowser` do not auto-open the browser

Example:
```powershell
.\start.ps1 -Full -Port 9000 -Listen -NoBrowser
```

## How it works (step by step)

1) UI + persistence
- The app UI is defined in `gpt-caption.py` using Gradio Blocks.
- API settings are saved in `api_settings.json` the first time you run a provider.

2) Providers and where to put credentials
- OpenAI (GPT-4o):
  - API Key: your OpenAI key
  - API URL: keep default `https://api.openai.com/v1/chat/completions`
  - Model: e.g. `gpt-4o` or `gpt-4o-mini`
- Anthropic Claude (optional):
  - API Key: your Claude key
  - API URL: `https://api.anthropic.com/v1/messages`
  - Model: e.g. `claude-3.5-sonnet`
- Google Gemini (non-Vertex):
  - API Key: your Gemini API key
  - API URL: any string containing `gemini` (auto-detected)
  - Model: e.g. `gemini-1.5-pro` or `gemini-1.5-flash-latest`
- Alibaba Qwen-VL:
  - API Key: your DashScope key
  - API URL: `https://dashscope.aliyuncs.com/v1/services/aigc/multimodal-generation/generation`
  - Model: choose from the dropdown (e.g., `qwen-vl-plus`, `qwen-vl-max`)
- Google Vertex AI (Gemini on Vertex):
  - API Key field: path to your Service Account JSON (file on disk)
  - API URL field: your Google Cloud Project ID (e.g., `my-project-123456`)
  - Model: `gemini-2.0-flash-exp` by default (change if needed)
  - You can also save this config via the "Vertex AI Configuration" accordion in the UI.
    - Tip: Copy `service_account.json.templete` to `service_account.json` (repo root) and fill it with your real values. The real JSON file is ignored by git. `start.ps1` will automatically set `GOOGLE_APPLICATION_CREDENTIALS` and try to export `GOOGLE_CLOUD_PROJECT` from that file. In the UI, you can simply set Project ID or even use the sentinel `vertex-ai` value in the API URL box to rely on auto-detection.

3) Choosing the backend at runtime
- Use the "Choose API / 选择API" dropdown and click "Switch".
- For cloud providers, your request is sent directly to that provider’s HTTP API (no extra server required).
- For local models (Moondream / CogVLM / MiniCPM), the app will start an internal FastAPI server (`openai_api.py`) on `http://127.0.0.1:8000` and route requests to it.

4) Captioning workflow
- Single Image tab: upload one image and click "Caption Single Image".
- Batch Image tab: point to a folder. The app writes one `.txt` next to each image, with overwrite/append/prepend/skip policy.
- Prompt can include `{path\\to\\captions\\}` to inject extra tags from sidecar `.txt` files named the same as the image.
- Quality controls influence image resizing for some providers.

5) Extra tools
- Image Zip: pre-resize/normalize images for faster labeling.
- Watermark Detection: move/copy images likely containing watermarks to a target folder.
- Image filtering: rule-based classification into subfolders.
- Image Segmentation: split each image into a grid and save parts.
- Tag Manage: analyze, clean up and visualize tags (requires optional dependencies).

## Install (manual)

If you prefer to set up manually instead of using `start.ps1`:

```powershell
# From the repository root
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
# Optional features
pip install -r requirements-optional.txt

# Run the app
python gpt-caption.py --port 8848
```

Notes for optional/local models:
- PyTorch installation depends on your CUDA/CPU. For best results, follow https://pytorch.org/get-started/locally/ and install a matching `torch` and `torchvision` version before `requirements-optional.txt`.
- Hugging Face model downloads are large (20–40GB+). Ensure adequate disk and VRAM (see UI notes in "Local Model" accordion).

## Deploy

- Local network (LAN):
  - Start with `--listen` to bind `0.0.0.0`, then open the chosen port on your firewall.
  - Example: `python gpt-caption.py --listen --port 8848 --no-browser`
- Public internet (quick demo):
  - Use `--share` to get a temporary Gradio URL. Not recommended for production.
- Reverse proxy (recommended for persistent access):
  - Put Nginx/Caddy/IIS/Traefik in front of the app, proxying to `http://127.0.0.1:8848`.
  - Consider enabling HTTPS and basic auth at the proxy.

## Troubleshooting

- PowerShell cannot run scripts
  - Run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force`
- `google.genai` or `google.generativeai` import errors
  - Install extras: `pip install -r requirements-optional.txt` or `pip install google-genai google-generativeai`
- Qwen (DashScope) import error
  - Install: `pip install dashscope`
- Tag visualization errors (matplotlib/networkx/wordcloud)
  - Install extras: `pip install -r requirements-optional.txt`
- Torch or CUDA errors
  - Install the right PyTorch build for your CUDA/CPU from pytorch.org, then reinstall `requirements-optional.txt`.
- Large model downloads are slow
  - Use a mirror (see `downloader` UI option with `CN` acceleration) or ensure a stable connection.

## Repository map (entry points)
- `gpt-caption.py` – main Gradio app
- `lib/Api_Utils.py` – provider routing, retries, settings persistence
- `openai_api.py` – local FastAPI wrapper for certain backends
- `vertex_api.py` – Vertex AI client integration
- `lib/*` – image processing, prompts, tag processing, helper utilities

## License
This project includes third-party models and libraries under their respective licenses. Review the licenses before commercial use.
