# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "NLP Fraud Engine"
    ENVIRONMENT: str = "development"
    
    # Model Configuration
    MODEL_PATH: str = "mrm8488/bert-tiny-finetuned-sms-spam-detection"
    
    # Score Aggregation Weights (Optimized for Recall)
    RULE_WEIGHT: float = 0.60
    MODEL_WEIGHT: float = 0.40
    
    # Risk Action Thresholds (Lowered Sensitivity Floors)
    HIGH_RISK_THRESHOLD: float = 0.75
    MEDIUM_RISK_THRESHOLD: float = 0.40

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()