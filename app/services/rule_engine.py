import re
from typing import List, Dict, Any


class RuleEngine:
    def __init__(self):
        self.rules = [
            {
                "rule_id": "R001",
                "description": "High Urgency Keyword",
                "pattern": re.compile(r"\b(urgent|immediately|action required|suspended|expire)\b", re.IGNORECASE),
                "severity": 0.3
            },
            {
                "rule_id": "R002",
                "description": "High-Risk Payment Method",
                "pattern": re.compile(r"\b(wire|gift card|crypto|bitcoin|zelle|venmo)\b", re.IGNORECASE),
                "severity": 0.4
            },
            {
                "rule_id": "R003",
                "description": "Advance-Fee / Prize Pattern",
                "pattern": re.compile(r"\b(lottery|prize|winner|claim|inheritance|grant)\b", re.IGNORECASE),
                "severity": 0.5
            }
        ]

    def evaluate(self, raw_text: str) -> Dict[str, Any]:
        triggered_rules = []
        high_risk_tokens = set()
        total_severity = 0.0

        for rule in self.rules:
            matches = rule["pattern"].findall(raw_text)
            if matches:
                triggered_rules.append({
                    "rule_id": rule["rule_id"],
                    "description": rule["description"],
                    "severity": rule["severity"]
                })
                total_severity += rule["severity"]
                for match in matches:
                    high_risk_tokens.add(match.lower())

        # Cap rule score at 1.0
        rule_score = min(1.0, total_severity)

        return {
            "rule_score": round(rule_score, 4),
            "triggered_rules": triggered_rules,
            "high_risk_tokens": list(high_risk_tokens)
        }