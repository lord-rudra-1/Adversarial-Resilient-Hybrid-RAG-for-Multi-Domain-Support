#!/usr/bin/env python3
"""
Interactive Terminal Agent — MLE Hiring Challenge
═══════════════════════════════════════════════════
A live REPL that lets you query the support agent directly from your terminal.
Runs the full multi-stage pipeline: Sanitize → Safety → Retrieve → Generate → Validate

Usage:
    python3 code/cli.py
    python3 code/cli.py --company DevPlatform
"""

import sys
import os
import json
import asyncio
import argparse
import time
import logging

# Ensure imports work from code/ directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from retrieval import HybridRetriever
from agent_core import PipelineCoordinator
from llm_client import close_session, GROQ_MODEL

# ─── ANSI Colors ─────────────────────────────────────────────────────────────
class C:
    RESET    = "\033[0m"
    BOLD     = "\033[1m"
    DIM      = "\033[2m"
    ITALIC   = "\033[3m"
    UNDER    = "\033[4m"

    BLACK    = "\033[30m"
    RED      = "\033[31m"
    GREEN    = "\033[32m"
    YELLOW   = "\033[33m"
    BLUE     = "\033[34m"
    MAGENTA  = "\033[35m"
    CYAN     = "\033[36m"
    WHITE    = "\033[37m"

    BG_BLACK = "\033[40m"
    BG_BLUE  = "\033[44m"
    BG_CYAN  = "\033[46m"
    BG_MAG   = "\033[45m"

    # 256-color / bright
    GRAY     = "\033[90m"
    B_GREEN  = "\033[92m"
    B_CYAN   = "\033[96m"
    B_YELLOW = "\033[93m"
    B_MAGENTA= "\033[95m"
    B_RED    = "\033[91m"
    B_BLUE   = "\033[94m"

# ─── Pretty Printing ─────────────────────────────────────────────────────────

LOGO = f"""{C.B_CYAN}{C.BOLD}
  ╔═══════════════════════════════════════════════════════════════╗
  ║                                                               ║
  ║   ▄▀▀▀▀▄  █    █ █▀▀▀█ █▀▀▀█ █▀▀▀█ █▀▀█ ▀▀█▀▀              ║
  ║   █▄▄▄▄▀  █    █ █▄▄▄█ █▄▄▄█ █   █ █▄▄▀   █                ║
  ║   ▀▄▄▄▄▀  ▀▄▄▄▀ █     █     █▄▄▄█ █  ▀▄  █                 ║
  ║                                                               ║
  ║           🤖  Interactive Support Agent  v1.0                 ║
  ║                                                               ║
  ╚═══════════════════════════════════════════════════════════════╝{C.RESET}
"""

HELP_TEXT = f"""
{C.BOLD}{C.B_CYAN}Available Commands:{C.RESET}
  {C.B_GREEN}/help{C.RESET}              Show this help message
  {C.B_GREEN}/company <name>{C.RESET}    Set the company context (e.g., /company DevPlatform)
  {C.B_GREEN}/model{C.RESET}             Show current LLM model info
  {C.B_GREEN}/clear{C.RESET}             Clear the screen
  {C.B_GREEN}/history{C.RESET}           Show conversation history
  {C.B_GREEN}/quit{C.RESET}              Exit the agent

{C.BOLD}{C.B_CYAN}Tips:{C.RESET}
  {C.DIM}• Type any support question and press Enter
  • Multi-turn conversations are supported
  • Set company context for better routing{C.RESET}
"""

def print_divider(char="─", width=65, color=C.GRAY):
    print(f"{color}{char * width}{C.RESET}")

def print_status(label, value, color=C.B_GREEN):
    print(f"  {C.GRAY}{label:<18}{C.RESET} {color}{value}{C.RESET}")

def print_response_card(result):
    """Render the agent response as a rich terminal card."""
    print()
    print_divider("═", 65, C.B_CYAN)
    print(f"  {C.BOLD}{C.B_CYAN}🤖 AGENT RESPONSE{C.RESET}")
    print_divider("─", 65, C.CYAN)

    # Status badge
    status = result.status
    if status == "replied":
        badge = f"{C.BOLD}{C.B_GREEN}● REPLIED{C.RESET}"
    elif status == "escalated":
        badge = f"{C.BOLD}{C.B_YELLOW}▲ ESCALATED{C.RESET}"
    else:
        badge = f"{C.BOLD}{C.B_RED}✕ {status.upper()}{C.RESET}"

    print_status("Status", badge)
    print_status("Product Area", result.product_area, C.B_MAGENTA)
    print_status("Request Type", result.request_type, C.WHITE)

    # Risk level with color coding
    risk_colors = {"low": C.B_GREEN, "medium": C.B_YELLOW, "high": C.B_RED, "critical": f"{C.BOLD}{C.B_RED}"}
    risk_c = risk_colors.get(result.risk_level, C.WHITE)
    print_status("Risk Level", f"{risk_c}{result.risk_level.upper()}{C.RESET}")

    # Confidence bar
    conf = result.confidence_score
    bar_len = 20
    filled = int(conf * bar_len)
    bar = f"{'█' * filled}{'░' * (bar_len - filled)}"
    conf_color = C.B_GREEN if conf >= 0.7 else (C.B_YELLOW if conf >= 0.4 else C.B_RED)
    print_status("Confidence", f"{conf_color}{bar} {conf:.0%}{C.RESET}")

    print_status("Language", result.language.upper(), C.WHITE)
    print_status("PII Detected", "⚠ YES" if result.pii_detected else "✓ No", C.B_RED if result.pii_detected else C.B_GREEN)

    # Response body
    print_divider("─", 65, C.CYAN)
    if result.response:
        # Word-wrap the response
        words = result.response.split()
        lines = []
        current = "  "
        for w in words:
            if len(current) + len(w) + 1 > 63:
                lines.append(current)
                current = "  "
            current += w + " "
        if current.strip():
            lines.append(current)
        for line in lines:
            print(f"{C.WHITE}{line}{C.RESET}")
    else:
        print(f"  {C.DIM}(No response — escalated to human agent){C.RESET}")

    # Justification
    if result.justification:
        print()
        print(f"  {C.GRAY}{C.ITALIC}Justification: {result.justification[:200]}{C.RESET}")

    # Source documents
    if result.source_documents:
        print()
        print(f"  {C.BOLD}{C.B_BLUE}📄 Sources:{C.RESET}")
        for doc in result.source_documents.split("|"):
            doc = doc.strip()
            if doc:
                print(f"    {C.GRAY}→ {C.DIM}{doc}{C.RESET}")

    # Actions
    if result.actions_taken:
        print()
        print(f"  {C.BOLD}{C.B_MAGENTA}⚡ Actions:{C.RESET}")
        for action in result.actions_taken:
            if hasattr(action, 'action'):
                print(f"    {C.GRAY}→ {action.action}{C.RESET}")
            elif isinstance(action, dict):
                print(f"    {C.GRAY}→ {action.get('action', '?')}{C.RESET}")

    print_divider("═", 65, C.B_CYAN)
    print()


def print_thinking(stage):
    """Print a stage indicator."""
    stages = {
        "sanitize":  f"  {C.GRAY}[1/5]{C.RESET} {C.DIM}Sanitizing input...{C.RESET}",
        "safety":    f"  {C.GRAY}[2/5]{C.RESET} {C.DIM}Running safety check...{C.RESET}",
        "retrieve":  f"  {C.GRAY}[3/5]{C.RESET} {C.DIM}Retrieving relevant documents...{C.RESET}",
        "generate":  f"  {C.GRAY}[4/5]{C.RESET} {C.DIM}Generating response...{C.RESET}",
        "validate":  f"  {C.GRAY}[5/5]{C.RESET} {C.DIM}Validating output...{C.RESET}",
    }
    print(stages.get(stage, f"  {C.DIM}{stage}{C.RESET}"), flush=True)


# ─── Interactive Pipeline ────────────────────────────────────────────────────

class InteractiveAgent:
    def __init__(self, retriever: HybridRetriever, repo_root: str):
        self.coordinator = PipelineCoordinator(retriever=retriever, repo_root=repo_root)
        self.company = "Unknown"
        self.conversation_history = []
        self.turn_count = 0

    async def process_query(self, query: str) -> None:
        """Process a single user query through the full pipeline with streaming."""
        self.turn_count += 1
        self.conversation_history.append({"role": "user", "content": query})

        row = {
            "Issue": json.dumps(self.conversation_history),
            "Subject": query[:80],
            "Company": self.company,
        }

        print()
        print(f"  {C.B_CYAN}{C.BOLD}⏳ Processing (Groq API + Heuristics)...{C.RESET}")
        
        start = time.time()

        generator = await self.coordinator.process_ticket(row, stream=True)
        
        # Stream the raw output to terminal as it arrives
        print(f"  {C.CYAN}STREAM:{C.RESET} {C.DIM}", end="", flush=True)
        final_result = None
        
        async for item in generator:
            if isinstance(item, str):
                # Print tokens live
                print(item, end="", flush=True)
            else:
                final_result = item
                
        print(f"{C.RESET}") # Reset formatting after stream
        elapsed = time.time() - start

        if final_result and final_result.response:
            self.conversation_history.append({"role": "assistant", "content": final_result.response})

        if final_result:
            print_response_card(final_result)
            
        print(f"  {C.GRAY}⏱  Processed in {elapsed:.3f}s{C.RESET}")
        print()

    def set_company(self, company: str):
        self.company = company
        print(f"\n  {C.B_GREEN}✓{C.RESET} Company set to {C.BOLD}{company}{C.RESET}\n")

    def show_history(self):
        print(f"\n{C.BOLD}{C.B_CYAN}Conversation History ({len(self.conversation_history)} messages):{C.RESET}")
        print_divider()
        for msg in self.conversation_history:
            role = msg["role"]
            content = msg["content"][:150]
            if role == "user":
                print(f"  {C.B_GREEN}You:{C.RESET} {content}")
            else:
                print(f"  {C.B_CYAN}Agent:{C.RESET} {content}")
        print_divider()
        print()

    def clear_history(self):
        self.conversation_history = []
        self.turn_count = 0
        print(f"\n  {C.B_GREEN}✓{C.RESET} Conversation history cleared\n")


# ─── Main REPL ───────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="Interactive Support Agent CLI")
    parser.add_argument("--company", default="Unknown", help="Set initial company context")
    args = parser.parse_args()

    # Suppress noisy logs in interactive mode
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Print logo
    os.system("clear" if os.name != "nt" else "cls")
    print(LOGO)
    print(f"  {C.DIM}Model: {C.RESET}{C.BOLD}{GROQ_MODEL}{C.RESET}")
    print(f"  {C.DIM}Type {C.B_GREEN}/help{C.RESET}{C.DIM} for commands, or just ask a question.{C.RESET}")
    print()
    print_divider("═", 65, C.GRAY)
    print()

    # Initialize retriever
    print(f"  {C.B_YELLOW}⏳ Loading knowledge base...{C.RESET}", end="", flush=True)
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(repo_root, "data")
    retriever = HybridRetriever(data_dir=data_dir)
    print(f"\r  {C.B_GREEN}✓  Knowledge base loaded.{C.RESET}          ")
    print()

    agent = InteractiveAgent(retriever=retriever, repo_root=repo_root)
    if args.company != "Unknown":
        agent.set_company(args.company)

    # REPL loop
    try:
        while True:
            try:
                prompt_str = f"{C.B_GREEN}{C.BOLD}  ❯ {C.RESET}"
                user_input = input(prompt_str).strip()
            except EOFError:
                break

            if not user_input:
                continue

            # Handle commands
            lower = user_input.lower()

            if lower in ("/quit", "/exit", "/q"):
                print(f"\n  {C.B_CYAN}👋 Goodbye!{C.RESET}\n")
                break

            elif lower == "/help":
                print(HELP_TEXT)
                continue

            elif lower == "/clear":
                os.system("clear" if os.name != "nt" else "cls")
                print(LOGO)
                continue

            elif lower == "/model":
                print(f"\n  {C.BOLD}Model:{C.RESET} {GROQ_MODEL}")
                print(f"  {C.BOLD}Company:{C.RESET} {agent.company}")
                print(f"  {C.BOLD}Turns:{C.RESET} {agent.turn_count}")
                print()
                continue

            elif lower == "/history":
                agent.show_history()
                continue

            elif lower == "/reset":
                agent.clear_history()
                continue

            elif lower.startswith("/company "):
                company = user_input[9:].strip()
                if company:
                    agent.set_company(company)
                else:
                    print(f"\n  {C.B_RED}Usage: /company <name>{C.RESET}\n")
                continue

            elif lower.startswith("/"):
                print(f"\n  {C.B_RED}Unknown command: {user_input}{C.RESET}")
                print(f"  {C.DIM}Type /help for available commands{C.RESET}\n")
                continue

            # Process as a support query
            await agent.process_query(user_input)

    except KeyboardInterrupt:
        print(f"\n\n  {C.B_CYAN}👋 Interrupted. Goodbye!{C.RESET}\n")
    finally:
        await close_session()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
