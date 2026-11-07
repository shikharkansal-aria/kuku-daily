"""One LLM entry point. Swap models with env vars only (see .env.example).

LLM_PROVIDER: openai (any OpenAI-compatible URL: Groq, Gemini, OpenAI, Ollama, Kuku's own) | anthropic | mock
LLM_MODEL, OPENAI_BASE_URL, OPENAI_API_KEY, ANTHROPIC_API_KEY. LLM_CACHE=0 disables the disk cache.
"""
import contextvars
import hashlib
import json
import os
import re
import time
from contextlib import contextmanager
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:  # dotenv is optional at runtime
    pass

CACHE = Path(__file__).resolve().parent.parent / ".cache" / "llm"
CALLS = {"live": 0, "cached": 0, "in_tokens": 0, "out_tokens": 0}  # tokens: live calls only
MOCKS = {}  # task name -> fn(prompt) -> str, registered by callers for offline tests
_OVR = contextvars.ContextVar("llm_override", default={})  # per-session settings; never touch os.environ


@contextmanager
def use(**cfg):
    """Per-session override, e.g. a key typed in the app sidebar, so one visitor's key never leaks to another."""
    tok = _OVR.set({k: v for k, v in cfg.items() if v})
    try:
        yield
    finally:
        _OVR.reset(tok)


def _get(k, default=""):
    return _OVR.get().get(k) or os.getenv(k, default)


def settings():
    return {k: _get(k) for k in ("LLM_PROVIDER", "LLM_MODEL", "OPENAI_BASE_URL")}  # no keys: this gets logged


def _call(system, prompt, want_json, temperature):
    provider = _get("LLM_PROVIDER", "mock")
    model = _get("LLM_MODEL")
    if provider == "anthropic":
        import anthropic
        r = anthropic.Anthropic(api_key=_get("ANTHROPIC_API_KEY") or None).messages.create(
            model=model, max_tokens=2000, temperature=temperature,
            system=system or "", messages=[{"role": "user", "content": prompt}])
        CALLS["in_tokens"] += r.usage.input_tokens
        CALLS["out_tokens"] += r.usage.output_tokens
        return r.content[0].text
    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=_get("OPENAI_API_KEY") or None, base_url=_get("OPENAI_BASE_URL") or None, timeout=60, max_retries=1)
        msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        kw = {"response_format": {"type": "json_object"}} if want_json else {}
        try:
            r = client.chat.completions.create(model=model, messages=msgs, temperature=temperature, **kw)
        except Exception as e:  # some endpoints reject response_format; retry once without it
            if not kw or "response_format" not in str(e):
                raise
            r = client.chat.completions.create(model=model, messages=msgs, temperature=temperature)
        if r.usage:
            CALLS["in_tokens"] += r.usage.prompt_tokens or 0
            CALLS["out_tokens"] += r.usage.completion_tokens or 0
        return r.choices[0].message.content
    raise ValueError(f"unknown LLM_PROVIDER {provider!r}")


def parse_json(text):
    m = re.search(r"\{.*\}|\[.*\]", text or "", re.S)
    if not m:
        raise ValueError("no JSON found")
    return json.loads(m.group(0))


def complete(prompt, system=None, want_json=False, task="general", temperature=0.4):
    """Return text (or parsed JSON when want_json). Retries rate limits; one JSON repair pass."""
    if _get("LLM_PROVIDER", "mock") == "mock":
        out = MOCKS[task](prompt)
        return parse_json(out) if want_json else out
    key = hashlib.sha256(json.dumps([settings(), system, prompt, want_json]).encode()).hexdigest()[:24]
    path = CACHE / f"{task}-{key}.txt"
    if os.getenv("LLM_CACHE", "1") != "0" and path.exists():
        CALLS["cached"] += 1
        out = path.read_text()
    else:
        for attempt in range(6):
            try:
                out = _call(system, prompt, want_json, temperature)
                break
            except Exception as e:
                if attempt == 5 or not re.search(r"429|rate|overload|503|timeout", str(e), re.I):
                    raise
                time.sleep(min(65, 5 * 2 ** attempt))  # free tiers reset per minute
        CALLS["live"] += 1
        CACHE.mkdir(parents=True, exist_ok=True)
        path.write_text(out)
    if not want_json:
        return out
    try:
        return parse_json(out)
    except (ValueError, json.JSONDecodeError):
        fixed = _call("Return only valid JSON. No prose.", f"Fix this into valid JSON:\n{out}", True, 0)
        path.write_text(fixed)
        return parse_json(fixed)
