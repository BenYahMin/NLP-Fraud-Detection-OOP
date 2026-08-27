import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import logging as tf_logging
from app.config import settings
from app.utils.logger import logger

# Suppress HuggingFace un-initialized weight warnings on raw heads
tf_logging.set_verbosity_error()


class ModelService:
    def __init__(self):
        self.tokenizer = None
        self.model = None

    def load_model(self):
        try:
            logger.info(f"Loading transformer model from: {settings.MODEL_PATH}")
            self.tokenizer = AutoTokenizer.from_pretrained(settings.MODEL_PATH)
            self.model = AutoModelForSequenceClassification.from_pretrained(settings.MODEL_PATH)
            self.model.eval()
            logger.info("Transformer model successfully loaded.")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise e

    def is_ready(self) -> bool:
        return self.tokenizer is not None and self.model is not None

    def predict(self, text: str) -> float:
        if not self.is_ready():
            raise RuntimeError("Model is not initialized.")

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=128,
            padding=True
        )

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)
            # Probability of positive (spam/fraud) class
            fraud_prob = probs[0][-1].item()

        return round(fraud_prob, 4)


model_service = ModelService()