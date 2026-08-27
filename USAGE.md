# NLP Fraud Detection Engine — User Guide & Manual

This guide provides detailed instructions on how to set up, configure, run, and integrate the **NLP Fraud Detection Engine**.

---

## Overview

The **NLP Fraud Detection Engine** is a hybrid security pipeline designed to analyze text payloads (e.g., transactional memos, payment notes, emails, SMS) for financial scam patterns, phishing, and advance-fee fraud. 

It combines three core architectural layers:
1. **PII Masking Preprocessor**: Automatic scrubbing of bank accounts, phone numbers, and emails before downstream processing.
2. **Deterministic Rule Engine**: High-precision regex pattern matching for urgency tokens, payment methods, and scam structures.
3. **Deep Learning Transformer**: Contextual NLP sequence classification using BERT-based models.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- Git

### 2. Environment Setup

Clone the repository and set up a virtual environment:

```bash
# Clone the repository
git clone [https://github.com/BenYahMin/nlp-fraud-engine.git](https://github.com/your-BenYahMin/nlp-fraud-engine.git)
cd nlp-fraud-engine

# Create and activate virtual environment
python -m venv venv

# On Linux/macOS:
source venv/bin/activate
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

3. Environment Variables Configuration
Create or update your .env file in the project root to optimize for High Recall (minimizing false negatives on scam attempts):

APP_NAME="NLP Fraud Engine"
ENVIRONMENT="development"
MODEL_PATH="mrm8488/bert-tiny-finetuned-sms-spam-detection"

# Score Fusion Weights (Must sum to 1.0)
RULE_WEIGHT=0.60
MODEL_WEIGHT=0.40

# Risk Thresholds
HIGH_RISK_THRESHOLD=0.75
MEDIUM_RISK_THRESHOLD=0.40

4. Running the Application
Start the FastAPI application with Uvicorn:

uvicorn app.main:app --reload --port 8000

Once running:

Web Dashboard: Open http://localhost:8000

Interactive OpenAPI/Swagger Docs: Open http://localhost:8000/docs

ReDoc Technical Specs: Open http://localhost:8000/redoc

Health Check: Open http://localhost:8000/health

Interface & Usage Methods
Method 1: Visual Web Dashboard (Browser)
Navigate to http://localhost:8000 in your browser to access the built-in test console.

Enter a Transaction ID (e.g., tx_1001).

Type or paste the payload into the Raw Transaction Text area.

Click Run Detection.

View real-time risk scores, PII redaction outputs, triggered rules, and decision labels.

Method 2: PowerShell API Request
Run the following command in PowerShell:

$headers = @{ "Content-Type" = "application/json" }
$body = @{
    transaction_id = "tx_9901"
    raw_text = "URGENT: Please wire $2,500 immediately to account 987654321 to claim your lottery prize!"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/analyze" -Method Post -Headers $headers -Body $body

Method 3: Python Integration Example
You can integrate this API into downstream microservices using standard HTTP requests:

import requests

API_URL = "http://localhost:8000/api/v1/analyze"

payload = {
    "transaction_id": "tx_4002",
    "raw_text": "Action required: Wire funds to crypto wallet to release inheritance."
}

response = requests.post(API_URL, json=payload)
data = response.json()

print(f"Risk Level: {data['risk_level']}")
print(f"Action: {data['action']}")
print(f"Sanitized Text: {data['sanitized_text']}")
print(f"Final Score: {data['final_score']}")

Method 4: cURL Request

curl -X POST "http://localhost:8000/api/v1/analyze" \
     -H "Content-Type: application/json" \
     -d '{
           "transaction_id": "tx_2001",
           "raw_text": "URGENT: Suspended account. Verify details immediately at user@example.com"
         }'

Automated Testing
Run the pytest suite to verify pattern matching, PII redaction integrity, and API endpoint routing:

pytest -v

# I will create a pdf on how the scoring works for a better understanding of the engine.