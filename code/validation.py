import json
import os
from pathlib import Path
from typing import List, Dict, Any
from models import ActionCall

DESTRUCTIVE_ACTIONS = {"issue_refund", "modify_subscription", "lock_account"}
TRUSTED_VERIFICATION_PHRASES = (
    "identity verified",
    "verification complete",
    "verified identity",
    "otp verified",
    "security questions verified",
    "authentication complete",
)

def _load_tool_specs() -> Dict[str, Dict[str, Any]]:
    spec_path = Path(__file__).resolve().parent.parent / "data" / "api_specs" / "internal_tools.json"
    try:
        raw_specs = json.loads(spec_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {spec["name"]: spec["parameters"] for spec in raw_specs if "name" in spec and "parameters" in spec}

TOOL_SPECS = _load_tool_specs()

def _coerce_action(action: Any) -> ActionCall | None:
    if isinstance(action, ActionCall):
        return action
    if isinstance(action, dict) and "action" in action:
        params = action.get("parameters", {})
        if not isinstance(params, dict):
            params = {}
        return ActionCall(action=str(action["action"]), parameters=params)
    return None

def _trusted_identity_verified(conversation_history: List[Dict[str, str]]) -> bool:
    for message in conversation_history:
        role = str(message.get("role", "")).lower()
        if role == "user":
            continue
        content = str(message.get("content", "")).lower()
        if any(phrase in content for phrase in TRUSTED_VERIFICATION_PHRASES):
            return True
    return False

def _schema_validated_action(action: ActionCall) -> ActionCall | None:
    schema = TOOL_SPECS.get(action.action)
    if not schema:
        return None

    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    params = action.parameters if isinstance(action.parameters, dict) else {}

    if not required.issubset(params.keys()):
        return None

    cleaned_params = {key: params[key] for key in properties if key in params}
    return ActionCall(action=action.action, parameters=cleaned_params)

def _verification_target(action: ActionCall) -> str | None:
    params = action.parameters if isinstance(action.parameters, dict) else {}
    for key in ("user_email", "email", "phone", "phone_number", "target"):
        value = params.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    identifier = params.get("user_identifier")
    if isinstance(identifier, str) and ("@" in identifier or any(ch.isdigit() for ch in identifier)):
        return identifier.strip()
    return None

def validate_tool_calls(actions: List[ActionCall], conversation_history: List[Dict[str, str]]) -> List[ActionCall]:
    """Strictly validates tool calls and blocks unsafe destructive actions."""
    if not actions:
        return []
        
    validated = []
    is_verified = _trusted_identity_verified(conversation_history)
    
    for action in actions:
        raw_action = _coerce_action(action)
        if raw_action is None:
            continue

        action = _schema_validated_action(raw_action)
        if action is None:
            continue

        if action.action in DESTRUCTIVE_ACTIONS:
            if not is_verified:
                target = _verification_target(raw_action)
                if target:
                    validated.append(ActionCall(
                        action="verify_identity",
                        parameters={"method": "email_otp", "target": target}
                    ))
                continue
        validated.append(action)
        
    return validated

def validate_citations(source_documents_str: str, repo_root: str) -> str:
    """Ensures cited paths are existing repo-relative corpus documents."""
    if not source_documents_str:
        return ""
        
    paths = source_documents_str.split('|')
    valid_paths = []
    repo_path = Path(repo_root).resolve()
    data_path = (repo_path / "data").resolve()
    
    for path in paths:
        path = path.strip()
        if not path:
            continue
        if "://" in path or os.path.isabs(path):
            continue
            
        full_path = (repo_path / path).resolve()
        try:
            full_path.relative_to(data_path)
        except ValueError:
            continue

        if full_path.exists() and full_path.is_file():
            valid_paths.append(str(full_path.relative_to(repo_path)))
            
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
