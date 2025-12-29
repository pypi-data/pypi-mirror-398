#!/usr/bin/env python3
"""
See top-level `infer.py` – this is the exact same code, bundled inside the
`kamiwaza_mlx` package so that it can be launched with:

    python -m kamiwaza_mlx.infer -p "hello"

The implementation below is kept byte-for-byte identical (bar this docstring)
so maintenance remains single-source. Any improvements should be applied to
both copies or refactored into a shared module.
"""

# NOTE: The full file is inlined here to avoid an extra runtime import hop. The
# original licence header / comments are preserved.

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from typing import Any, Dict, Generator, List, Optional

import requests
from pydantic import BaseModel, Field

# ────────────────────────── constants ────────────────────────────
STREAM_PREFIX       = "data: "
TAG                 = "image:"
DEFAULT_MAX_TOKENS  = 4096

# ────────────────── pydantic (request/response) ──────────────────
class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    images: Optional[List[str]] = None
    max_new_tokens: Optional[int] = None
    temperature: float = 0.7
    stream: bool = True

class ChatCompletionUsage(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int
    tokens_per_second: float
    input_tokens_details: Dict[str, Any]
    output_tokens_details: Dict[str, Any]

# ───────────────────────── helpers ───────────────────────────────

def system_prompt() -> Message:
    return Message(
        role="system",
        content=(
            "You are an elite coding assistant. Think step-by-step, ask for "
            "clarification when needed, and always follow the user's explicit "
            "instructions."
        ),
    )

_IMG_RE = re.compile(r"image:\s*(?:\"([^\"]+)\"|'([^']+)'|(\S+))")


def extract_image(line: str) -> tuple[str, Optional[str]]:
    """Detect image:<path> syntax and return text + optional image path."""
    if TAG not in line:
        return line.strip(), None

    m = _IMG_RE.search(line)
    if not m:
        return line.strip(), None

    path = next(g for g in m.groups() if g)
    img = pathlib.Path(path).expanduser()
    if not img.exists():
        raise FileNotFoundError(img)

    cleaned = (line[: m.start()] + line[m.end() :]).strip()
    if "<image>" not in cleaned:
        cleaned = (cleaned + " <image>").strip() if cleaned else "<image>"
    return cleaned, str(img)


def sse_chunks(resp: requests.Response) -> Generator[str, None, None]:
    """Yield content chunks from server-sent-events."""
    for raw in resp.iter_lines(chunk_size=1, decode_unicode=True):
        if not raw or not raw.startswith(STREAM_PREFIX):
            continue
        payload = raw[len(STREAM_PREFIX) :].strip()
        if payload == "[DONE]":
            break
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            continue
        delta = data.get("choices", [{}])[0].get("delta", {})
        if "content" in delta:
            yield delta["content"]


def request_and_print(endpoint: str, req: ChatCompletionRequest, *, plain_stdout: bool) -> None:
    """Helper that POSTs the request to the server and pretty-prints the reply."""
    try:
        resp = requests.post(endpoint, json=req.model_dump(), stream=req.stream)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"⚠️  Request failed: {e}", file=sys.stderr)
        return

    if req.stream:
        if not plain_stdout:
            print("Assistant: ", end="", flush=True)
        for chunk in sse_chunks(resp):
            print(chunk, end="", flush=True)
        print()
    else:
        answer = resp.json()["choices"][0]["message"]["content"]
        if plain_stdout:
            print(answer)
        else:
            print(f"Assistant: {answer}")


# ─────────────────────────── main ────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="Interactive CLI for the MLX chat server")
    ap.add_argument("--host", default="localhost:8000", help="server host:port (default: localhost:8000)")
    ap.add_argument("--model", default="model", help="model name to send")
    ap.add_argument("--max_new_tokens", type=int, help="override server default (omit → server decides)")
    ap.add_argument("-n", "--no-stream", action="store_true", help="disable streaming mode")
    ap.add_argument("-p", "--prompt", help="one-shot prompt (non-interactive mode)")
    args = ap.parse_args()

    endpoint = f"http://{args.host}/v1/chat/completions"

    # ─────────── one-shot / non-interactive mode ───────────
    if args.prompt is not None:
        try:
            text, img_path = extract_image(args.prompt)
        except FileNotFoundError as e:
            print(f"⚠️  Image not found: {e}", file=sys.stderr)
            sys.exit(1)

        if not text and img_path is None:
            sys.exit(0)

        req = ChatCompletionRequest(
            model=args.model,
            messages=[system_prompt(), Message(role="user", content=text or "<image>")],
            images=[img_path] if img_path else None,
            max_new_tokens=args.max_new_tokens,
            stream=not args.no_stream,
        )
        request_and_print(endpoint, req, plain_stdout=True)
        sys.exit(0)

    # ───────────────────── interactive mode ─────────────────────
    messages: List[Message] = [system_prompt()]

    print("Tip: prepend  image:/path/to/file.jpg  inside a prompt to attach an image.")
    print("Enter your prompt (type Ctrl-N to reset, Ctrl-C to quit).\n")

    while True:
        try:
            line = input("> ")
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if line.lower() == "ctrl-n":
            messages = [system_prompt()]
            print("Conversation reset.\n")
            continue

        try:
            text, img_path = extract_image(line)
        except FileNotFoundError as e:
            print(f"⚠️  Image not found: {e}", file=sys.stderr)
            continue

        if not text and img_path is None:
            print("⚠️  Empty prompt ignored.", file=sys.stderr)
            continue

        messages.append(Message(role="user", content=text or "<image>"))

        req = ChatCompletionRequest(
            model=args.model,
            messages=messages,
            images=[img_path] if img_path else None,
            max_new_tokens=args.max_new_tokens,
            stream=not args.no_stream,
        )

        request_and_print(endpoint, req, plain_stdout=False)

        if not req.stream:
            data = requests.post(endpoint, json=req.model_dump()).json()
            answer = data["choices"][0]["message"]["content"]
            messages.append(Message(role="assistant", content=answer.strip()))


# ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main() 
