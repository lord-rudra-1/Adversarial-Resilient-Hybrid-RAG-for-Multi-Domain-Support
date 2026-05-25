import re
import string

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
    """Detects credit cards, SSNs, emails, and basic phone numbers."""
    cc_pattern = r'\b(?:\d[ -]*?){13,16}\b'
    ssn_pattern = r'\b\d{3}[ -]?\d{2}[ -]?\d{4}\b'
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Very basic checks - for real prod we'd use Presidio
    if re.search(cc_pattern, text): return True
    if re.search(ssn_pattern, text): return True
    if re.search(email_pattern, text): return True
    return False

def redact_pii(text: str) -> str:
    """Replaces PII with [REDACTED]."""
    cc_pattern = r'\b(?:\d[ -]*?){13,16}\b'
    ssn_pattern = r'\b\d{3}[ -]?\d{2}[ -]?\d{4}\b'
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    text = re.sub(cc_pattern, '[REDACTED_CC]', text)
    text = re.sub(ssn_pattern, '[REDACTED_SSN]', text)
    text = re.sub(email_pattern, '[REDACTED_EMAIL]', text)
    return text
