import sys
import os
import csv
import asyncio
import argparse
import time
import logging

from retrieval import HybridRetriever
from agent_core import PipelineCoordinator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def process_all(input_file: str, output_file: str, repo_root: str):
    logger.info(f"Starting execution. Reading from {input_file}")
    
    # 1. Initialize Retriever (loads corpus)
    data_dir = os.path.join(repo_root, "data")
    retriever = HybridRetriever(data_dir=data_dir)
    coordinator = PipelineCoordinator(retriever=retriever, repo_root=repo_root)
    
    # 2. Load tickets
    tickets = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tickets.append(row)
            
    logger.info(f"Loaded {len(tickets)} tickets.")
    
    # 3. Process with bounded concurrency
    # Limits concurrent LLM calls to prevent 429s.
    semaphore = asyncio.Semaphore(15) 
    
    async def bounded_process(ticket):
        async with semaphore:
            return await coordinator.process_ticket(ticket)
            
    tasks = [bounded_process(ticket) for ticket in tickets]
    results = await asyncio.gather(*tasks)
    
    # HARD FAIL DETECTION: Prevent silent success if API calls are failing globally
    failed_generations = sum(1 for r in results if r.justification == "LLM generation failed or returned invalid format.")
    if tickets:
        failure_rate = failed_generations / len(tickets)
        if failure_rate > 0.2:
            logger.error(f"CRITICAL SYSTEM FAILURE: {failed_generations}/{len(tickets)} API calls failed entirely. "
                         f"Hard crashing to prevent silent hidden-test failure. Check API keys and network limits.")
            sys.exit(1)
            
    # 4. Write output
    fieldnames = [
        "status", "product_area", "response", "justification", "request_type",
        "confidence_score", "source_documents", "risk_level", "pii_detected", 
        "language", "actions_taken"
    ]
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            row = result.model_dump()
            import json
            row["actions_taken"] = json.dumps([a for a in row["actions_taken"]])
            writer.writerow(row)
            
    logger.info(f"Finished processing. Wrote to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="MLE Hiring Challenge Support Agent")
    parser.add_argument("--input", default="support_tickets/support_tickets.csv")
    parser.add_argument("--output", default="support_tickets/output.csv")
    args = parser.parse_args()
    
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(repo_root, args.input)
    output_path = os.path.join(repo_root, args.output)
    
    start_time = time.time()
    asyncio.run(process_all(input_path, output_path, repo_root))
    end_time = time.time()
    
    duration = end_time - start_time
    logger.info(f"Total execution time: {duration:.2f} seconds")

if __name__ == "__main__":
    main()
