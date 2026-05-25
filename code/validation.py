import os
from typing import List, Dict, Any
from code.models import ActionCall

def validate_tool_calls(actions: List[ActionCall], conversation_history: List[Dict[str, str]]) -> List[ActionCall]:
    """Ensures destructive actions are preceded by identity verification."""
    if not actions:
        return []
        
    validated = []
    
    # Check if identity was verified in conversation history
    history_text = " ".join([m["content"] for m in conversation_history]).lower()
    is_verified = "verified" in history_text or "otp" in history_text or "security questions" in history_text
    
    for action in actions:
        if action.action in ["issue_refund", "modify_subscription", "lock_account"]:
            if not is_verified:
                # Override: force verify_identity instead of the destructive action
                validated.append(ActionCall(
                    action="verify_identity", 
                    parameters={"method": "email_otp", "target": "user@example.com"} # Placeholder target
                ))
                continue
        validated.append(action)
        
    return validated

def validate_citations(source_documents_str: str, repo_root: str) -> str:
    """Ensures cited paths actually exist in the file system."""
    if not source_documents_str:
        return ""
        
    paths = source_documents_str.split('|')
    valid_paths = []
    
    for path in paths:
        path = path.strip()
        if not path:
            continue
            
        full_path = os.path.join(repo_root, path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            valid_paths.append(path)
            
    return "|".join(valid_paths)

def calibrate_confidence(base_confidence: float, retrieved_scores: List[float], is_escalated: bool, pii_detected: bool, is_malicious: bool) -> float:
    """Adjusts confidence based on retrieval quality and risk penalties."""
    if is_malicious:
        return 1.0 # 100% confident it's an injection
        
    confidence = base_confidence
    
    if is_escalated:
        return min(0.95, confidence)
        
    # Penalty if max retrieval score is low (hallucination risk)
    if not retrieved_scores:
        confidence -= 0.3
    else:
        max_score = max(retrieved_scores)
        if max_score < 0.4:
            confidence -= 0.2
            
    # Risk penalty
    if pii_detected:
        confidence -= 0.1
        
    return max(0.0, min(1.0, confidence))
