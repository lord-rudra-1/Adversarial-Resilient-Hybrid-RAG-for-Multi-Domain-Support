import re
import string

CC_PATTERN = r'\b(?:\d[ -]*?){13,16}\b'
SSN_PATTERN = r'\b\d{3}[ -]?\d{2}[ -]?\d{4}\b'
EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
PHONE_PATTERN = r'(?<!\w)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\w)'
ADDRESS_PATTERN = (
    r'\b\d{1,6}\s+'
    r'(?:[A-Za-z0-9#.-]+\s+){1,6}'
    r'(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln|boulevard|blvd|'
    r'way|court|ct|circle|cir|place|pl)\b'
    r'(?:[,\s]+[A-Za-z .-]+)?(?:[,\s]+[A-Z]{2})?(?:\s+\d{5}(?:-\d{4})?)?'
)

def sanitize_text(text: str) -> str:
    """Removes weird control characters and normalizes whitespace."""
    if not isinstance(text, str):
        return ""
    # Remove unprintable characters except standard whitespace
    printable = set(string.printable)
    text = ''.join(filter(lambda x: x in printable, text))
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def detect_pii(text: str) -> bool:
    """Detects common high-risk PII in support tickets."""
    if not isinstance(text, str):
        return False
    
    if re.search(CC_PATTERN, text): return True
    if re.search(SSN_PATTERN, text): return True
    if re.search(EMAIL_PATTERN, text): return True
    if re.search(PHONE_PATTERN, text): return True
    if re.search(ADDRESS_PATTERN, text, flags=re.IGNORECASE): return True
    return False

def redact_pii(text: str) -> str:
    """Replaces PII with [REDACTED]."""
    if not isinstance(text, str):
        return ""
    
    text = re.sub(CC_PATTERN, '[REDACTED_CC]', text)
    text = re.sub(SSN_PATTERN, '[REDACTED_SSN]', text)
    text = re.sub(EMAIL_PATTERN, '[REDACTED_EMAIL]', text)
    text = re.sub(PHONE_PATTERN, '[REDACTED_PHONE]', text)
    text = re.sub(ADDRESS_PATTERN, '[REDACTED_ADDRESS]', text, flags=re.IGNORECASE)
    return text
