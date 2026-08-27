# NLP Fraud Detection Engine

A hybrid fraud detection API combining heuristic rule engines and pre-trained Transformer models (BERT) to analyze text payloads for phishing, scam, and fraudulent payment patterns.

## Features
- **PII Masking**: Automated redaction of bank accounts, phone numbers, and emails using lookaround regexes that preserve currency values.
- **Rule Engine**: Pattern matching for urgency keywords, high-risk payment channels, and advance-fee scam structures.
- **Transformer Inference**: Deep-learning scoring via HuggingFace `transformers`.
- **Score Fusion**: Weighted aggregation of heuristic and deep learning probabilities into actionable risk decisions (`ALLOW`, `MANUAL_REVIEW`, `BLOCK`).

## Quick Start

### 1. Installation
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt