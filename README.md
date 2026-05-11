# NLP-Fraud-Detection-OOP
An OOP-based NLP system for fraudulent job detection featuring concurrent processing and active learning (Milestones 5 &amp; 6)
NLP Fraud Detection System (Milestones 5 & 6)
An OOP-based NLP system designed to detect fraudulent job postings. This project fulfills the requirements for the Object-Oriented Programming (OOP) unit, focusing on high-performance concurrency and research-level innovation.

## Key Features
Concurrent Processing (Milestone 5): Utilizes Python's multiprocessing and concurrent.futures to parallelize text preprocessing, significantly reducing execution time for large datasets.

Active Learning (Milestone 6): Implements an "uncertainty sampling" logic where the model flags low-confidence predictions for manual review, allowing for iterative improvement.

Advanced OOP Architecture: Employs design patterns like the Strategy Pattern for text cleaning and Custom Exception Handling for robust system state management.

High-Performance Pipelines: Uses asynchronous I/O and functional generators for memory-efficient data handling.

## System Architecture
The system is built on a modular structure to ensure scalability and maintainability:

Document: The core data structure.

TextPreprocessor: Encapsulates text cleaning logic.

NLPSystem: The main controller that manages training, concurrent prediction, and state persistence.

## Technical Stack
Language: Python.

Libraries: scikit-learn (ML), pandas (Data handling), asyncio & multiprocessing (Performance).

Documentation: Research-level analysis generated for conference-standard reporting.

## How to Run
Ensure you have the fake_job_postings.csv in the root directory.

Install dependencies: from the requirements.txt

Run the main script:

python sprint3_milestone56.py
