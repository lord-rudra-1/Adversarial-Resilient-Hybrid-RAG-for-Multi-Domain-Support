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
                actions_taken=[ActionCall(action="escalate_to_human", parameters={"priority": "urgent", "department": "security"})]
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
            
        # For batch mode, we just consume the stream silently
        final_output = None
        async for chunk in self._generate_response_stream(state):
            if not isinstance(chunk, str):
                final_output = chunk
                
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
        
    async def _generate_response_stream(self, state: TicketState):
        """Yields streaming string chunks, then returns the final AgentOutput."""
        # Truncate each context chunk to keep prompt tiny
        context_str = "\n\n".join([f"Document: {chunk['path']}\n{chunk['content'][:800]}" for chunk in state.retrieved_chunks])
        
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
            "9. risk_level must be exactly 'low', 'medium', 'high', or 'critical'.\n"
            "10. Do NOT tell the user to 'read the article' or 'follow the link'. You MUST extract and display the exact troubleshooting steps from the context directly in your response.\n"
            "11. If the user's latest message is just 'thank you' or a greeting, simply acknowledge it politely (e.g., 'You\\'re welcome!'). Do NOT repeat previous troubleshooting steps."
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
                "request_type": {"type": "string"},
                "confidence_score": {"type": "number"},
                "source_documents": {"type": "string"},
                "risk_level": {"type": "string"},
                "pii_detected": {"type": "boolean"},
                "language": {"type": "string"},
                "actions_taken": {"type": "array"}
            },
            "required": ["status", "product_area", "response", "justification", "request_type", "confidence_score", "source_documents", "risk_level", "pii_detected", "language", "actions_taken"]
        }
        
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
        
        # Normalize fields
        raw_actions = data.get("actions_taken", [])
        if isinstance(raw_actions, str):
            try:
                raw_actions = json.loads(raw_actions)
            except:
                raw_actions = []
        normalized_actions = []
        if isinstance(raw_actions, list):
            for a in raw_actions:
                if isinstance(a, dict) and "action" in a:
                    normalized_actions.append({"action": str(a["action"]), "parameters": a.get("parameters", {})})
        data["actions_taken"] = normalized_actions
        
        try:
            data["confidence_score"] = float(data.get("confidence_score", 0.5))
        except:
            data["confidence_score"] = 0.5
        
        data["pii_detected"] = bool(data.get("pii_detected", state.pii_present))
        if data.get("status") not in ("replied", "escalated"):
            data["status"] = "escalated"
        
        for k in ["language", "product_area", "response", "justification", "request_type", "source_documents", "risk_level"]:
            data.setdefault(k, "")
            if not data[k]:
                data[k] = ""
        data["language"] = data["language"] or "en"
        data["product_area"] = data["product_area"] or "general"
        data["request_type"] = data["request_type"] or "product_issue"
        data["risk_level"] = data["risk_level"] or "medium"
        
        try:
            yield AgentOutput(**data)
        except Exception as e:
            logger.error(f"Failed to construct AgentOutput: {e}")
            yield None
