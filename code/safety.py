import logging
import re
import math
from collections import Counter

logger = logging.getLogger(__name__)

def entropy(string):
    """Calculates the Shannon entropy of a string."""
    prob = [ float(string.count(c)) / len(string) for c in dict.fromkeys(list(string)) ]
    return - sum([ p * math.log(p) / math.log(2.0) for p in prob ])

def heuristic_injection_check(text: str) -> bool:
    """Advanced heuristic check for prompt injections, jailbreaks, and adversarial behavior.
    Runs locally in <1ms without LLM overhead.
    """
    if not text:
        return False
        
    text_lower = text.lower()
    
    # 1. Known jailbreak vectors
    suspicious_patterns = [
        r"ignore previous instructions",
        r"forget all instructions",
        r"system prompt",
        r"you are now",
        r"new rules",
        r"disregard",
        r"bypass",
        r"print previous",
        r"translate this into",
        r"do anything now",
        r"DAN",
        r"hypothetical situation",
        r"pretend that you"
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, text_lower):
            logger.warning(f"Safety Check: Pattern match '{pattern}'")
            return True
            
    # 2. Base64 / Encoding tricks (looking for long strings without spaces)
    longest_word = max(text.split(), key=len) if text.split() else ""
    if len(longest_word) > 100:
        logger.warning(f"Safety Check: Abnormally long word detected ({len(longest_word)} chars)")
        return True
        
    # 3. High Entropy Check (gibberish or obfuscation)
    # E.g. "xjkzbxkjzb" will have high entropy for its length, but typically English is around 3.5 - 5.0
    # We apply this only to very long inputs to avoid false positives on short inputs
    if len(text) > 200:
        ent = entropy(text)
        if ent > 5.5:  # High entropy threshold
            logger.warning(f"Safety Check: High entropy detected ({ent:.2f})")
            return True
            
    # 4. Length limits (prevent buffer overflow style attacks)
    if len(text) > 5000:
        logger.warning(f"Safety Check: Input exceeded length limit ({len(text)} chars)")
        return True

    return False

async def run_safety_check(issue_text: str) -> bool:
    """Runs the advanced heuristic safety check.
    Returns True if malicious, False if safe.
    Replaces the old LLM-based check to achieve <5ms latency.
    """
    return heuristic_injection_check(issue_text)
