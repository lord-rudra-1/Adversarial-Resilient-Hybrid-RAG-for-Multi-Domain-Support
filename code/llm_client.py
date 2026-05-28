import aiohttp
import os
import json
import asyncio
import logging
import re
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

# --- Load .env manually if needed ---
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ.setdefault(k, v)

# --- Configuration ---
def _load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k.strip()] = v.strip(' "\'')

_load_env()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# Using 8b instant for maximum speed
GROQ_MODEL = "llama-3.1-8b-instant"

if not GROQ_API_KEY:
    logger.error("GROQ_API_KEY not found in .env or environment variables.")

_SESSION: aiohttp.ClientSession | None = None

async def _get_session() -> aiohttp.ClientSession:
    global _SESSION
    if _SESSION is None or _SESSION.closed:
        timeout = aiohttp.ClientTimeout(total=60) 
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
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```\s*$', '', text)
    text = text.strip()
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
    max_tokens: int = 1024,
    retries: int = 3,
):
    """Backwards compatible blocking call for batch processing (main.py)."""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

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
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }

    if response_schema:
        payload["response_format"] = {"type": "json_object"}

    session = await _get_session()

    for attempt in range(retries):
        try:
            async with session.post(GROQ_URL, headers=headers, json=payload, ssl=False) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.error(f"Groq API error: {resp.status} {body[:200]}")
                    await asyncio.sleep(2 ** attempt)
                    continue

                data = await resp.json()
                content = data["choices"][0]["message"].get("content", "")

                if response_schema:
                    content = _extract_json(content)

                return content
        except Exception as e:
            logger.error(f"Groq API network error: {e}")
            await asyncio.sleep(2 ** attempt)

    return None

async def call_llm_stream(
    prompt: str,
    system_instruction: str = None,
    temperature: float = 0.0,
    max_tokens: int = 1024,
) -> AsyncGenerator[str, None]:
    """Streaming generator for the interactive CLI."""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True
    }

    session = await _get_session()

    try:
        async with session.post(GROQ_URL, headers=headers, json=payload, ssl=False) as resp:
            if resp.status != 200:
                body = await resp.text()
                logger.error(f"Groq stream error: {resp.status} {body[:200]}")
                yield f"[Error: API failed with status {resp.status}]"
                return

            async for line in resp.content:
                if line:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: ') and line != 'data: [DONE]':
                        try:
                            chunk = json.loads(line[6:])
                            token = chunk['choices'][0]['delta'].get('content', '')
                            if token:
                                yield token
                        except json.JSONDecodeError:
                            pass
    except Exception as e:
        logger.error(f"Groq stream exception: {e}")
        yield f"[Connection Error: {e}]"
