import aiohttp
import os
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

async def call_gemini_async(prompt: str, system_instruction: str = None, response_schema: dict = None, temperature: float = 0.0, max_tokens: int = 1024, retries: int = 4):
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not set")
        return None

    # Using gemini-1.5-flash for speed and cost efficiency
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
    }
    
    if response_schema:
        payload["generationConfig"]["responseMimeType"] = "application/json"
        payload["generationConfig"]["responseSchema"] = response_schema
    else:
        payload["generationConfig"]["responseMimeType"] = "text/plain"
        
    if system_instruction:
        payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        
    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 429:
                        # Rate limit - exponential backoff
                        retry_after = int(response.headers.get("Retry-After", 2 ** attempt))
                        logger.warning(f"Rate limited. Waiting {retry_after}s...")
                        await asyncio.sleep(retry_after)
                        continue
                        
                    response.raise_for_status()
                    data = await response.json()
                    
                    if "candidates" in data and len(data["candidates"]) > 0:
                        candidate = data["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            content = candidate["content"]["parts"][0]["text"]
                            return content
                        elif "finishReason" in candidate and candidate["finishReason"] == "SAFETY":
                            logger.warning("Generation blocked by safety filters.")
                            return None
                    
                    logger.warning(f"No valid candidates in response: {data}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Gemini API network error (attempt {attempt+1}/{retries}): {e}")
            await asyncio.sleep(2 ** attempt)
        except Exception as e:
            logger.error(f"Gemini API unexpected error (attempt {attempt+1}/{retries}): {e}")
            await asyncio.sleep(2 ** attempt)
            
    return None
