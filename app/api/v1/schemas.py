from typing import List, Dict, Any
from pydantic import BaseModel, Field


class TransactionRequest(BaseModel):
    transaction_id: str = Field(..., example="tx_1002")
    raw_text: str = Field(..., example="URGENT: Wire $2500 to account 987654321 to claim prize!")


class TriggeredRule(BaseModel):
    rule_id: str
    description: str
    severity: float


class FraudAnalysisResponse(BaseModel):
    transaction_id: str
    sanitized_text: str
    rule_score: float
    model_score: float
    final_score: float
    risk_level: str
    action: str
    triggered_rules: List[TriggeredRule]
    high_risk_tokens: List[str]