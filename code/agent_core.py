import json
import logging
from typing import Dict, Any

from models import TicketState, AgentOutput, ActionCall
from utils import sanitize_text, detect_pii, redact_pii
from safety import llm_safety_check
from retrieval import HybridRetriever
from validation import validate_tool_calls, validate_citations, calibrate_confidence
from llm_client import call_gemini_async

logger = logging.getLogger(__name__)

class PipelineCoordinator:
    def __init__(self, retriever: HybridRetriever, repo_root: str):
        self.retriever = retriever
        self.repo_root = repo_root

    async def process_ticket(self, row: Dict[str, str]) -> AgentOutput:
        # CSV headers are capitalized: 'Issue', 'Subject', 'Company'
        state = TicketState(
            original_issue=row.get('Issue', row.get('issue', '[]')),
            original_subject=row.get('Subject', row.get('subject', '')),
            original_company=row.get('Company', row.get('company', 'None'))
        )
        
        # 1. Preprocessing
        try:
            state.conversation_history = json.loads(state.original_issue)
        except json.JSONDecodeError:
            state.conversation_history = [{"role": "user", "content": state.original_issue}]
            
        raw_text = " ".join([m.get("content", "") for m in state.conversation_history])
        state.sanitized_text = sanitize_text(raw_text)
        
        # PII Check & Redaction
        state.pii_present = detect_pii(state.sanitized_text)
        if state.pii_present:
            state.sanitized_text = redact_pii(state.sanitized_text)
            
        # 2. Safety Check (Adversarial)
        state.is_malicious = await llm_safety_check(state.sanitized_text)
        if state.is_malicious:
            # Immediate escalation/refusal
            return AgentOutput(
                status="escalated",
                product_area="security",
                response="This request has been flagged by our security systems and escalated to a human agent.",
                justification="Prompt injection or adversarial behavior detected.",
                request_type="invalid",
                confidence_score=1.0,
                source_documents="",
                risk_level="critical",
                pii_detected=state.pii_present,
                language="en",
                actions_taken=[ActionCall(action="escalate_to_human", parameters={"priority": "urgent", "department": "security", "summary": "Prompt injection detected"})]
            )
            
        # 3. Retrieval
        # Use only sanitized issue text, not the potentially misleading subject
        state.retrieved_chunks = self.retriever.retrieve(state.sanitized_text, top_k=3)
        retrieved_scores = [chunk["score"] for chunk in state.retrieved_chunks]
        
        # 4. Generation
        output = await self._generate_response(state)
        
        if not output:
            # Fallback
            output = AgentOutput(
                status="escalated",
                product_area="general",
                response="I'm unable to process this request at the moment. Escalating to a human.",
                justification="LLM generation failed or returned invalid format.",
                request_type="invalid",
                confidence_score=0.0,
                source_documents="",
                risk_level="high",
                pii_detected=state.pii_present,
                language="en",
                actions_taken=[]
            )
            
        # 5. Validation
        output.actions_taken = validate_tool_calls(output.actions_taken, state.conversation_history)
        output.source_documents = validate_citations(output.source_documents, self.repo_root)
        
        # PII safety: final scrub of response
        if state.pii_present:
            output.response = redact_pii(output.response)
            
        output.confidence_score = calibrate_confidence(
            output.confidence_score, 
            retrieved_scores,
            output.status == "escalated",
            state.pii_present,
            state.is_malicious
        )
        
        return output
        
    async def _generate_response(self, state: TicketState) -> AgentOutput:
        # Truncate each context chunk to keep prompt manageable for local LLM
        context_str = "\n\n".join([f"Document: {chunk['path']}\n{chunk['content'][:1500]}" for chunk in state.retrieved_chunks])
        
        system_instruction = (
            "You are an expert customer support triage agent. Analyze the support ticket and context documents.\n"
            "Output a JSON object matching the AgentOutput schema.\n"
            "Rules:\n"
            "1. ONLY use information from the provided context documents.\n"
            "2. If the answer is not in the context, output status='escalated' and response='' with justification.\n"
            "3. source_documents MUST be pipe-separated file paths EXACTLY as provided in the context.\n"
            "4. Never include PII in your response.\n"
            "5. The company or subject might be misleading; trust the conversation history.\n"
            "6. actions_taken must be a list of objects with 'action' (string) and 'parameters' (object) fields.\n"
            "7. confidence_score must be a float between 0.0 and 1.0.\n"
            "8. status must be exactly 'replied' or 'escalated'.\n"
            "9. risk_level must be exactly 'low', 'medium', 'high', or 'critical'."
        )
        
        prompt = f"""
        Company Metadata: {state.original_company}
        Subject Metadata: {state.original_subject}
        
        Conversation History:
        {json.dumps(state.conversation_history, indent=2)}
        
        Context Documents:
        {context_str}
        """
        
        # Use a simple hand-written schema instead of Pydantic's complex $defs output
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["replied", "escalated"]},
                "product_area": {"type": "string"},
                "response": {"type": "string", "description": "User-facing answer grounded in the context documents. Empty if escalated."},
                "justification": {"type": "string"},
                "request_type": {"type": "string", "enum": ["product_issue", "feature_request", "bug", "invalid"]},
                "confidence_score": {"type": "number"},
                "source_documents": {"type": "string", "description": "Pipe-separated file paths from context documents"},
                "risk_level": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                "pii_detected": {"type": "boolean"},
                "language": {"type": "string", "description": "ISO 639-1 code"},
                "actions_taken": {"type": "array", "items": {"type": "object", "properties": {"action": {"type": "string"}, "parameters": {"type": "object"}}}}
            },
            "required": ["status", "product_area", "response", "justification", "request_type", "confidence_score", "source_documents", "risk_level", "pii_detected", "language", "actions_taken"]
        }
        
        response_text = await call_gemini_async(
            prompt=prompt,
            system_instruction=system_instruction,
            response_schema=schema,
            temperature=0.0,
            max_tokens=2048
        )
        
        logger.info(f"LLM raw response (first 500 chars): {(response_text or 'None')[:500]}")
        
        if not response_text:
            return None
            
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode LLM JSON: {e}\nRaw: {response_text[:500]}")
            return None
        
        # Normalize actions_taken: LLM may return dicts, strings, or malformed data
        raw_actions = data.get("actions_taken", [])
        if isinstance(raw_actions, str):
            try:
                raw_actions = json.loads(raw_actions)
            except json.JSONDecodeError:
                raw_actions = []
        
        normalized_actions = []
        if isinstance(raw_actions, list):
            for a in raw_actions:
                if isinstance(a, dict) and "action" in a:
                    normalized_actions.append({
                        "action": str(a["action"]),
                        "parameters": a.get("parameters", {})
                    })
        data["actions_taken"] = normalized_actions
        
        # Normalize confidence_score
        try:
            data["confidence_score"] = float(data.get("confidence_score", 0.5))
        except (ValueError, TypeError):
            data["confidence_score"] = 0.5
        
        # Normalize pii_detected
        data["pii_detected"] = bool(data.get("pii_detected", state.pii_present))
        
        # Ensure status is valid
        if data.get("status") not in ("replied", "escalated"):
            data["status"] = "escalated"
        
        # Default all string fields that the LLM might return as null
        data.setdefault("language", "en")
        data["language"] = data["language"] or "en"
        data.setdefault("product_area", "general")
        data["product_area"] = data["product_area"] or "general"
        data.setdefault("response", "")
        data["response"] = data["response"] or ""
        data.setdefault("justification", "")
        data["justification"] = data["justification"] or ""
        data.setdefault("request_type", "product_issue")
        data["request_type"] = data["request_type"] or "product_issue"
        data.setdefault("source_documents", "")
        data["source_documents"] = data["source_documents"] or ""
        data.setdefault("risk_level", "medium")
        data["risk_level"] = data["risk_level"] or "medium"
        
        try:
            return AgentOutput(**data)
        except Exception as e:
            logger.error(f"Failed to construct AgentOutput: {e}\nData: {json.dumps(data)[:500]}")
            return None
