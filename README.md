# Adversarial-Resilient Hybrid RAG for Multi-Domain Support Triage

A terminal-based AI agent designed to triage real-world support tickets across three major product ecosystems (DevPlatform, Claude, and Visa) using a robust Hybrid Retrieval-Augmented Generation (RAG) approach.

## Overview

This project implements an AI agent that effectively retrieves and leverages knowledge base documents to solve customer support tickets. It features a hybrid retrieval pipeline that combines both dense embeddings and sparse (BM25) search to ensure high accuracy and resilience, even when users submit adversarial or confusing queries.

### Key Features
- **Multi-Domain Support:** Seamlessly handles tickets from entirely different domains.
- **Hybrid RAG Pipeline:** Combines vector search with keyword-based retrieval for optimal document matching.
- **Adversarial Resilience:** Robust against ambiguous, malformed, or intentionally tricky queries.
- **Low Latency:** Optimized for speed with cached retrievals, local safety filters, and Groq streaming.
- **CLI Interface:** A terminal-based interaction loop for request and response handling.

## Setup & Installation

Ensure you have Python installed, then set up the environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Set up your API keys by creating a `.env` file or exporting them in your terminal.

## Usage

You can start the triage agent via the CLI:

```bash
python main.py
```
*(Usage commands may vary depending on the specific CLI module setup).*