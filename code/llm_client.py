import aiohttp
import os
import json
import asyncio
import logging
import re

logger = logging.getLogger(__name__)

# --- Configuration ---
# Ollama runs locally — no API key needed, no rate limits, no SSL headaches.
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")

# Module-level aiohttp session — created lazily, reused for connection pooling.
_SESSION: aiohttp.ClientSession | None = None

async def _get_session() -> aiohttp.ClientSession:
    global _SESSION
    if _SESSION is None or _SESSION.closed:
        timeout = aiohttp.ClientTimeout(total=600)  # Local LLM can be slow on large prompts
        _SESSION = aiohttp.ClientSession(timeout=timeout)
    return _SESSION

async def close_session():
    """Call at shutdown to cleanly close the shared session."""
    global _SESSION
    if _SESSION and not _SESSION.closed:
        await _SESSION.close()
        _SESSION = None

def _extract_json(text: str) -> str:
    """Robustly extract a JSON object from potentially wrapped LLM output."""
    text = text.strip()
    # Strip markdown fences
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```\s*$', '', text)
    text = text.strip()
    # Find the outermost { ... }
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    return text

async def call_gemini_async(
    prompt: str,
    system_instruction: str = None,
    response_schema: dict = None,
    temperature: float = 0.0,
    max_tokens: int = 2048,
    retries: int = 3,
):
    """Call Ollama's local API. Function name kept as call_gemini_async for
    backward compatibility with the rest of the pipeline."""

    url = f"{OLLAMA_BASE_URL}/api/chat"

    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})

    effective_prompt = prompt
    if response_schema:
        effective_prompt += (
            "\n\nYou MUST respond with ONLY a valid JSON object (no markdown, no explanation) "
            f"matching this schema:\n{json.dumps(response_schema, indent=2)}"
        )
    messages.append({"role": "user", "content": effective_prompt})

    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }

    # If we want JSON output, request it via Ollama's format parameter
    if response_schema:
        payload["format"] = "json"

    session = await _get_session()

    for attempt in range(retries):
        try:
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.error(f"Ollama API error (attempt {attempt+1}/{retries}): {resp.status} {body[:200]}")
                    await asyncio.sleep(2 ** attempt)
                    continue

                data = await resp.json()
                content = data.get("message", {}).get("content", "")

                if not content:
                    logger.warning(f"Ollama returned empty content (attempt {attempt+1}/{retries})")
                    await asyncio.sleep(1)
                    continue

                if response_schema:
                    content = _extract_json(content)

                return content

        except aiohttp.ClientError as e:
            logger.error(f"Ollama API network error (attempt {attempt+1}/{retries}): {e}")
            await asyncio.sleep(2 ** attempt)
        except Exception as e:
            logger.error(f"Ollama API unexpected error (attempt {attempt+1}/{retries}): {e}")
            await asyncio.sleep(2 ** attempt)

    logger.error(f"All {retries} retries exhausted for Ollama API call.")
    return None
