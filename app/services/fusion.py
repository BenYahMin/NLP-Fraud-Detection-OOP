# app/services/fusion.py
from typing import List, Dict, Any
from app.config import settings


class FusionEngine:
    def __init__(self):
        self.rule_weight = settings.RULE_WEIGHT
        self.model_weight = settings.MODEL_WEIGHT
        self.high_threshold = settings.HIGH_RISK_THRESHOLD
        self.med_threshold = settings.MEDIUM_RISK_THRESHOLD

    def fuse(
        self,
        transaction_id: str,
        sanitized_text: str,
        rule_score: float,
        model_score: float,
        triggered_rules: List[Dict[str, Any]],
        high_risk_tokens: List[str]
    ) -> Dict[str, Any]:
        
        # Weighted Score Aggregation
        final_score = (self.rule_weight * rule_score) + (self.model_weight * model_score)
        
        # CRITICAL FIX: Rule Override Logic
        # If heuristics hit 1.0, floor the final_score to at least 0.75 or force MEDIUM/HIGH
        if rule_score >= 1.0:
            final_score = max(final_score, 0.75)

        final_score = round(final_score, 4)

        # Decision Mapping
        if final_score >= self.high_threshold:
            risk_level = "HIGH"
            action = "BLOCK"
        elif final_score >= self.med_threshold:
            risk_level = "MEDIUM"
            action = "MANUAL_REVIEW"
        else:
            risk_level = "LOW"
            action = "ALLOW"

        return {
            "transaction_id": transaction_id,
            "sanitized_text": sanitized_text,
            "rule_score": rule_score,
            "model_score": model_score,
            "final_score": final_score,
            "risk_level": risk_level,
            "action": action,
            "triggered_rules": triggered_rules,
            "high_risk_tokens": high_risk_tokens
        }