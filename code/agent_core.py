import json
import logging
from typing import Dict, Any

from code.models import TicketState, AgentOutput, ActionCall
from code.utils import sanitize_text, detect_pii, redact_pii
from code.safety import llm_safety_check
from code.retrieval import HybridRetriever
from code.validation import validate_tool_calls, validate_citations, calibrate_confidence
from code.llm_client import call_gemini_async

logger = logging.getLogger(__name__)

class PipelineCoordinator:
    def __init__(self, retriever: HybridRetriever, repo_root: str):
        self.retriever = retriever
        self.repo_root = repo_root

    async def process_ticket(self, row: Dict[str, str]) -> AgentOutput:
        state = TicketState(
            original_issue=row.get('issue', '[]'),
            original_subject=row.get('subject', ''),
            original_company=row.get('company', 'None')
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
        context_str = "\n\n".join([f"Document: {chunk['path']}\n{chunk['content']}" for chunk in state.retrieved_chunks])
        
        system_instruction = (
            "You are an expert customer support triage agent. Analyze the support ticket and context documents.\n"
            "Output a JSON object matching the AgentOutput schema.\n"
            "Rules:\n"
            "1. ONLY use information from the provided context documents.\n"
            "2. If the answer is not in the context, output status='escalated' and response='' with justification.\n"
            "3. source_documents MUST be pipe-separated file paths EXACTLY as provided in the context.\n"
            "4. Never include PII in your response.\n"
            "5. The company or subject might be misleading; trust the conversation history."
        )
        
        prompt = f"""
        Company Metadata: {state.original_company}
        Subject Metadata: {state.original_subject}
        
        Conversation History:
        {json.dumps(state.conversation_history, indent=2)}
        
        Context Documents:
        {context_str}
        """
        
        schema = AgentOutput.model_json_schema()
        
        response_text = await call_gemini_async(
            prompt=prompt,
            system_instruction=system_instruction,
            response_schema=schema,
            temperature=0.0,
            max_tokens=1024
        )
        
        if response_text:
            try:
                data = json.loads(response_text)
                return AgentOutput(**data)
            except Exception as e:
                logger.error(f"Failed to parse generation output: {e}\nResponse: {response_text}")
                
        return None
