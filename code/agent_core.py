import json
import logging
from typing import Dict, Any, AsyncGenerator, Union

from models import TicketState, AgentOutput, ActionCall
from utils import sanitize_text, detect_pii, redact_pii
from safety import run_safety_check
from retrieval import HybridRetriever
from validation import validate_tool_calls, validate_citations, calibrate_confidence
from llm_client import call_gemini_async, call_llm_stream

logger = logging.getLogger(__name__)

VALID_REQUEST_TYPES = {"product_issue", "feature_request", "bug", "invalid"}
VALID_RISK_LEVELS = {"low", "medium", "high", "critical"}

def _normalize_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    if value is None:
        return default
    return bool(value)

def _normalize_request_type(value: Any, status: str) -> str:
    raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if raw in VALID_REQUEST_TYPES:
        return raw
    if "feature" in raw:
        return "feature_request"
    if "bug" in raw or "error" in raw:
        return "bug"
    if "invalid" in raw or "adversarial" in raw or "prompt" in raw:
        return "invalid"
    return "invalid" if status == "escalated" and not raw else "product_issue"

def _normalize_risk_level(value: Any) -> str:
    raw = str(value or "").strip().lower()
    return raw if raw in VALID_RISK_LEVELS else "medium"

class PipelineCoordinator:
    def __init__(self, retriever: HybridRetriever, repo_root: str):
        self.retriever = retriever
        self.repo_root = repo_root

    def _fallback_output(self, state: TicketState, justification: str) -> AgentOutput:
        return AgentOutput(
            status="escalated",
            product_area="general",
            response="I'm unable to process this request at the moment. Escalating to a human.",
            justification=justification,
            request_type="invalid",
            confidence_score=0.0,
            source_documents="",
            risk_level="high",
            pii_detected=state.pii_present,
            language="en",
            actions_taken=[]
        )

    async def process_ticket(self, row: Dict[str, str], stream: bool = False) -> Union[AgentOutput, AsyncGenerator]:
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
            
        user_msgs = [m.get("content", "") for m in state.conversation_history if m.get("role") == "user"]
        # Only use the absolutely most recent message to retrieve context, preventing topic bleeding
        raw_text = user_msgs[-1] if user_msgs else state.original_issue
        state.sanitized_text = sanitize_text(raw_text)
        
        # PII Check & Redaction
        state.pii_present = detect_pii(state.sanitized_text)
        if state.pii_present:
            state.sanitized_text = redact_pii(state.sanitized_text)
            
        # 2. Safety Check (Adversarial) - Now local & sync
        state.is_malicious = await run_safety_check(state.sanitized_text)
        if state.is_malicious:
            # Immediate escalation/refusal
            output = AgentOutput(
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
                actions_taken=[ActionCall(action="escalate_to_human", parameters={
                    "priority": "urgent",
                    "department": "security",
                    "summary": "Prompt injection or adversarial behavior detected."
                })]
            )
            if stream:
                async def _yield_output():
                    yield output
                return _yield_output()
            return output
            
        # 3. Retrieval
        state.retrieved_chunks = self.retriever.retrieve(state.sanitized_text, top_k=3)
        retrieved_scores = [chunk["score"] for chunk in state.retrieved_chunks]
        
        if stream:
            # Return a generator that yields strings then finally the AgentOutput
            async def _stream_generator():
                final_output = None
                async for chunk in self._generate_response_stream(state):
                    if isinstance(chunk, str):
                        yield chunk
                    else:
                        final_output = chunk
                
                if not final_output:
                    final_output = self._fallback_output(state, "LLM generation failed.")
                
                # 5. Validation
                final_output.actions_taken = validate_tool_calls(final_output.actions_taken, state.conversation_history)
                final_output.source_documents = validate_citations(final_output.source_documents, self.repo_root)
                final_output.confidence_score = calibrate_confidence(final_output.confidence_score, retrieved_scores, final_output.status == "escalated", state.pii_present, state.is_malicious)
                yield final_output

            return _stream_generator()
            
        final_output = await self._generate_response_once(state)
                
        if not final_output:
            final_output = self._fallback_output(state, "LLM generation failed or returned invalid format.")
            
        # 5. Validation
        final_output.actions_taken = validate_tool_calls(final_output.actions_taken, state.conversation_history)
        final_output.source_documents = validate_citations(final_output.source_documents, self.repo_root)
        
        final_output.confidence_score = calibrate_confidence(
            final_output.confidence_score, 
            retrieved_scores,
            final_output.status == "escalated",
            state.pii_present,
            state.is_malicious
        )
        
        return final_output

    def _generation_payload(self, state: TicketState) -> tuple[str, str, Dict[str, Any]]:
        # Keep context compact for live LLM TPM limits while still grounding the
        # answer in the strongest retrieved evidence.
        context_str = "\n\n".join([
            f"Document: {chunk['path']}\n{chunk['content'][:500]}"
            for chunk in state.retrieved_chunks[:2]
        ])

        system_instruction = (
            "You are an expert customer support triage agent. Analyze the support ticket and context documents.\n"
            "Output a JSON object matching the AgentOutput schema.\n"
            "Rules:\n"
            "1. ONLY use information from the provided context documents.\n"
            "2. If the answer is not in the context, output status='escalated' and response='' with justification.\n"
            "3. source_documents MUST be pipe-separated file paths EXACTLY as provided in the context.\n"
            "4. Never include PII in your response.\n"
            "5. The company or subject might be misleading; trust the conversation history.\n"
            "6. actions_taken must be a list of objects with 'action' and 'parameters'.\n"
            "7. confidence_score must be a float between 0.0 and 1.0.\n"
            "8. status must be exactly 'replied' or 'escalated'.\n"
            "9. request_type must be exactly one of: product_issue, feature_request, bug, invalid.\n"
            "10. risk_level must be exactly 'low', 'medium', 'high', or 'critical'.\n"
            "11. Do NOT tell the user to 'read the article' or 'follow the link'. Extract useful steps from context directly.\n"
            "12. If the user's latest message is just 'thank you' or a greeting, simply acknowledge it politely."
        )

        prompt = f"""
        Company: {state.original_company}
        Subject: {state.original_subject}

        History:
        {json.dumps(state.conversation_history, indent=2)}

        Context:
        {context_str}
        """

        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["replied", "escalated"]},
                "product_area": {"type": "string"},
                "response": {"type": "string"},
                "justification": {"type": "string"},
                "request_type": {"type": "string", "enum": ["product_issue", "feature_request", "bug", "invalid"]},
                "confidence_score": {"type": "number"},
                "source_documents": {"type": "string"},
                "risk_level": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                "pii_detected": {"type": "boolean"},
                "language": {"type": "string"},
                "actions_taken": {"type": "array"}
            },
            "required": ["status", "product_area", "response", "justification", "request_type", "confidence_score", "source_documents", "risk_level", "pii_detected", "language", "actions_taken"]
        }
        return prompt, system_instruction, schema

    def _normalize_agent_data(self, data: Dict[str, Any], state: TicketState) -> Dict[str, Any]:
        raw_actions = data.get("actions_taken", [])
        if isinstance(raw_actions, str):
            try:
                raw_actions = json.loads(raw_actions)
            except Exception:
                raw_actions = []
        normalized_actions = []
        if isinstance(raw_actions, list):
            for action in raw_actions:
                if isinstance(action, dict) and "action" in action:
                    params = action.get("parameters", {})
                    normalized_actions.append({
                        "action": str(action["action"]),
                        "parameters": params if isinstance(params, dict) else {}
                    })
        data["actions_taken"] = normalized_actions

        try:
            data["confidence_score"] = float(data.get("confidence_score", 0.5))
        except Exception:
            data["confidence_score"] = 0.5

        data["pii_detected"] = _normalize_bool(data.get("pii_detected"), state.pii_present)
        if data.get("status") not in ("replied", "escalated"):
            data["status"] = "escalated"

        for key in ["language", "product_area", "response", "justification", "request_type", "source_documents", "risk_level"]:
            data.setdefault(key, "")
            if not data[key]:
                data[key] = ""
        data["language"] = data["language"] or "en"
        data["product_area"] = data["product_area"] or "general"
        data["request_type"] = _normalize_request_type(data.get("request_type"), data["status"])
        data["risk_level"] = _normalize_risk_level(data.get("risk_level"))
        return data

    async def _generate_response_once(self, state: TicketState) -> AgentOutput | None:
        prompt, system_instruction, schema = self._generation_payload(state)
        full_text = await call_gemini_async(
            prompt=prompt,
            system_instruction=system_instruction,
            response_schema=schema,
            max_tokens=700,
            retries=5,
        )
        if not full_text:
            return None
        try:
            from llm_client import _extract_json
            data = json.loads(_extract_json(full_text))
            return AgentOutput(**self._normalize_agent_data(data, state))
        except Exception as e:
            logger.error(f"Failed to decode LLM JSON: {e}\nRaw: {str(full_text)[:500]}")
            return None
        
    async def _generate_response_stream(self, state: TicketState):
        """Yields streaming string chunks, then returns the final AgentOutput."""
        prompt, system_instruction, schema = self._generation_payload(state)
        
        # We will yield the raw text chunks as they arrive
        full_text = ""
        async for chunk in call_llm_stream(
            prompt=prompt + f"\n\nJSON Schema:\n{json.dumps(schema)}", 
            system_instruction=system_instruction,
            max_tokens=1024
        ):
            full_text += chunk
            yield chunk
            
        if not full_text:
            yield None
            return
            
        try:
            from llm_client import _extract_json
            json_text = _extract_json(full_text)
            data = json.loads(json_text)
        except Exception as e:
            logger.error(f"Failed to decode LLM JSON: {e}\nRaw: {full_text[:500]}")
            yield None
            return
        
        data = self._normalize_agent_data(data, state)
        
        try:
            yield AgentOutput(**data)
        except Exception as e:
            logger.error(f"Failed to construct AgentOutput: {e}")
            yield None
