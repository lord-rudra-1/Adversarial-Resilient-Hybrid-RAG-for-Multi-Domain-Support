# Support Triage Agent

## Prerequisites
- Python 3.9+
- Gemini API Key

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
   export GEMINI_API_KEY="your_api_key_here"
   ```

## Execution
Run the agent from the repository root:
```bash
python3 code/main.py --input support_tickets/support_tickets.csv --output support_tickets/output.csv
```
This will process all tickets concurrently and output to the specified CSV.
