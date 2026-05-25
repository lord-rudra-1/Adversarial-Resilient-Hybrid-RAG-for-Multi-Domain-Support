from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ActionCall(BaseModel):
    action: str = Field(..., description="Name of the tool/API to call")
    parameters: Dict[str, Any] = Field(..., description="Arguments for the tool")

class AgentOutput(BaseModel):
    status: str = Field(..., description="'replied' or 'escalated'")
    product_area: str = Field(..., description="Relevant support category, e.g., 'billing', 'technical', 'general', or specific product names")
    response: str = Field(..., description="User facing response grounded in corpus. Must not contain PII. Must be empty if escalated.")
    justification: str = Field(..., description="Reasoning for decision, including risk assessment")
    request_type: str = Field(..., description="'product_issue', 'feature_request', 'bug', 'invalid'")
    confidence_score: float = Field(..., description="Confidence in the response (0.0 to 1.0)")
    source_documents: str = Field(..., description="Pipe-separated file paths used to generate response")
    risk_level: str = Field(..., description="'low', 'medium', 'high', 'critical'")
    pii_detected: bool = Field(..., description="Whether PII was detected in the input")
    language: str = Field(..., description="ISO 639-1 code of the user input")
    actions_taken: List[ActionCall] = Field(..., description="List of API tool calls")

class TicketState(BaseModel):
    original_issue: str
    original_subject: str
    original_company: str
    
    # Processed data
    conversation_history: List[Dict[str, str]] = []
    sanitized_text: str = ""
    is_malicious: bool = False
    is_escalated: bool = False
    pii_present: bool = False
    
    # Retrieval
    retrieved_chunks: List[Dict[str, Any]] = []
    
    # Final outputs
    final_output: Optional[AgentOutput] = None
