import re


class Preprocessor:
    def __init__(self):
        # Precise boundary lookarounds prevent matching currency strings (e.g. $2,500)
        self.account_pattern = re.compile(r"(?<![\$\d,])\b\d{8,16}\b")
        self.email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
        self.phone_pattern = re.compile(r"(?<!\d)\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")

    def clean_text(self, text: str) -> str:
        # Scrub PII in order
        text = self.email_pattern.sub("[EMAIL_REDACTED]", text)
        text = self.phone_pattern.sub("[PHONE_REDACTED]", text)
        text = self.account_pattern.sub("[ACCOUNT_REDACTED]", text)
        
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text