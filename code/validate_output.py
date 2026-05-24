#!/usr/bin/env python3
"""
MLE Hiring Challenge — Output Validator

Run this script to check your output.csv for format compliance before submission.
This validates STRUCTURE ONLY — it does NOT evaluate correctness.

Usage:
    python validate_output.py
"""

import csv
import sys
import os

EXPECTED_HEADERS = [
    "issue", "subject", "company", "response", "product_area",
    "status", "request_type", "justification", "confidence_score",
    "source_documents", "risk_level", "pii_detected", "language",
    "actions_taken"
]

VALID_STATUS = {"replied", "escalated"}
VALID_REQUEST_TYPE = {"product_issue", "feature_request", "bug", "invalid"}
VALID_RISK_LEVEL = {"low", "medium", "high", "critical"}
VALID_PII_DETECTED = {"true", "false"}

def validate():
    output_path = os.path.join(os.path.dirname(__file__), "..", "support_tickets", "output.csv")
    input_path = os.path.join(os.path.dirname(__file__), "..", "support_tickets", "support_tickets.csv")
    
    if not os.path.exists(output_path):
        print("❌ FAIL: output.csv not found at", output_path)
        return False
    
    if not os.path.exists(input_path):
        print("❌ FAIL: support_tickets.csv not found at", input_path)
        return False
    
    # Count input rows
    with open(input_path, "r", encoding="utf-8") as f:
        input_reader = csv.reader(f)
        next(input_reader)  # skip header
        input_count = sum(1 for _ in input_reader)
    
    # Validate output
    errors = []
    warnings = []
    
    with open(output_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        # Check headers
        actual_headers = reader.fieldnames
        if actual_headers is None:
            print("❌ FAIL: output.csv is empty or has no headers")
            return False
        
        missing_headers = set(EXPECTED_HEADERS) - set(actual_headers)
        extra_headers = set(actual_headers) - set(EXPECTED_HEADERS)
        
        if missing_headers:
            errors.append(f"Missing columns: {', '.join(sorted(missing_headers))}")
        if extra_headers:
            warnings.append(f"Extra columns (will be ignored): {', '.join(sorted(extra_headers))}")
        
        rows = list(reader)
        output_count = len(rows)
        
        if output_count != input_count:
            errors.append(f"Row count mismatch: expected {input_count}, got {output_count}")
        
        for i, row in enumerate(rows, start=1):
            # Check status
            status = row.get("status", "").strip().lower()
            if status not in VALID_STATUS:
                errors.append(f"Row {i}: invalid status '{status}' (expected: {VALID_STATUS})")
            
            # Check request_type
            request_type = row.get("request_type", "").strip().lower()
            if request_type not in VALID_REQUEST_TYPE:
                errors.append(f"Row {i}: invalid request_type '{request_type}' (expected: {VALID_REQUEST_TYPE})")
            
            # Check response is not empty
            response = row.get("response", "").strip()
            if not response:
                warnings.append(f"Row {i}: empty response")
            
            # Check confidence_score is a valid float 0-1
            conf = row.get("confidence_score", "").strip()
            if conf:
                try:
                    conf_val = float(conf)
                    if not (0.0 <= conf_val <= 1.0):
                        errors.append(f"Row {i}: confidence_score {conf_val} out of range [0.0, 1.0]")
                except ValueError:
                    errors.append(f"Row {i}: confidence_score '{conf}' is not a valid float")
            else:
                warnings.append(f"Row {i}: empty confidence_score")
            
            # Check risk_level
            risk = row.get("risk_level", "").strip().lower()
            if risk and risk not in VALID_RISK_LEVEL:
                errors.append(f"Row {i}: invalid risk_level '{risk}' (expected: {VALID_RISK_LEVEL})")
            elif not risk:
                warnings.append(f"Row {i}: empty risk_level")
            
            # Check pii_detected
            pii = row.get("pii_detected", "").strip().lower()
            if pii and pii not in VALID_PII_DETECTED:
                errors.append(f"Row {i}: invalid pii_detected '{pii}' (expected: {VALID_PII_DETECTED})")
            elif not pii:
                warnings.append(f"Row {i}: empty pii_detected")
            
            # Check language
            lang = row.get("language", "").strip().lower()
            if not lang:
                warnings.append(f"Row {i}: empty language")
            elif len(lang) > 5:
                warnings.append(f"Row {i}: language '{lang}' seems too long for ISO 639-1")
            
            # Check actions_taken is valid JSON array
            actions = row.get("actions_taken", "").strip()
            if not actions:
                warnings.append(f"Row {i}: actions_taken is empty (expected '[]' if no actions)")
            else:
                try:
                    import json
                    parsed = json.loads(actions)
                    if not isinstance(parsed, list):
                        errors.append(f"Row {i}: actions_taken must be a JSON array, got {type(parsed).__name__}")
                except json.JSONDecodeError as e:
                    errors.append(f"Row {i}: actions_taken is not valid JSON ({str(e)})")
    
    # Print results
    print("=" * 60)
    print("MLE Hiring Challenge — Output Validation Report")
    print("=" * 60)
    print(f"\nInput tickets:  {input_count}")
    print(f"Output rows:    {output_count}")
    print(f"Columns found:  {len(actual_headers)}/{len(EXPECTED_HEADERS)}")
    
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for e in errors[:20]:  # cap at 20
            print(f"   • {e}")
        if len(errors) > 20:
            print(f"   ... and {len(errors) - 20} more errors")
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for w in warnings[:10]:  # cap at 10
            print(f"   • {w}")
        if len(warnings) > 10:
            print(f"   ... and {len(warnings) - 10} more warnings")
    
    if not errors:
        print("\n✅ PASS: Output format is valid.")
        print("   Note: This validates structure only, NOT correctness.")
        print("   Your submission will also be evaluated on a hidden test set.")
    else:
        print(f"\n❌ FAIL: {len(errors)} errors found. Fix them before submitting.")
    
    print("=" * 60)
    return len(errors) == 0


if __name__ == "__main__":
    success = validate()
    sys.exit(0 if success else 1)
