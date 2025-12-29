# Kamiwaza-MLX 📦

A simple openai (chat.completions) compatible mlx server that:
- Supports both vision models (via flag or model name detection) and text-only models
- Supports streaming boolean flag
- Has a --strip-thinking which will remove <think></think> tag (in both streaming and not) - good for backwards compat
- Supports usage to the client in openai style
- Prints usage on the server side output
- Appears to deliver reasonably good performance across all paths (streaming/not, vision/not)
- Has a terminal client that works with the server, which also support syntax like `image:/Users/matt/path/to/image.png Describe this image in detail`
- Experimental multi-node execution via `mlx.distributed` when `PAIRED_HOST` is provided

Tested largely with Qwen2.5-VL and Qwen3 models

**Note:** Not specific to Kamiwaza (that is, you can use on any Mac, Kamiwaza not required)
```bash
pip install kamiwaza-mlx

# start the server
a) python -m kamiwaza_mlx.server -m ./path/to/model --port 18000
# or, if you enabled the optional entry-points during install
b) kamiwaza-mlx-server -m ./path/to/model --port 18000

# chat from another terminal (note: specify --host to match server port)
python -m kamiwaza_mlx.infer --host localhost:18000 -p "Say hello"
```

The remainder of this README documents the original features in more detail.

# MLX-LM 🦙 — Drop-in OpenAI-style API for any local MLX model

A FastAPI micro-server (server.py) that speaks the OpenAI
`/v1/chat/completions` dialect, plus a tiny CLI client
(`infer.py`) for quick experiments.
Ideal for poking at huge models like Dracarys-72B on an
M4-Max/Studio, hacking on prompts, or piping the output straight into
other tools that already understand the OpenAI schema.

---

## ✨ Highlight reel

| Feature | Details |
|---------|---------|
| 🔌 OpenAI compatible | Same request / response JSON (streaming too) – just change the base-URL. |
| 📦 Zero-config | Point at a local folder or HuggingFace repo (`-m /path/to/model`). |
| 🖼️ Vision-ready | Accepts `{"type":"image_url", …}` parts & base64 URLs – works with Qwen-VL & friends. |
| 🎥 Video-aware | Auto-extracts N key-frames with ffmpeg and feeds them as images. |
| 🧮 Usage metrics | Prompt / completion tokens + tokens-per-second in every response. |
| ⚙️ CLI playground | `infer.py` gives you a REPL with reset (Ctrl-N), verbose mode, max-token flag… |

---

## 🚀 Running the server

```bash
# minimal
python server.py -m /var/tmp/models/mlx-community/Dracarys2-72B-Instruct-4bit

# custom port / host
python server.py -m ./Qwen2.5-VL-72B-Instruct-6bit --host 0.0.0.0 --port 12345
```
Default host/port: `0.0.0.0:18000`

### Most useful flags:

| Flag | Default | What it does |
|------|---------|--------------|
| `-m / --model` | `mlx-community/Qwen2-VL-2B-Instruct-4bit` | Path or HF repo. |
| `--host` | `0.0.0.0` | Network interface to bind to. |
| `--port` | `18000` | TCP port to listen on. |
| `-V / --vision` | off | Force vision pipeline; otherwise auto-detect. |
| `--strip-thinking` | off | Removes `<think>…</think>` blocks from model output. |
| `--enable-prefix-caching` | `True` | Enable automatic prompt caching for text-only models. If enabled, the server attempts to load a cache from a model-specific file in `--prompt-cache-dir`. If not found, it creates one from the first processed prompt and saves it. |
| `--prompt-cache-dir` | `./.cache/mlx_prompt_caches/` | Directory to store/load automatic prompt cache files. Cache filenames are derived from the model name. |

---

### Experimental multi-node via `mlx.distributed`

The server can bootstrap a two-node mesh using `mlx.distributed`. Set a rendezvous host via `PAIRED_HOST` (optionally in a `.env` file) and launch each node with matching ranks/world-size. The helper will automatically read `.env` files passed via `--distributed-env-file` or located beside the server script.

```bash
# shared settings (either export or place in .env)
PAIRED_HOST=10.0.0.2
PAIRED_PORT=17863
WORLD_SIZE=2

# leader node (rank 0 hosts FastAPI)
RANK=0 python -m kamiwaza_mlx.server --distributed-env-file .env -m ./model

# worker node (rank 1 participates in mlx.distributed but does not bind HTTP)
RANK=1 python -m kamiwaza_mlx.server --distributed-env-file .env -m ./model
```

Useful knobs:

- `--distributed` – force-enable/disable distributed mode (auto when `PAIRED_HOST` or `WORLD_SIZE>1`).
- `--distributed-rank` / `--distributed-world-size` – override `RANK`/`WORLD_SIZE` env vars.
- `--distributed-host` / `--distributed-port` – override `PAIRED_HOST` / `PAIRED_PORT`.
- `--distributed-server-rank` – choose which rank should host the HTTP server (defaults to 0).

Non-leader ranks simply keep the MLX runtime alive for collective ops once the model weights are synchronized.

---

## 💬 Talking to it with the CLI

```bash
python kamiwaza_mlx/infer.py --host localhost:18000 --max_new_tokens 2048
```

### Interactive keys
- Ctrl-N: reset conversation
- Ctrl-C: quit

---

## 🌐 HTTP API

GET `/v1/models`

Returns a list with the currently loaded model:

```json
{
  "object": "list",
  "data": [
    {
      "id": "Dracarys2-72B-Instruct-4bit",
      "object": "model",
      "created": 1727389042,
      "owned_by": "kamiwaza"
    }
  ]
}
```
The `created` field is set when the server starts and mirrors the OpenAI API's timestamp.

POST `/v1/chat/completions`

```json
{
  "model": "Dracarys2-72B-Instruct-4bit",
  "messages": [
    { "role": "user",
      "content": [
        { "type": "text", "text": "Describe this image." },
        { "type": "image_url",
          "image_url": { "url": "data:image/jpeg;base64,..." } }
      ]
    }
  ],
  "max_tokens": 512,
  "stream": false
}
```

Response (truncated):

```json
{
  "id": "chatcmpl-d4c5…",
  "object": "chat.completion",
  "created": 1715242800,
  "model": "Dracarys2-72B-Instruct-4bit",
  "choices": [
    {
      "index": 0,
      "message": { "role": "assistant", "content": "The image shows…" },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 143,
    "completion_tokens": 87,
    "total_tokens": 230,
    "tokens_per_second": 32.1
  }
}
```

Add `"stream": true` and you'll get Server-Sent Events chunks followed by
`data: [DONE]`.

**System Prefix Caching (Text-Only Models):**
- Purpose: Dramatically speed up repeated queries that share the same system context (e.g., large document in `role: system`). The server caches only the system message(s), not the whole prompt, so subsequent turns process only new user tokens.
- Flags:
  - `--enable-prefix-caching` (default `True`)
  - `--prompt-cache-dir` (default `./.cache/mlx_prompt_caches/`)
- How it works (high‑level):
  1) On first request with a system message, the server builds a KV cache for just the system portion and saves three files under `--prompt-cache-dir`:
     - `<model>.safetensors` (KV), `<model>.safetensors.len` (token count), `<model>.safetensors.hash` (SHA256 over token IDs)
  2) On subsequent requests with the same system text (hash matches), the server deep‑copies the cached KV and processes only new user/assistant tokens.
  3) If the system message changes, the old cache is discarded and replaced automatically.
- Example: A 10,000‑token system document is processed once; later questions only process the user tokens.
- Notes: text‑only models; fully transparent to clients (no special fields needed).

**Conversation KV Caching (Long chats, fast follow‑ups):**
- Rationale: For whole conversations, we reuse KV across turns and tokenize only the tail. We also honor message boundaries so rollbacks (dropping a turn) are fast: we trim to the prior boundary and continue.
- Enabling & behavior:
  - Conversation KV cache is on by default. Provide a `conversation` or `conversation_id` in the request body (or `X-Conversation-Id` header). If omitted, auto‑ID binds by client IP.
  - The server returns headers for every request (JSON & SSE):
    - `X-Conv-Id` (resolved ID), `X-Conv-KV` (`fresh|hit|snapshot|none|disabled`), `X-Conv-Cached-Tokens`, `X-Conv-Processing-Tokens`.
  - Non‑stream JSON also includes `usage.input_tokens_details.cached_tokens` and `metadata.conversation_id`.
  - Default capacity: `--conversation-kv-max-tokens 131072` (128k; clamped to model context if detected). Snapshots: `--conversation-snapshots 1`.
- Save/Load (manual only):
  - Save a conversation KV & metadata for later: `POST /v1/conv_kv/save` with `{conversation|conversation_id, title?}`.
  - Load it back into memory: `POST /v1/conv_kv/load` with `{conversation|conversation_id}`.
  - List/delete saved KV: `GET /v1/conv_kv/stats`, `DELETE /v1/conv_kv/{id}`.
  - Safety: per‑save hard limit (`--conversation-disk-max-gb`, default 200 GiB) and 90% disk occupancy guard.

For a deeper dive (headers, examples, and endpoints), see `kv-cache-dev-guide.md`.

---

## 🛠️ Internals (two-sentence tour)

* **server.py** – loads the model with mlx-vlm, converts incoming
OpenAI vision messages to the model's chat-template, handles images /
video frames, and streams tokens back. For text-only models, if enabled via server flags, it automatically manages a system message cache to speed up processing when multiple queries reference the same system context.
* **infer.py** – lightweight REPL that keeps conversation context and
shows latency / TPS stats.

That's it – drop it in front of any MLX model and start chatting!
