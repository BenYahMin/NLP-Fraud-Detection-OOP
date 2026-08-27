from fastapi import APIRouter, HTTPException, status
from app.api.v1.schemas import TransactionRequest, FraudAnalysisResponse
from app.services.preprocessor import Preprocessor
from app.services.rule_engine import RuleEngine
from app.services.model_service import model_service
from app.services.fusion import FusionEngine
from app.utils.logger import logger

router = APIRouter()
preprocessor = Preprocessor()
rule_engine = RuleEngine()
fusion_engine = FusionEngine()


@router.post("/analyze", response_model=FraudAnalysisResponse)
async def analyze_transaction(request: TransactionRequest):
    try:
        # 1. PII Redaction & Normalization
        sanitized_text = preprocessor.clean_text(request.raw_text)

        # 2. Rule-Based Evaluation
        rule_result = rule_engine.evaluate(request.raw_text)

        # 3. Transformer Model Inference
        model_score = model_service.predict(sanitized_text)

        # 4. Fusion & Decision Logic
        final_response = fusion_engine.fuse(
            transaction_id=request.transaction_id,
            sanitized_text=sanitized_text,
            rule_score=rule_result["rule_score"],
            model_score=model_score,
            triggered_rules=rule_result["triggered_rules"],
            high_risk_tokens=rule_result["high_risk_tokens"]
        )

        return final_response

    except Exception as e:
        logger.error(f"Error processing transaction {request.transaction_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal fraud engine error: {str(e)}"
        )