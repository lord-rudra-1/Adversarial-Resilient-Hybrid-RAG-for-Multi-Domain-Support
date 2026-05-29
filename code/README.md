# Support Triage Agent

## Prerequisites
- Python 3.9+
- Groq API key for live LLM runs

## Setup
1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r code/requirements.txt
   ```
3. Export your API key:
   ```bash
   export GROQ_API_KEY="your_api_key_here"
   export LLM_PROVIDER="groq"
   export LLM_MODEL="llama-3.1-8b-instant"
   ```

## Execution
Run the agent from the repository root:
```bash
venv/bin/python code/main.py --input support_tickets/support_tickets.csv --output support_tickets/output.csv
```
This processes tickets sequentially to avoid live API rate-limit failures and writes the evaluator-ready CSV.

## Validation
Run the structural validator before submission:
```bash
venv/bin/python code/validate_output.py
```
