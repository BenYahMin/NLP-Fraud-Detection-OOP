from app.services.preprocessor import Preprocessor
from app.services.rule_engine import RuleEngine


def test_preprocessor_currency_preservation():
    preprocessor = Preprocessor()
    raw = "Wire $2,500 to account 987654321 immediately."
    clean = preprocessor.clean_text(raw)
    assert "$2,500" in clean
    assert "[ACCOUNT_REDACTED]" in clean


def test_rule_engine_matching():
    engine = RuleEngine()
    result = engine.evaluate("URGENT: Claim your lottery prize via wire transfer!")
    assert result["rule_score"] == 1.0
    assert len(result["triggered_rules"]) == 3
    assert "urgent" in result["high_risk_tokens"]